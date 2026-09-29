"""src/finger/split.py

Partitions the 180 TRAIN virtual subjects into:
- 150 fit fingers (50 per DB: DB1_A, DB2_A, DB3_A)
- 30 validation fingers (10 per DB: DB1_A, DB2_A, DB3_A)
Output: data/processed/finger_train_val_split.json

Strictly isolated from test subjects: test subjects are NEVER touched.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

import yaml


def create_finger_train_val_split(
    manifest_path: str | Path = "data/processed/split_manifest.json",
    config_path: str | Path = "configs/paths.yaml",
    output_path: str | Path = "data/processed/finger_train_val_split.json",
) -> tuple[dict[str, Any], str]:
    manifest_path = Path(manifest_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    seed = cfg.get("seed", 42)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    train_subjects = manifest["train"]
    assert len(train_subjects) == 180, f"Expected 180 train subjects, got {len(train_subjects)}"

    # Group by fingerprint DB
    by_db: dict[str, list[dict[str, Any]]] = {"DB1_A": [], "DB2_A": [], "DB3_A": []}
    for subj in train_subjects:
        db = subj["fingerprint_db"]
        if db in by_db:
            by_db[db].append(subj)
        else:
            raise ValueError(f"Unexpected DB: {db}")

    fit_records = []
    val_records = []

    for db_name, subjects in sorted(by_db.items()):
        assert len(subjects) == 60, f"Expected 60 train subjects for {db_name}, got {len(subjects)}"
        # Sort for determinism
        sorted_subjs = sorted(subjects, key=lambda s: s["subject_id"])

        rng = random.Random(f"{seed}_finger_split_{db_name}")
        shuffled = list(sorted_subjs)
        rng.shuffle(shuffled)

        db_fit = shuffled[:50]
        db_val = shuffled[50:]

        fit_records.extend(db_fit)
        val_records.extend(db_val)

    # Sort output records by subject_id
    fit_records.sort(key=lambda s: s["subject_id"])
    val_records.sort(key=lambda s: s["subject_id"])

    split_data = {
        "metadata": {
            "description": "Fingerprint Train (Fit) / Validation Split (Strictly from 180 TRAIN subjects)",
            "seed": seed,
            "num_fit": len(fit_records),
            "num_val": len(val_records),
            "num_total_train": len(fit_records) + len(val_records),
            "stratification": {
                "fit_per_db": 50,
                "val_per_db": 10,
            },
        },
        "fit": fit_records,
        "val": val_records,
    }

    canonical_json = json.dumps(split_data, indent=2, sort_keys=True) + "\n"
    canonical_bytes = canonical_json.encode("utf-8")
    sha256_hash = hashlib.sha256(canonical_bytes).hexdigest()

    with open(output_path, "wb") as f:
        f.write(canonical_bytes)

    print(f"Created finger train/val split: {len(fit_records)} fit, {len(val_records)} val")
    print(f"Saved to: {output_path.resolve()} (SHA-256: {sha256_hash})")
    return split_data, sha256_hash


if __name__ == "__main__":
    create_finger_train_val_split()
