"""src/finger/train_resnet.py

Fine-tunes ResNet18 with CosFace margin loss on the 150 fit fingers (1,200 images).
Validates on the 30 validation fingers with early stopping.
Strictly isolated: test subjects are NEVER loaded or used.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
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


class FingerprintFitDataset(Dataset):
    """Dataset of the 150 fit fingers (8 impressions each = 1,200 samples)."""

    def __init__(self, fit_records: list[dict], loader: FingerprintLoader, is_train: bool = True) -> None:
        self.loader = loader
        self.samples: list[tuple[str, str, int]] = []  # (db, filename, class_label)

        for class_idx, rec in enumerate(fit_records):
            db = rec["fingerprint_db"]
            # All 8 impressions
            all_files = rec["fingerprint_enroll_files"] + rec["fingerprint_probe_files"]
            for fn in all_files:
                self.samples.append((db, fn, class_idx))

        if is_train:
            self.transform = transforms.Compose(
                [
                    transforms.RandomRotation(degrees=(-15, 15)),
                    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.95, 1.05)),
                    transforms.ColorJitter(brightness=0.15, contrast=0.15),
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
        preproc = preprocess_fingerprint(raw_img, target_size=(128, 128))
        img_pil = Image.fromarray(preproc, mode="L")
        tensor = self.transform(img_pil)
        return tensor, label


def evaluate_val_separation(
    model: FingerResNet18,
    val_records: list[dict],
    loader: FingerprintLoader,
    device: torch.device,
) -> float:
    """Evaluates validation separation (mean genuine - mean impostor cosine similarity)

    across the 30 validation fingers.
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
                p = preprocess_fingerprint(loader.load_by_filename(db, fn), target_size=(128, 128))
                enr_tensors.append(val_transform(Image.fromarray(p, mode="L")))
            batch_enr = torch.stack(enr_tensors).to(device)
            embs_enr = model(batch_enr).cpu().numpy()
            tmpl = np.mean(embs_enr, axis=0)
            tmpl = tmpl / np.linalg.norm(tmpl)
            templates.append(tmpl)

            # Probe 6-8
            prb_tensors = []
            for fn in rec["fingerprint_probe_files"]:
                p = preprocess_fingerprint(loader.load_by_filename(db, fn), target_size=(128, 128))
                prb_tensors.append(val_transform(Image.fromarray(p, mode="L")))
            batch_prb = torch.stack(prb_tensors).to(device)
            embs_prb = model(batch_prb).cpu().numpy()
            probes_list.append(embs_prb)

    # Compute genuine and impostor scores
    gen_scores = []
    imp_scores = []
    num_val = len(val_records)

    for i in range(num_val):
        for k in range(probes_list[i].shape[0]):
            gen_scores.append(float(np.dot(templates[i], probes_list[i][k])))
        for j in range(num_val):
            if i != j:
                for k in range(probes_list[j].shape[0]):
                    imp_scores.append(float(np.dot(templates[i], probes_list[j][k])))

    separation = float(np.mean(gen_scores) - np.mean(imp_scores))
    return separation


def train_finger_resnet18(
    split_path: str | Path = "data/processed/finger_train_val_split.json",
    checkpoint_path: str | Path = "data/processed/finger_resnet18_best.pth",
    epochs: int = 10,
    batch_size: int = 32,
    lr: float = 1e-3,
) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training FingerResNet18 on device: {device}")

    with open(split_path, encoding="utf-8") as f:
        split_data = json.load(f)

    fit_records = split_data["fit"]
    val_records = split_data["val"]

    loader = FingerprintLoader()
    train_dataset = FingerprintFitDataset(fit_records, loader, is_train=True)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)

    model = FingerResNet18(embedding_dim=256, pretrained=True).to(device)
    cosface = CosFaceMarginProduct(in_features=256, out_features=len(fit_records), s=30.0, m=0.35).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(cosface.parameters()),
        lr=lr,
        weight_decay=1e-4,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_sep = -1.0
    best_epoch = 0
    patience = 4
    no_improve = 0

    print(f"Starting training: {len(fit_records)} classes, {len(train_dataset)} samples, {epochs} epochs...")

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

        # Validation separation
        val_sep = evaluate_val_separation(model, val_records, loader, device)
        print(
            f"Epoch {epoch:2d}/{epochs:2d} [{epoch_time:.1f}s] - "
            f"Loss: {train_loss:.4f}, Acc: {train_acc:.1f}% | "
            f"Val Sep: {val_sep:.4f}"
        )

        if val_sep > best_val_sep:
            best_val_sep = val_sep
            best_epoch = epoch
            no_improve = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "val_separation": val_sep,
                    "embedding_dim": 256,
                },
                checkpoint_path,
            )
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"Early stopping at epoch {epoch} (no improvement for {patience} epochs).")
                break

    print(f"Best model saved from epoch {best_epoch} with validation separation: {best_val_sep:.4f}")
    return {
        "best_epoch": best_epoch,
        "best_val_separation": best_val_sep,
        "checkpoint_path": str(checkpoint_path),
        "device": str(device),
    }


if __name__ == "__main__":
    train_finger_resnet18(epochs=10)
