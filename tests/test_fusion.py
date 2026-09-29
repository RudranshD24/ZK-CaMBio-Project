"""tests/test_fusion.py

Unit and integration tests for Phase 3: Multimodal biometric fusion,
mathematical properties, cache integrity, and baseline results.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from src.fusion.fuse import (
    compute_cmc,
    compute_d_prime,
    compute_eer,
    compute_fnmr_at_fmr,
    fuse_embeddings_feature_level,
)


def test_fusion_feature_level_math():
    rng = np.random.RandomState(42)

    # Random unit vectors
    face_1 = rng.randn(512).astype(np.float32)
    face_1 = face_1 / np.linalg.norm(face_1)

    face_2 = rng.randn(512).astype(np.float32)
    face_2 = face_2 / np.linalg.norm(face_2)

    finger_1 = rng.randn(256).astype(np.float32)
    finger_1 = finger_1 / np.linalg.norm(finger_1)

    finger_2 = rng.randn(256).astype(np.float32)
    finger_2 = finger_2 / np.linalg.norm(finger_2)

    w = 0.60
    fused_1 = fuse_embeddings_feature_level(face_1, finger_1, w=w)
    fused_2 = fuse_embeddings_feature_level(face_2, finger_2, w=w)

    # 1. Output dimension must be 768
    assert fused_1.shape == (768,)
    assert fused_2.shape == (768,)

    # 2. Preserves unit norm
    norm_1 = np.linalg.norm(fused_1)
    norm_2 = np.linalg.norm(fused_2)
    assert np.isclose(norm_1, 1.0, atol=1e-5), f"Expected unit norm, got {norm_1}"
    assert np.isclose(norm_2, 1.0, atol=1e-5), f"Expected unit norm, got {norm_2}"

    # 3. Cosine equality property: cos(fused_1, fused_2) == w*cos_face + (1-w)*cos_finger
    cos_face = float(np.dot(face_1, face_2))
    cos_finger = float(np.dot(finger_1, finger_2))
    expected_fused_cos = w * cos_face + (1.0 - w) * cos_finger
    actual_fused_cos = float(np.dot(fused_1, fused_2))

    assert np.isclose(actual_fused_cos, expected_fused_cos, atol=1e-5), (
        f"Cosine equality violated: actual={actual_fused_cos}, expected={expected_fused_cos}"
    )


def test_fusion_weight_bounds():
    dummy_face = np.ones(512, dtype=np.float32) / np.sqrt(512)
    dummy_finger = np.ones(256, dtype=np.float32) / np.sqrt(256)

    # Valid weights
    f0 = fuse_embeddings_feature_level(dummy_face, dummy_finger, w=0.0)
    assert np.isclose(np.linalg.norm(f0), 1.0, atol=1e-5)
    f1 = fuse_embeddings_feature_level(dummy_face, dummy_finger, w=1.0)
    assert np.isclose(np.linalg.norm(f1), 1.0, atol=1e-5)

    # Invalid weights
    with pytest.raises(ValueError):
        fuse_embeddings_feature_level(dummy_face, dummy_finger, w=-0.1)
    with pytest.raises(ValueError):
        fuse_embeddings_feature_level(dummy_face, dummy_finger, w=1.1)


def test_biometric_metrics_utilities():
    gen = np.array([0.8, 0.85, 0.9, 0.75, 0.88], dtype=np.float32)
    imp = np.array([0.1, 0.15, 0.2, 0.05, 0.12], dtype=np.float32)

    # D-prime must be strictly positive and high for well-separated distributions
    dp = compute_d_prime(gen, imp)
    assert dp > 5.0, f"Expected high d-prime for separable distributions, got {dp}"

    # EER must be 0 for perfectly separable scores
    eer, thresh, _, _ = compute_eer(gen, imp)
    assert eer == 0.0, f"Expected EER 0 for separated scores, got {eer}"

    # FNMR at FMR=1% must be 0
    fnmr, _ = compute_fnmr_at_fmr(gen, imp, target_fmr=0.01)
    assert fnmr == 0.0

    # CMC test
    tmpls = np.eye(5, dtype=np.float32)
    prbs = np.eye(5, dtype=np.float32)[:, None, :]  # (5, 1, 5) perfect match
    cmc = compute_cmc(tmpls, prbs, max_rank=5)
    assert cmc[0] == 1.0, f"Expected perfect Rank-1 accuracy, got {cmc[0]}"



def test_fused_embeddings_cache_structure():
    cache_path = Path("data/processed/fused_embeddings.npz")
    if not cache_path.is_file():
        pytest.skip("fused_embeddings.npz not generated yet")

    data = np.load(cache_path)
    subject_ids = data["subject_ids"]
    splits = data["splits"]
    tmpl = data["enroll_templates"]
    prb = data["probe_embeddings"]

    assert len(subject_ids) == 300
    assert np.sum(splits == "train") == 180
    assert np.sum(splits == "test") == 120

    assert tmpl.shape == (300, 768), f"Expected (300, 768), got {tmpl.shape}"
    assert prb.shape == (300, 3, 768), f"Expected (300, 3, 768), got {prb.shape}"

    # Templates and probes must be unit-norm
    tmpl_norms = np.linalg.norm(tmpl, axis=-1)
    prb_norms = np.linalg.norm(prb, axis=-1)
    assert np.allclose(tmpl_norms, 1.0, atol=1e-4)
    assert np.allclose(prb_norms, 1.0, atol=1e-4)


def test_fusion_baseline_results():
    results_path = Path("results/fused_unprotected.json")
    if not results_path.is_file():
        pytest.skip("fused_unprotected.json not generated yet")

    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "systems" in data
    systems = data["systems"]
    for key in ["S1_face", "S2_finger", "S3_fused", "S3b_score"]:
        assert key in systems
        p = systems[key]["pooled"]
        assert p["num_test_subjects"] == 120
        assert p["num_genuine_scores"] == 360
        assert p["num_impostor_scores"] == 14040
        assert 0.0 <= p["eer_percent"] <= 100.0
        assert len(p["eer_ci_95_percent"]) == 2
