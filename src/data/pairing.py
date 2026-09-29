"""src/data/pairing.py

Generates the 300 virtual subjects and creates the canonical subject-disjoint
train/test split manifest (180 train / 120 test) stratified by fingerprint DB.
Output: data/processed/split_manifest.json
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

import yaml


def generate_pairing_and_split(
    config_path: str | Path = "configs/paths.yaml",
) -> tuple[dict[str, Any], str]:
    """Generates the virtual subjects, train/test split, and returns (manifest, sha256_hash)."""
    config_path = Path(config_path)
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    project_root = config_path.resolve().parent.parent if config_path.is_absolute() else Path.cwd()
    face_root = project_root / cfg["dataset"]["face_dataset_root"]
    processed_root = project_root / cfg["processed"]["root"]
    manifest_path = project_root / cfg["processed"]["split_manifest"]
    seed = cfg.get("seed", 42)

    # 1. Select 300 Face Identities (folders with >= 20 images)
    image_exts = {".jpg", ".jpeg", ".png", ".bmp"}
    eligible_face_folders: list[str] = []

    for d in sorted(face_root.iterdir()):
        if d.is_dir():
            img_count = sum(1 for p in d.iterdir() if p.suffix.lower() in image_exts)
            if img_count >= 20:
                eligible_face_folders.append(d.name)

    if len(eligible_face_folders) < 300:
        raise ValueError(
            f"Insufficient face folders with >= 20 images. Found {len(eligible_face_folders)}, needed 300."
        )

    eligible_face_folders.sort()
    face_rng = random.Random(seed)
    shuffled_face_ids = list(eligible_face_folders)
    face_rng.shuffle(shuffled_face_ids)
    selected_face_ids = shuffled_face_ids[:300]

    # 2. Select Finger Keys from DB1_A, DB2_A, DB3_A (100 each -> 300 total)
    # Stratified: 60 train, 40 test per DB
    dbs = ["DB1_A", "DB2_A", "DB3_A"]
    train_finger_keys: list[tuple[str, int]] = []
    test_finger_keys: list[tuple[str, int]] = []

    # Use deterministic seeded shuffle per DB
    for db_idx, db_name in enumerate(dbs):
        db_rng = random.Random(seed + db_idx + 1)
        fingers = list(range(1, 101))
        db_rng.shuffle(fingers)
        for f in fingers[:60]:
            train_finger_keys.append((db_name, f))
        for f in fingers[60:]:
            test_finger_keys.append((db_name, f))

    # Shuffle train and test finger keys deterministically so DBs are interleaved
    interleave_rng = random.Random(seed + 100)
    interleave_rng.shuffle(train_finger_keys)
    interleave_rng.shuffle(test_finger_keys)

    # Split face identities: first 180 train, remaining 120 test
    train_face_ids = selected_face_ids[:180]
    test_face_ids = selected_face_ids[180:]

    def build_subject_records(
        subject_id_start: int,
        face_ids: list[str],
        finger_keys: list[tuple[str, int]],
        split_name: str,
    ) -> list[dict[str, Any]]:
        records = []
        for i, (face_id, (db_name, finger_id)) in enumerate(zip(face_ids, finger_keys, strict=True)):
            subj_num = subject_id_start + i
            subject_id = f"VS_{subj_num:04d}"

            folder_path = face_root / face_id
            all_face_files = sorted(
                p.name for p in folder_path.iterdir() if p.suffix.lower() in image_exts
            )

            # Sample 5 enroll and 3 probe face images across whole folder
            sample_rng = random.Random(f"{seed}_{face_id}_{subject_id}")
            sampled_face_images = sample_rng.sample(all_face_files, 8)
            face_enroll = sorted(sampled_face_images[:5])
            face_probe = sorted(sampled_face_images[5:])

            finger_enroll = [f"{finger_id}_{imp}.tif" for imp in range(1, 6)]
            finger_probe = [f"{finger_id}_{imp}.tif" for imp in range(6, 9)]

            records.append(
                {
                    "subject_id": subject_id,
                    "split": split_name,
                    "face_id": face_id,
                    "face_enroll_files": face_enroll,
                    "face_probe_files": face_probe,
                    "fingerprint_db": db_name,
                    "fingerprint_id": finger_id,
                    "fingerprint_enroll_files": finger_enroll,
                    "fingerprint_probe_files": finger_probe,
                }
            )
        return records

    train_records = build_subject_records(1, train_face_ids, train_finger_keys, "train")
    test_records = build_subject_records(181, test_face_ids, test_finger_keys, "test")

    manifest = {
        "metadata": {
            "dataset_version": "1.0.0",
            "description": "ZK-CaMBio Virtual Subjects Split Manifest",
            "face_source": "UMDFaces (dataset/facial_dataset/)",
            "fingerprint_source": "FVC2004 (DB1_A, DB2_A, DB3_A)",
            "num_train": len(train_records),
            "num_test": len(test_records),
            "num_total": len(train_records) + len(test_records),
            "seed": seed,
            "stratification": {
                "train_per_db": 60,
                "test_per_db": 40,
            },
        },
        "train": train_records,
        "test": test_records,
    }

    # Format canonically: sorted keys, 2 spaces indentation
    canonical_json = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    canonical_bytes = canonical_json.encode("utf-8")
    sha256_hash = hashlib.sha256(canonical_bytes).hexdigest()

    # Save to data/processed/split_manifest.json
    processed_root.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "wb") as f:
        f.write(canonical_bytes)

    return manifest, sha256_hash


if __name__ == "__main__":
    manifest, sha = generate_pairing_and_split()
    print("Successfully generated split manifest.")
    print(f"Total subjects: {manifest['metadata']['num_total']}")
    print(f"Train subjects: {manifest['metadata']['num_train']}")
    print(f"Test subjects:  {manifest['metadata']['num_test']}")
    print(f"Manifest SHA-256: {sha}")
