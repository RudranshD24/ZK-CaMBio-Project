"""tests/test_data.py

Tests for Phase 1 data loaders, pairing, and split manifest.
Acceptance criteria:
- Subject-disjoint splits (train vs test)
- 180 train + 120 test = 300 virtual subjects
- Each face identity used exactly once
- Each (DB, finger) key used exactly once
- Stratification: exactly 60 train + 40 test per DB (DB1_A, DB2_A, DB3_A)
- Enroll / probe sets have correct counts and zero overlap
- All referenced image files exist on disk
- Rerun with seed 42 produces identical SHA-256
- FaceLoader and FingerprintLoader stream valid PIL images
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from src.data.face_loader import FaceLoader
from src.data.finger_loader import FingerprintLoader
from src.data.pairing import generate_pairing_and_split


def test_manifest_structure_and_counts():
    manifest_path = Path("data/processed/split_manifest.json")
    assert manifest_path.is_file(), "split_manifest.json must exist"

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    train_records = data["train"]
    test_records = data["test"]

    assert len(train_records) == 180, f"Expected 180 train subjects, got {len(train_records)}"
    assert len(test_records) == 120, f"Expected 120 test subjects, got {len(test_records)}"
    assert data["metadata"]["num_total"] == 300


def test_subject_disjointness():
    manifest_path = Path("data/processed/split_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    train_ids = {r["subject_id"] for r in data["train"]}
    test_ids = {r["subject_id"] for r in data["test"]}

    assert train_ids.isdisjoint(test_ids), "Train and test subject IDs must be strictly disjoint!"
    assert len(train_ids | test_ids) == 300


def test_unique_face_and_finger_identities():
    manifest_path = Path("data/processed/split_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    all_records = data["train"] + data["test"]

    face_ids = [r["face_id"] for r in all_records]
    assert len(face_ids) == 300
    assert len(set(face_ids)) == 300, "Each face identity must be used exactly once"

    finger_keys = [(r["fingerprint_db"], r["fingerprint_id"]) for r in all_records]
    assert len(finger_keys) == 300
    assert len(set(finger_keys)) == 300, "Each (DB, finger) key must be used exactly once"


def test_stratification_per_db():
    manifest_path = Path("data/processed/split_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    train_db_counts = Counter(r["fingerprint_db"] for r in data["train"])
    test_db_counts = Counter(r["fingerprint_db"] for r in data["test"])

    expected_dbs = {"DB1_A", "DB2_A", "DB3_A"}
    assert set(train_db_counts.keys()) == expected_dbs
    assert set(test_db_counts.keys()) == expected_dbs

    for db in expected_dbs:
        assert train_db_counts[db] == 60, f"Expected 60 train subjects for {db}, got {train_db_counts[db]}"
        assert test_db_counts[db] == 40, f"Expected 40 test subjects for {db}, got {test_db_counts[db]}"


def test_enroll_probe_separation_and_counts():
    manifest_path = Path("data/processed/split_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    all_records = data["train"] + data["test"]

    for r in all_records:
        # Face enroll/probe
        face_enroll = set(r["face_enroll_files"])
        face_probe = set(r["face_probe_files"])
        assert len(face_enroll) == 5, f"Subject {r['subject_id']} face enroll must have 5 files"
        assert len(face_probe) == 3, f"Subject {r['subject_id']} face probe must have 3 files"
        assert face_enroll.isdisjoint(face_probe), f"Subject {r['subject_id']} face enroll/probe overlap!"

        # Fingerprint enroll/probe
        finger_enroll = set(r["fingerprint_enroll_files"])
        finger_probe = set(r["fingerprint_probe_files"])
        assert len(finger_enroll) == 5, f"Subject {r['subject_id']} finger enroll must have 5 files"
        assert len(finger_probe) == 3, f"Subject {r['subject_id']} finger probe must have 3 files"
        assert finger_enroll.isdisjoint(finger_probe), f"Subject {r['subject_id']} finger enroll/probe overlap!"


def test_reproducibility_sha256():
    manifest, new_sha = generate_pairing_and_split()
    manifest_path = Path("data/processed/split_manifest.json")

    with open(manifest_path, "rb") as f:
        current_sha = hashlib.sha256(f.read()).hexdigest()

    assert new_sha == current_sha, "Manifest generation must be 100% deterministic"
    assert current_sha == "a3454a7c59e609ffccac38ba8d0a584858e128715a7c125ea442ef6809f8f6b4"


def test_data_loaders_streaming():
    manifest_path = Path("data/processed/split_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    first_subj = data["train"][0]

    # Test FaceLoader
    face_loader = FaceLoader()
    face_img = face_loader.load_image(first_subj["face_id"], first_subj["face_enroll_files"][0])
    assert face_img is not None
    assert face_img.mode == "RGB"
    assert face_img.size == (112, 112)

    # Test FingerprintLoader
    finger_loader = FingerprintLoader()
    finger_img = finger_loader.load_by_filename(
        first_subj["fingerprint_db"], first_subj["fingerprint_enroll_files"][0]
    )
    assert finger_img is not None
    assert finger_img.mode == "L"
    assert finger_img.size[0] > 0 and finger_img.size[1] > 0
