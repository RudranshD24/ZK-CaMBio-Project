"""src/face/extractor.py

Extracts and caches face embeddings for all 300 virtual subjects.
Reads data/processed/split_manifest.json and streams images using FaceLoader.
Outputs: data/processed/face_embeddings.npz
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from tqdm import tqdm

try:
    from src.data.face_loader import FaceLoader
    from src.face.encoder import FaceEncoder
except ImportError:
    from data.face_loader import FaceLoader
    from face.encoder import FaceEncoder


def extract_and_cache_face_embeddings(
    manifest_path: str | Path = "data/processed/split_manifest.json",
    output_path: str | Path = "data/processed/face_embeddings.npz",
    encoder: FaceEncoder | None = None,
    loader: FaceLoader | None = None,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if encoder is None:
        encoder = FaceEncoder()
    if loader is None:
        loader = FaceLoader()

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    all_subjects = manifest["train"] + manifest["test"]
    num_subjects = len(all_subjects)

    subject_ids = []
    splits = []
    face_ids = []
    enroll_embeddings_list = []
    probe_embeddings_list = []
    enroll_templates_list = []

    print(f"Extracting face embeddings for {num_subjects} subjects on device '{encoder.device}'...")

    for subj in tqdm(all_subjects, desc="Extracting faces"):
        s_id = subj["subject_id"]
        split = subj["split"]
        face_id = subj["face_id"]

        # Load 5 enroll images and 3 probe images
        enroll_imgs = [loader.load_image(face_id, fn) for fn in subj["face_enroll_files"]]
        probe_imgs = [loader.load_image(face_id, fn) for fn in subj["face_probe_files"]]

        # Extract embeddings
        enroll_embs = encoder.extract_batch(enroll_imgs)  # shape (5, 512)
        probe_embs = encoder.extract_batch(probe_imgs)    # shape (3, 512)

        # Enroll template: L2-normalized mean of 5 enroll embeddings
        template = np.mean(enroll_embs, axis=0)
        t_norm = np.linalg.norm(template)
        if t_norm > 0:
            template = template / t_norm

        subject_ids.append(s_id)
        splits.append(split)
        face_ids.append(face_id)
        enroll_embeddings_list.append(enroll_embs)
        probe_embeddings_list.append(probe_embs)
        enroll_templates_list.append(template)

    enroll_embs_arr = np.array(enroll_embeddings_list, dtype=np.float32)      # (300, 5, 512)
    probe_embs_arr = np.array(probe_embeddings_list, dtype=np.float32)        # (300, 3, 512)
    enroll_templates_arr = np.array(enroll_templates_list, dtype=np.float32)  # (300, 512)
    subject_ids_arr = np.array(subject_ids)
    splits_arr = np.array(splits)
    face_ids_arr = np.array(face_ids)

    np.savez_compressed(
        output_path,
        subject_ids=subject_ids_arr,
        splits=splits_arr,
        face_ids=face_ids_arr,
        enroll_embeddings=enroll_embs_arr,
        probe_embeddings=probe_embs_arr,
        enroll_templates=enroll_templates_arr,
    )

    print(f"Cached face embeddings saved to: {output_path.resolve()}")
    return {
        "num_subjects": num_subjects,
        "output_path": str(output_path),
        "enroll_shape": enroll_embs_arr.shape,
        "probe_shape": probe_embs_arr.shape,
        "template_shape": enroll_templates_arr.shape,
    }


if __name__ == "__main__":
    extract_and_cache_face_embeddings()
