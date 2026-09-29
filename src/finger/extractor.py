"""src/finger/extractor.py

Extracts and caches fingerprint embeddings for all 300 virtual subjects
for both Baseline A (Gabor 256-d) and Baseline B (fine-tuned ResNet18 256-d).
Outputs:
- data/processed/finger_embeddings_gabor.npz
- data/processed/finger_embeddings_resnet.npz
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from tqdm import tqdm

try:
    from src.data.finger_loader import FingerprintLoader
    from src.finger.gabor import GaborFeatureExtractor
    from src.finger.models import FingerResNet18
    from src.finger.preprocess import preprocess_fingerprint
except ImportError:
    from data.finger_loader import FingerprintLoader
    from finger.gabor import GaborFeatureExtractor
    from finger.models import FingerResNet18
    from finger.preprocess import preprocess_fingerprint


def extract_and_cache_gabor(
    manifest_path: str | Path = "data/processed/split_manifest.json",
    output_path: str | Path = "data/processed/finger_embeddings_gabor.npz",
    loader: FingerprintLoader | None = None,
) -> dict[str, Any]:
    if loader is None:
        loader = FingerprintLoader()
    extractor = GaborFeatureExtractor()

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    all_subjects = manifest["train"] + manifest["test"]
    subject_ids = []
    splits = []
    finger_dbs = []
    finger_ids = []
    enroll_list = []
    probe_list = []
    template_list = []

    print(f"Extracting Gabor features for {len(all_subjects)} subjects...")

    for subj in tqdm(all_subjects, desc="Gabor extraction"):
        s_id = subj["subject_id"]
        split = subj["split"]
        db = subj["fingerprint_db"]
        f_id = subj["fingerprint_id"]

        # Enroll 1-5
        enr_feats = []
        for fn in subj["fingerprint_enroll_files"]:
            raw = loader.load_by_filename(db, fn)
            feat = extractor.extract(raw)
            enr_feats.append(feat)

        enr_arr = np.array(enr_feats, dtype=np.float32)  # (5, 256)
        tmpl = np.mean(enr_arr, axis=0)
        norm = np.linalg.norm(tmpl)
        tmpl = tmpl / norm if norm > 0 else tmpl

        # Probe 6-8
        prb_feats = []
        for fn in subj["fingerprint_probe_files"]:
            raw = loader.load_by_filename(db, fn)
            feat = extractor.extract(raw)
            prb_feats.append(feat)

        prb_arr = np.array(prb_feats, dtype=np.float32)  # (3, 256)

        subject_ids.append(s_id)
        splits.append(split)
        finger_dbs.append(db)
        finger_ids.append(f_id)
        enroll_list.append(enr_arr)
        probe_list.append(prb_arr)
        template_list.append(tmpl)

    np.savez_compressed(
        output_path,
        subject_ids=np.array(subject_ids),
        splits=np.array(splits),
        fingerprint_dbs=np.array(finger_dbs),
        fingerprint_ids=np.array(finger_ids),
        enroll_embeddings=np.array(enroll_list, dtype=np.float32),
        probe_embeddings=np.array(probe_list, dtype=np.float32),
        enroll_templates=np.array(template_list, dtype=np.float32),
    )
    print(f"Saved Gabor fingerprint embeddings to: {output_path}")
    return {"num_subjects": len(all_subjects), "output_path": str(output_path)}


def extract_and_cache_resnet(
    manifest_path: str | Path = "data/processed/split_manifest.json",
    checkpoint_path: str | Path = "data/processed/finger_resnet18_best.pth",
    output_path: str | Path = "data/processed/finger_embeddings_resnet.npz",
    loader: FingerprintLoader | None = None,
    device: str | None = None,
) -> dict[str, Any]:
    if loader is None:
        loader = FingerprintLoader()
    dev = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))

    model = FingerResNet18(embedding_dim=256, pretrained=False)
    ckpt = torch.load(checkpoint_path, map_location=dev)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(dev).eval()

    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5]),
        ]
    )

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    all_subjects = manifest["train"] + manifest["test"]
    subject_ids = []
    splits = []
    finger_dbs = []
    finger_ids = []
    enroll_list = []
    probe_list = []
    template_list = []

    print(f"Extracting ResNet18 embeddings for {len(all_subjects)} subjects on {dev}...")

    with torch.no_grad():
        for subj in tqdm(all_subjects, desc="ResNet18 extraction"):
            s_id = subj["subject_id"]
            split = subj["split"]
            db = subj["fingerprint_db"]
            f_id = subj["fingerprint_id"]

            # Enroll 1-5
            enr_tensors = []
            for fn in subj["fingerprint_enroll_files"]:
                raw = loader.load_by_filename(db, fn)
                proc = preprocess_fingerprint(raw, target_size=(128, 128))
                enr_tensors.append(transform(Image.fromarray(proc, mode="L")))
            b_enr = torch.stack(enr_tensors).to(dev)
            enr_embs = model(b_enr).cpu().numpy()  # (5, 256)

            tmpl = np.mean(enr_embs, axis=0)
            norm = np.linalg.norm(tmpl)
            tmpl = tmpl / norm if norm > 0 else tmpl

            # Probe 6-8
            prb_tensors = []
            for fn in subj["fingerprint_probe_files"]:
                raw = loader.load_by_filename(db, fn)
                proc = preprocess_fingerprint(raw, target_size=(128, 128))
                prb_tensors.append(transform(Image.fromarray(proc, mode="L")))
            b_prb = torch.stack(prb_tensors).to(dev)
            prb_embs = model(b_prb).cpu().numpy()  # (3, 256)

            subject_ids.append(s_id)
            splits.append(split)
            finger_dbs.append(db)
            finger_ids.append(f_id)
            enroll_list.append(enr_embs)
            probe_list.append(prb_embs)
            template_list.append(tmpl)

    np.savez_compressed(
        output_path,
        subject_ids=np.array(subject_ids),
        splits=np.array(splits),
        fingerprint_dbs=np.array(finger_dbs),
        fingerprint_ids=np.array(finger_ids),
        enroll_embeddings=np.array(enroll_list, dtype=np.float32),
        probe_embeddings=np.array(probe_list, dtype=np.float32),
        enroll_templates=np.array(template_list, dtype=np.float32),
    )
    print(f"Saved ResNet18 fingerprint embeddings to: {output_path}")
    return {"num_subjects": len(all_subjects), "output_path": str(output_path)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract and cache fingerprint embeddings")
    parser.add_argument("--gabor", action="store_true", help="Extract Gabor features")
    parser.add_argument("--resnet", action="store_true", help="Extract ResNet18 features")
    args = parser.parse_args()

    if not args.gabor and not args.resnet:
        # Default to both if none specified
        args.gabor = True
        args.resnet = True

    if args.gabor:
        extract_and_cache_gabor()
    if args.resnet:
        extract_and_cache_resnet()

