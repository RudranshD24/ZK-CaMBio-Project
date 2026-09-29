"""src/finger/train_resnet.py

Fine-tunes FingerResNet18 with CosFace margin loss on the 150 fit fingers (1,200 impressions).
Optionally incorporates 140 extra train-only fingers (1,120 impressions) from DB4_A and DB*_B.
Evaluates on the 30 validation fingers with early stopping.
Strictly isolated: test subjects (120) are NEVER loaded or touched.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import roc_curve
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

try:
    from src.data.finger_loader import FingerprintLoader
    from src.finger.models import CosFaceMarginProduct, FingerResNet18
    from src.finger.preprocess import preprocess_fingerprint
except ImportError:
    from data.finger_loader import FingerprintLoader
    from finger.models import CosFaceMarginProduct, FingerResNet18
    from finger.preprocess import preprocess_fingerprint


def compute_val_eer(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> float:
    """Computes Equal Error Rate on validation scores."""
    labels = np.concatenate([np.ones_like(genuine_scores), np.zeros_like(impostor_scores)])
    scores = np.concatenate([genuine_scores, impostor_scores])
    fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
    fnr = 1.0 - tpr
    diff = fnr - fpr
    idx = int(np.argmin(np.abs(diff)))
    return float((fpr[idx] + fnr[idx]) / 2.0)


class FingerprintFitDataset(Dataset):
    """Dataset of fit fingers (8 impressions each).

    Can optionally include extra train-only fingers from DB4_A and DB*_B.
    """

    def __init__(
        self,
        fit_records: list[dict],
        loader: FingerprintLoader,
        preproc_variant: str = "v2",
        include_extra_data: bool = False,
        is_train: bool = True,
    ) -> None:
        self.loader = loader
        self.preproc_variant = preproc_variant
        self.samples: list[tuple[str, str, int]] = []  # (db, filename, class_label)

        # 1. 150 fit fingers
        for class_idx, rec in enumerate(fit_records):
            db = rec["fingerprint_db"]
            all_files = rec["fingerprint_enroll_files"] + rec["fingerprint_probe_files"]
            for fn in all_files:
                self.samples.append((db, fn, class_idx))

        # 2. Optional extra train-only fingers (140 fingers: DB4_A 100, DB1_B..DB4_B 10 each)
        if include_extra_data:
            next_class_idx = len(fit_records)
            extra_configs = [
                ("DB4_A", 100, 1),
                ("DB1_B", 10, 101),
                ("DB2_B", 10, 101),
                ("DB3_B", 10, 101),
                ("DB4_B", 10, 101),
            ]
            for db_name, count, offset in extra_configs:
                for f_id in range(offset, offset + count):
                    for imp in range(1, 9):
                        fn = f"{f_id}_{imp}.tif"
                        self.samples.append((db_name, fn, next_class_idx))
                    next_class_idx += 1

        if is_train:
            self.transform = transforms.Compose(
                [
                    transforms.RandomRotation(degrees=(-12, 12)),
                    transforms.RandomAffine(degrees=0, translate=(0.04, 0.04), scale=(0.96, 1.04)),
                    transforms.ColorJitter(brightness=0.10, contrast=0.10),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.5], std=[0.5]),
                ]
            )
        else:
            self.transform = transforms.Compose(
                [
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.5], std=[0.5]),
                ]
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        db, fn, label = self.samples[idx]
        raw_img = self.loader.load_by_filename(db, fn)
        preproc = preprocess_fingerprint(raw_img, db_hint=db, variant=self.preproc_variant)
        img_pil = Image.fromarray(preproc, mode="L")
        tensor = self.transform(img_pil)
        return tensor, label


def evaluate_val_metrics(
    model: FingerResNet18,
    val_records: list[dict],
    loader: FingerprintLoader,
    device: torch.device,
    preproc_variant: str = "v2",
) -> tuple[float, float]:
    """Evaluates validation separation and validation EER on the 30 validation fingers

    under same-DB protocol (10 subjects per DB).
    """
    model.eval()
    val_transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5]),
        ]
    )

    templates = []
    probes_list = []

    with torch.no_grad():
        for rec in val_records:
            db = rec["fingerprint_db"]
            # Enroll 1-5
            enr_tensors = []
            for fn in rec["fingerprint_enroll_files"]:
                p = preprocess_fingerprint(
                    loader.load_by_filename(db, fn), db_hint=db, variant=preproc_variant
                )
                enr_tensors.append(val_transform(Image.fromarray(p, mode="L")))
            batch_enr = torch.stack(enr_tensors).to(device)
            embs_enr = model(batch_enr).cpu().numpy()
            tmpl = np.mean(embs_enr, axis=0)
            norm = np.linalg.norm(tmpl)
            tmpl = tmpl / norm if norm > 0 else tmpl
            templates.append(tmpl)

            # Probe 6-8
            prb_tensors = []
            for fn in rec["fingerprint_probe_files"]:
                p = preprocess_fingerprint(
                    loader.load_by_filename(db, fn), db_hint=db, variant=preproc_variant
                )
                prb_tensors.append(val_transform(Image.fromarray(p, mode="L")))
            batch_prb = torch.stack(prb_tensors).to(device)
            embs_prb = model(batch_prb).cpu().numpy()
            probes_list.append(embs_prb)

    # Same-DB evaluation on val (10 subjects per DB, 3 DBs)
    db_indices = {"DB1_A": [], "DB2_A": [], "DB3_A": []}
    for idx, rec in enumerate(val_records):
        db_indices[rec["fingerprint_db"]].append(idx)

    gen_scores = []
    imp_scores = []
    for _db, idxs in db_indices.items():
        for i in idxs:
            for k in range(3):
                gen_scores.append(float(np.dot(templates[i], probes_list[i][k])))
            for j in idxs:
                if i != j:
                    for k in range(3):
                        imp_scores.append(float(np.dot(templates[i], probes_list[j][k])))

    gen_arr = np.array(gen_scores, dtype=np.float32)
    imp_arr = np.array(imp_scores, dtype=np.float32)

    separation = float(np.mean(gen_arr) - np.mean(imp_arr))
    val_eer = compute_val_eer(gen_arr, imp_arr)
    return separation, val_eer


def train_finger_resnet18(
    split_path: str | Path = "data/processed/finger_train_val_split.json",
    checkpoint_path: str | Path = "data/processed/finger_resnet18_best.pth",
    variant: str = "v2",
    use_extra_data: bool = False,
    epochs: int = 8,
    batch_size: int = 32,
    lr: float = 1e-3,
    patience: int = 3,
) -> dict[str, Any]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training FingerResNet18 ({variant}, extra_data={use_extra_data}) on: {device}")

    with open(split_path, encoding="utf-8") as f:
        split_data = json.load(f)

    fit_records = split_data["fit"]
    val_records = split_data["val"]

    loader = FingerprintLoader()
    train_dataset = FingerprintFitDataset(
        fit_records,
        loader,
        preproc_variant=variant,
        include_extra_data=use_extra_data,
        is_train=True,
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)

    num_classes = len(fit_records) + (140 if use_extra_data else 0)
    model = FingerResNet18(embedding_dim=256, pretrained=True).to(device)
    cosface = CosFaceMarginProduct(in_features=256, out_features=num_classes, s=30.0, m=0.35).to(
        device
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(cosface.parameters()),
        lr=lr,
        weight_decay=1e-4,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_sep = -1.0
    best_val_eer = 1.0
    best_epoch = 0
    no_improve = 0

    print(
        f"Training config: {num_classes} classes, {len(train_dataset)} samples, {epochs} epochs max (variant={variant})..."
    )

    for epoch in range(1, epochs + 1):
        model.train()
        cosface.train()
        running_loss = 0.0
        correct = 0
        total = 0
        t0 = time.time()

        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            embs = model(x)
            logits = cosface(embs, y)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * x.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += x.size(0)

        scheduler.step()
        epoch_time = time.time() - t0
        train_acc = correct / total * 100
        train_loss = running_loss / total

        # Validation separation & EER
        val_sep, val_eer = evaluate_val_metrics(
            model, val_records, loader, device, preproc_variant=variant
        )
        print(
            f"Epoch {epoch:2d}/{epochs:2d} [{epoch_time:.1f}s] - "
            f"Loss: {train_loss:.4f}, Acc: {train_acc:.1f}% | "
            f"Val Sep: {val_sep:.4f}, Val EER: {val_eer*100:.2f}%"
        )

        # Optimization metric: higher validation separation (and lower EER)
        if val_sep > best_val_sep:
            best_val_sep = val_sep
            best_val_eer = val_eer
            best_epoch = epoch
            no_improve = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "val_separation": val_sep,
                    "val_eer": val_eer,
                    "embedding_dim": 256,
                    "preproc_variant": variant,
                    "used_extra_data": use_extra_data,
                },
                checkpoint_path,
            )
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"Early stopping at epoch {epoch} (no improvement for {patience} epochs).")
                break

    print(
        f"Result for variant={variant} (extra_data={use_extra_data}): "
        f"Best Epoch={best_epoch}, Val Sep={best_val_sep:.4f}, Val EER={best_val_eer*100:.2f}%"
    )

    return {
        "variant": variant,
        "use_extra_data": use_extra_data,
        "best_epoch": best_epoch,
        "best_val_separation": float(best_val_sep),
        "best_val_eer": float(best_val_eer),
        "checkpoint_path": str(checkpoint_path),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FingerResNet18")
    parser.add_argument("--variant", choices=["v1", "v2"], default="v2", help="Preproc variant")
    parser.add_argument("--extra-data", action="store_true", help="Include DB4_A and DB*_B")
    parser.add_argument(
        "--checkpoint", default="data/processed/finger_resnet18_best.pth", help="Checkpoint path"
    )
    parser.add_argument("--epochs", type=int, default=8, help="Max epochs")
    args = parser.parse_args()

    train_finger_resnet18(
        checkpoint_path=args.checkpoint,
        variant=args.variant,
        use_extra_data=args.extra_data,
        epochs=args.epochs,
    )
