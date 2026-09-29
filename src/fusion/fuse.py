"""src/fusion/fuse.py

Multimodal biometric fusion module for ZK-CaMBio.
Implements:
1. Feature-level fusion (768-d concatenation of sqrt(w)*face and sqrt(1-w)*fingerprint).
2. Score-level fusion (z-score normalized weighted sum).
3. Biometric metric utilities: d-prime, FNMR @ FMR, EER, and CMC.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from sklearn.metrics import roc_curve


def fuse_embeddings_feature_level(
    face_emb: np.ndarray,
    finger_emb: np.ndarray,
    w: float = 0.60,
) -> np.ndarray:
    """Fuses L2-normalized face (512-d) and fingerprint (256-d) embeddings into

    a 768-d unit-norm vector:
    fused = [sqrt(w) * f_face, sqrt(1 - w) * f_finger]

    Because ||f_face|| = 1 and ||f_finger|| = 1,
    ||fused||^2 = w*1 + (1 - w)*1 = 1 (unit norm preserved).
    Cosine similarity on fused vectors equals:
    cos(fused_1, fused_2) = w * cos(face_1, face_2) + (1 - w) * cos(finger_1, finger_2).
    """
    if not (0.0 <= w <= 1.0):
        raise ValueError(f"Weight w must be in [0, 1], got {w}")

    # Ensure last dimension matches 512 and 256
    face_dim = face_emb.shape[-1]
    finger_dim = finger_emb.shape[-1]
    if face_dim != 512 or finger_dim != 256:
        raise ValueError(f"Expected face_dim=512 and finger_dim=256, got {face_dim} and {finger_dim}")

    scale_face = np.sqrt(w).astype(np.float32)
    scale_finger = np.sqrt(1.0 - w).astype(np.float32)

    scaled_face = face_emb * scale_face
    scaled_finger = finger_emb * scale_finger

    fused = np.concatenate([scaled_face, scaled_finger], axis=-1).astype(np.float32)
    return fused


def compute_d_prime(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> float:
    """Computes the decidability index (d-prime):

    d' = |mu_gen - mu_imp| / sqrt(0.5 * (var_gen + var_imp))
    """
    mu_g = np.mean(genuine_scores)
    mu_i = np.mean(impostor_scores)
    var_g = np.var(genuine_scores)
    var_i = np.var(impostor_scores)

    denom = np.sqrt(0.5 * (var_g + var_i))
    if denom == 0.0:
        return 0.0
    return float(np.abs(mu_g - mu_i) / denom)


def compute_fnmr_at_fmr(
    genuine_scores: np.ndarray,
    impostor_scores: np.ndarray,
    target_fmr: float = 0.01,
) -> tuple[float, float]:
    """Computes FNMR (False Non-Match Rate) at a given operational FMR (False Match Rate).

    Returns (fnmr, threshold).
    """
    labels = np.concatenate([np.ones_like(genuine_scores), np.zeros_like(impostor_scores)])
    scores = np.concatenate([genuine_scores, impostor_scores])

    fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
    fnr = 1.0 - tpr

    # Find threshold where FPR <= target_fmr
    idx = np.where(fpr <= target_fmr)[0]
    if len(idx) == 0:
        thresh = thresholds[0]
        fnmr = 1.0
    else:
        chosen_idx = idx[-1]
        thresh = thresholds[chosen_idx]
        fnmr = fnr[chosen_idx]

    return float(fnmr), float(thresh)


def compute_eer(
    genuine_scores: np.ndarray,
    impostor_scores: np.ndarray,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Computes Equal Error Rate (EER), operating threshold, and ROC curves."""
    labels = np.concatenate([np.ones_like(genuine_scores), np.zeros_like(impostor_scores)])
    scores = np.concatenate([genuine_scores, impostor_scores])

    fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
    fnr = 1.0 - tpr

    diff = fnr - fpr
    idx = np.argmin(np.abs(diff))
    eer = float((fpr[idx] + fnr[idx]) / 2.0)
    eer_thresh = float(thresholds[idx])

    if np.isnan(eer) or eer == 0.0 or eer == 1.0:
        try:
            f_diff = interp1d(thresholds, fnr - fpr, fill_value="extrapolate")
            eer_thresh = float(brentq(f_diff, thresholds.min(), thresholds.max()))
            eer = float(interp1d(thresholds, fpr, fill_value="extrapolate")(eer_thresh))
        except Exception:
            pass

    return float(eer), float(eer_thresh), fpr, tpr


def compute_cmc(
    templates: np.ndarray,
    probe_matrix: np.ndarray,
    max_rank: int = 20,
) -> np.ndarray:
    """Computes Cumulative Match Characteristic (CMC) curve within a gallery.

    templates: (N, D) gallery templates
    probe_matrix: (N, P, D) probe embeddings
    """
    num_subjects, num_probes, _ = probe_matrix.shape
    total_probes = num_subjects * num_probes

    rank_counts = np.zeros(max_rank, dtype=np.int32)

    for true_idx in range(num_subjects):
        for p_idx in range(num_probes):
            probe_emb = probe_matrix[true_idx, p_idx]
            sims = np.dot(templates, probe_emb)

            ranked_indices = np.argsort(-sims)
            match_rank = int(np.where(ranked_indices == true_idx)[0][0])

            if match_rank < max_rank:
                rank_counts[match_rank:] += 1

    return rank_counts / total_probes
