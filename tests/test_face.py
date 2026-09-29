"""tests/test_face.py

Tests for Stage 2a: Face encoder, embeddings cache, and face baseline metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from src.face.encoder import FaceEncoder


def test_face_encoder_output_dimensions_and_norm():
    encoder = FaceEncoder()
    dummy_img = Image.new("RGB", (112, 112), color=(128, 128, 128))

    emb = encoder.extract_embedding(dummy_img)
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (512,), f"Expected (512,), got {emb.shape}"
    norm = np.linalg.norm(emb)
    assert np.isclose(norm, 1.0, atol=1e-4), f"Embedding must be L2-normalized, got norm={norm}"

    batch_imgs = [dummy_img, dummy_img]
    batch_embs = encoder.extract_batch(batch_imgs)
    assert batch_embs.shape == (2, 512)
    norms = np.linalg.norm(batch_embs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4)


def test_face_embeddings_cache_structure():
    cache_path = Path("data/processed/face_embeddings.npz")
    assert cache_path.is_file(), "data/processed/face_embeddings.npz must exist"

    data = np.load(cache_path)
    subject_ids = data["subject_ids"]
    splits = data["splits"]
    enroll_embs = data["enroll_embeddings"]
    probe_embs = data["probe_embeddings"]
    templates = data["enroll_templates"]

    assert len(subject_ids) == 300
    assert enroll_embs.shape == (300, 5, 512)
    assert probe_embs.shape == (300, 3, 512)
    assert templates.shape == (300, 512)

    # Check splits count
    assert np.sum(splits == "train") == 180
    assert np.sum(splits == "test") == 120

    # Check templates are L2-normalized
    template_norms = np.linalg.norm(templates, axis=1)
    assert np.allclose(template_norms, 1.0, atol=1e-4)


def test_face_baseline_metrics_and_separation():
    metrics_path = Path("results/face_eer.json")
    assert metrics_path.is_file(), "results/face_eer.json must exist"

    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["num_test_subjects"] == 120
    assert metrics["num_genuine_scores"] == 360
    assert metrics["num_impostor_scores"] == 42840

    # EER must be low (target << 10%)
    eer = metrics["eer"]
    assert eer < 0.05, f"Face-only EER should be under 5%, got {eer * 100:.2f}%"

    # Rank-1 accuracy should be high (target > 90%)
    rank1 = metrics["rank_1_accuracy"]
    assert rank1 > 0.90, f"Rank-1 identification accuracy should exceed 90%, got {rank1 * 100:.2f}%"

    # Separation between genuine and impostor means
    gen_mean = metrics["genuine_mean"]
    imp_mean = metrics["impostor_mean"]
    assert gen_mean - imp_mean > 0.5, f"Separation between genuine and impostor should be > 0.5, got {gen_mean - imp_mean:.4f}"
