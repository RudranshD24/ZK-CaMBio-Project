"""src/fusion/extractor.py

Fuses cached face and fingerprint embeddings and saves fused vectors
for all 300 virtual subjects to data/processed/fused_embeddings.npz.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

try:
    from src.fusion.fuse import fuse_embeddings_feature_level
except ImportError:
    from fusion.fuse import fuse_embeddings_feature_level


def extract_and_cache_fused(
    face_path: str | Path = "data/processed/face_embeddings.npz",
    finger_path: str | Path = "data/processed/finger_embeddings_resnet.npz",
    output_path: str | Path = "data/processed/fused_embeddings.npz",
    w: float = 0.60,
) -> dict[str, Any]:
    """Loads face (512-d) and fingerprint (256-d) cached embeddings,

    applies feature-level fusion with weight w (default w=0.60), and saves
    fused 768-d unit-norm representations for all 300 subjects.
    """
    face_data = np.load(face_path)
    finger_data = np.load(finger_path)

    # Sanity checks
    assert np.array_equal(face_data["subject_ids"], finger_data["subject_ids"]), "Subject ID mismatch!"
    assert np.array_equal(face_data["splits"], finger_data["splits"]), "Splits mismatch!"

    subject_ids = face_data["subject_ids"]
    splits = face_data["splits"]
    finger_dbs = finger_data["fingerprint_dbs"]
    face_ids = face_data["face_ids"]
    finger_ids = finger_data["fingerprint_ids"]

    # Enroll templates: fusion of L2-normalized face template and finger template
    tmpl_face = face_data["enroll_templates"]  # (300, 512)
    tmpl_finger = finger_data["enroll_templates"]  # (300, 256)
    tmpl_fused = fuse_embeddings_feature_level(tmpl_face, tmpl_finger, w=w)  # (300, 768)

    # Check template unit norms
    tmpl_norms = np.linalg.norm(tmpl_fused, axis=-1)
    assert np.allclose(tmpl_norms, 1.0, atol=1e-4), "Fused templates must have unit norm"

    # Enroll embeddings (5 impressions per subject)
    enr_face = face_data["enroll_embeddings"]  # (300, 5, 512)
    enr_finger = finger_data["enroll_embeddings"]  # (300, 5, 256)
    enr_fused = fuse_embeddings_feature_level(enr_face, enr_finger, w=w)  # (300, 5, 768)

    # Probe embeddings (3 probes per subject, paired probe k to probe k)
    prb_face = face_data["probe_embeddings"]  # (300, 3, 512)
    prb_finger = finger_data["probe_embeddings"]  # (300, 3, 256)
    prb_fused = fuse_embeddings_feature_level(prb_face, prb_finger, w=w)  # (300, 3, 768)

    # Check probe unit norms
    prb_norms = np.linalg.norm(prb_fused, axis=-1)
    assert np.allclose(prb_norms, 1.0, atol=1e-4), "Fused probes must have unit norm"

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        out_p,
        subject_ids=subject_ids,
        splits=splits,
        fingerprint_dbs=finger_dbs,
        face_ids=face_ids,
        fingerprint_ids=finger_ids,
        enroll_templates=tmpl_fused,
        enroll_embeddings=enr_fused,
        probe_embeddings=prb_fused,
        fusion_weight_face=np.float32(w),
    )
    print(f"Saved fused embeddings (768-d, w={w:.2f}) for {len(subject_ids)} subjects to: {out_p}")

    return {
        "num_subjects": len(subject_ids),
        "embedding_dim": tmpl_fused.shape[-1],
        "weight_face": float(w),
        "output_path": str(out_p),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fuse and cache biometric embeddings")
    parser.add_argument("--weight", type=float, default=0.60, help="Face weight w in [0, 1]")
    parser.add_argument(
        "--output", default="data/processed/fused_embeddings.npz", help="Output path"
    )
    args = parser.parse_args()

    extract_and_cache_fused(w=args.weight, output_path=args.output)
