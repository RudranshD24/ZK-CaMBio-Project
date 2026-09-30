"""tests/test_security.py

Tests for Phase 6: Security and Non-Invertibility Evaluations (Protocol D-015).
Ensures:
1. Attacker training data isolation: ZERO test subjects enter attacker training sets or priors.
2. Atk-1 Sanity Check on synthetic Gaussian vectors: empirical mean cosine matches
   theoretical expectation sqrt(2/pi)*m / sqrt((2/pi)*m^2 + d*m) within 0.03 for m in {128, 512, 1024}.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


def test_attacker_training_data_isolation():
    """Asserts that no test-subject data enters attacker training or prior fitting."""
    manifest_path = Path("data/processed/split_manifest.json")
    assert manifest_path.is_file(), "split_manifest.json must exist"

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    train_subjects = {s["subject_id"] for s in manifest["train"]}
    test_subjects = {s["subject_id"] for s in manifest["test"]}

    assert len(train_subjects) == 180, f"Expected 180 train subjects, got {len(train_subjects)}"
    assert len(test_subjects) == 120, f"Expected 120 test subjects, got {len(test_subjects)}"
    overlap = train_subjects.intersection(test_subjects)
    assert len(overlap) == 0, f"Data leakage detected! Overlapping subjects: {overlap}"

    # Also check cached fused embeddings split tags
    fused_path = Path("data/processed/fused_embeddings.npz")
    assert fused_path.is_file(), "fused_embeddings.npz must exist"
    fused_data = np.load(fused_path)

    fused_train_ids = set(fused_data["subject_ids"][fused_data["splits"] == "train"])
    fused_test_ids = set(fused_data["subject_ids"][fused_data["splits"] == "test"])

    assert fused_train_ids == train_subjects, "Train subject IDs mismatch between manifest and fused data"
    assert fused_test_ids == test_subjects, "Test subject IDs mismatch between manifest and fused data"
    assert len(fused_train_ids.intersection(fused_test_ids)) == 0, "Leakage in fused_embeddings.npz"


@pytest.mark.parametrize("m,expected_theoretical", [
    (128, 0.3097),
    (512, 0.5459),
    (1024, 0.6776),
])
def test_atk1_backprojection_gaussian_sanity(m: int, expected_theoretical: float):
    """Sanity test on synthetic Gaussian unit vectors.

    Atk-1 back-projection mean cosine must match:
    sqrt(2/pi)*m / sqrt((2/pi)*m^2 + d*m)
    within 0.03 for m in {128, 512, 1024} with d=768.
    """
    d = 768
    n_samples = 2500
    rng = np.random.RandomState(42 + m)

    # Theoretical expectation
    theo = np.sqrt(2.0 / np.pi) * m / np.sqrt((2.0 / np.pi) * (m**2) + d * m)
    assert abs(theo - expected_theoretical) < 0.001, f"Theoretical formula mismatch: {theo} vs {expected_theoretical}"

    # Rademacher projection matrix R in {-1, +1}^{m x d}
    R = rng.choice([-1.0, 1.0], size=(m, d))

    # Synthetic Gaussian unit vectors
    X = rng.randn(n_samples, d)
    X = X / np.linalg.norm(X, axis=1, keepdims=True)

    # Projections and bits b = (R x >= 0)
    # Signs s = 2*b - 1
    proj = X @ R.T
    B = (proj >= 0.0).astype(np.float64)
    S = 2.0 * B - 1.0

    # Back-projection reconstruction: x_hat = S @ R / ||...||
    X_hat = S @ R
    X_hat_norm = X_hat / np.linalg.norm(X_hat, axis=1, keepdims=True)

    # Cosine similarities
    cosines = np.sum(X_hat_norm * X, axis=1)
    mean_cos = float(np.mean(cosines))

    diff = abs(mean_cos - theo)
    assert diff <= 0.03, (
        f"Atk-1 Gaussian sanity check failed for m={m}! "
        f"Empirical={mean_cos:.4f}, Theo={theo:.4f}, Diff={diff:.4f} > 0.03"
    )
