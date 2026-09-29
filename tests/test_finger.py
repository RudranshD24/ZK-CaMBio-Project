"""tests/test_finger.py

Tests for Stage 2b: Fingerprint preprocessing, Gabor baseline, ResNet18 model,
train/val split isolation, cached embeddings, and baseline evaluation results.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from src.finger.gabor import GaborFeatureExtractor
from src.finger.models import FingerResNet18
from src.finger.preprocess import preprocess_fingerprint


def test_fingerprint_preprocessing():
    # Synthetic fingerprint-like image with border
    img = np.zeros((300, 300), dtype=np.uint8)
    img[50:250, 50:250] = 120
    # Add some sinusoidal ridge patterns
    x = np.linspace(0, 10 * np.pi, 200)
    ridges = (np.sin(x)[:, None] * 50 + 120).astype(np.uint8)
    img[50:250, 50:250] = ridges

    proc = preprocess_fingerprint(img, target_size=(128, 128))
    assert isinstance(proc, np.ndarray)
    assert proc.shape == (128, 128), f"Expected (128, 128), got {proc.shape}"
    assert proc.dtype == np.uint8
    assert proc.min() >= 0 and proc.max() <= 255


def test_gabor_feature_extractor_dimensions_and_norm():
    extractor = GaborFeatureExtractor(grid_size=(8, 8))
    dummy_img = np.random.randint(0, 256, (128, 128), dtype=np.uint8)

    feat = extractor.extract(dummy_img)
    assert isinstance(feat, np.ndarray)
    assert feat.shape == (256,), f"Expected (256,), got {feat.shape}"
    assert not np.isnan(feat).any()
    norm = np.linalg.norm(feat)
    assert np.isclose(norm, 1.0, atol=1e-4), f"Gabor feature must be L2-normalized, got {norm}"


def test_resnet18_model_output_dimensions_and_norm():
    model = FingerResNet18(embedding_dim=256, pretrained=False)
    model.eval()

    dummy_input = torch.randn(4, 1, 128, 128)
    with torch.no_grad():
        embs = model(dummy_input)

    assert embs.shape == (4, 256), f"Expected (4, 256), got {embs.shape}"
    norms = torch.norm(embs, p=2, dim=1).numpy()
    assert np.allclose(norms, 1.0, atol=1e-4), "ResNet18 embeddings must be L2-normalized"


def test_train_val_split_isolation():
    split_path = Path("data/processed/finger_train_val_split.json")
    manifest_path = Path("data/processed/split_manifest.json")

    assert split_path.is_file(), "finger_train_val_split.json must exist"
    assert manifest_path.is_file(), "split_manifest.json must exist"

    with open(split_path, encoding="utf-8") as f:
        split_data = json.load(f)
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    fit_records = split_data["fit"]
    val_records = split_data["val"]
    test_records = manifest["test"]

    assert len(fit_records) == 150, f"Expected 150 fit subjects, got {len(fit_records)}"
    assert len(val_records) == 30, f"Expected 30 val subjects, got {len(val_records)}"

    # Check stratification: 50 fit and 10 val per DB
    for db in ["DB1_A", "DB2_A", "DB3_A"]:
        n_fit_db = sum(1 for r in fit_records if r["fingerprint_db"] == db)
        n_val_db = sum(1 for r in val_records if r["fingerprint_db"] == db)
        assert n_fit_db == 50, f"DB {db} must have 50 fit subjects, got {n_fit_db}"
        assert n_val_db == 10, f"DB {db} must have 10 val subjects, got {n_val_db}"

    # Verify complete isolation: disjoint subject IDs
    fit_subjs = {r["subject_id"] for r in fit_records}
    val_subjs = {r["subject_id"] for r in val_records}
    test_subjs = {r["subject_id"] for r in test_records}

    assert fit_subjs.isdisjoint(val_subjs), "Fit and Val subjects must be mutually disjoint!"
    assert fit_subjs.isdisjoint(test_subjs), "Fit and Test subjects must be mutually disjoint!"
    assert val_subjs.isdisjoint(test_subjs), "Val and Test subjects must be mutually disjoint!"


def test_fingerprint_embeddings_caches():
    for name in ["finger_embeddings_gabor.npz", "finger_embeddings_resnet.npz"]:
        cache_path = Path(f"data/processed/{name}")
        assert cache_path.is_file(), f"{cache_path} must exist"

        data = np.load(cache_path)
        subject_ids = data["subject_ids"]
        splits = data["splits"]
        enroll_embs = data["enroll_embeddings"]
        probe_embs = data["probe_embeddings"]
        templates = data["enroll_templates"]

        assert len(subject_ids) == 300
        assert enroll_embs.shape == (300, 5, 256)
        assert probe_embs.shape == (300, 3, 256)
        assert templates.shape == (300, 256)

        assert np.sum(splits == "train") == 180
        assert np.sum(splits == "test") == 120

        # Check L2-normalization of templates
        tmpl_norms = np.linalg.norm(templates, axis=1)
        assert np.allclose(tmpl_norms, 1.0, atol=1e-4)


def test_fingerprint_baseline_results():
    results_path = Path("results/finger_eer.json")
    assert results_path.is_file(), "results/finger_eer.json must exist"

    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "baseline_a_gabor" in data
    assert "baseline_b_resnet18" in data
    assert "comparison" in data

    a_pooled = data["baseline_a_gabor"]["pooled"]
    b_pooled = data["baseline_b_resnet18"]["pooled"]

    assert a_pooled["num_test_subjects"] == 120
    assert a_pooled["num_genuine_scores"] == 360
    assert a_pooled["num_impostor_scores"] == 14040

    assert b_pooled["num_test_subjects"] == 120
    assert b_pooled["num_genuine_scores"] == 360
    assert b_pooled["num_impostor_scores"] == 14040

    # Ensure EERs and CIs are valid numbers
    assert 0.0 <= a_pooled["eer"] <= 1.0
    assert 0.0 <= b_pooled["eer"] <= 1.0
    assert len(a_pooled["eer_ci_95"]) == 2
    assert len(b_pooled["eer_ci_95"]) == 2
