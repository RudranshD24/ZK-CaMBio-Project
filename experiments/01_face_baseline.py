"""experiments/01_face_baseline.py

Evaluates the face-only recognition baseline on the 120 test virtual subjects.
Computes:
- Genuine and impostor cosine similarity scores
- EER (Equal Error Rate) and EER threshold
- 95% Bootstrap Confidence Interval for EER over test subjects
- ROC curve (FPR vs TPR) -> results/face_roc.png
- CMC curve (Rank-1 to Rank-20) -> results/face_cmc.png
- Score distribution histogram -> results/face_score_dist.png
- Saves results/face_eer.json, results/face_genuine_scores.npy, results/face_impostor_scores.npy
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from sklearn.metrics import roc_curve


def compute_eer(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Computes Equal Error Rate (EER), operating threshold, and ROC curves."""
    labels = np.concatenate([np.ones_like(genuine_scores), np.zeros_like(impostor_scores)])
    scores = np.concatenate([genuine_scores, impostor_scores])

    fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
    fnr = 1.0 - tpr

    # Find the threshold where FAR (fpr) == FRR (fnr)
    try:
        # Interpolate fnr - fpr
        diff = fnr - fpr
        # Find index near zero crossing
        idx = np.argmin(np.abs(diff))
        eer = (fpr[idx] + fnr[idx]) / 2.0
        eer_thresh = thresholds[idx]
    except Exception:
        # Fallback to linear interpolation
        f_diff = interp1d(thresholds, fnr - fpr, fill_value="extrapolate")
        eer_thresh = brentq(f_diff, thresholds.min(), thresholds.max())
        eer = float(interp1d(thresholds, fpr, fill_value="extrapolate")(eer_thresh))

    return float(eer), float(eer_thresh), fpr, tpr


def compute_cmc(
    templates: np.ndarray,
    probe_matrix: np.ndarray,
    max_rank: int = 20,
) -> np.ndarray:
    """Computes Cumulative Match Characteristic (CMC) curve.

    templates: (N, D) array of enrolled templates for N subjects.
    probe_matrix: (N, P, D) array of P probe embeddings for each subject.
    Returns: cmc array of length max_rank (fractions from 0 to 1).
    """
    num_subjects, num_probes, _ = probe_matrix.shape
    total_probes = num_subjects * num_probes

    rank_counts = np.zeros(max_rank, dtype=np.int32)

    for true_idx in range(num_subjects):
        for p_idx in range(num_probes):
            probe_emb = probe_matrix[true_idx, p_idx]  # (D,)
            sims = np.dot(templates, probe_emb)         # (N,)

            # Ranks: descending order of similarity
            ranked_indices = np.argsort(-sims)
            match_rank = int(np.where(ranked_indices == true_idx)[0][0])  # 0-indexed

            if match_rank < max_rank:
                rank_counts[match_rank:] += 1

    return rank_counts / total_probes


def bootstrap_eer_ci(
    templates: np.ndarray,
    probe_matrix: np.ndarray,
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """Computes a 95% bootstrap confidence interval for EER by resampling test subjects."""
    rng = np.random.RandomState(seed)
    num_subjects = templates.shape[0]
    num_probes = probe_matrix.shape[1]

    bootstrap_eers = []

    for _ in range(n_bootstraps):
        sampled_indices = rng.choice(num_subjects, size=num_subjects, replace=True)

        sample_templates = templates[sampled_indices]
        sample_probes = probe_matrix[sampled_indices]

        # Genuine scores
        gen = []
        for i in range(num_subjects):
            for k in range(num_probes):
                gen.append(float(np.dot(sample_templates[i], sample_probes[i, k])))

        # Impostor scores
        imp = []
        for i in range(num_subjects):
            for j in range(num_subjects):
                if sampled_indices[i] != sampled_indices[j]:
                    for k in range(num_probes):
                        imp.append(float(np.dot(sample_templates[i], sample_probes[j, k])))

        if gen and imp:
            eer, _, _, _ = compute_eer(np.array(gen), np.array(imp))
            bootstrap_eers.append(eer)

    lower = float(np.percentile(bootstrap_eers, 2.5))
    upper = float(np.percentile(bootstrap_eers, 97.5))
    return lower, upper


def main() -> None:
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    cache_path = Path("data/processed/face_embeddings.npz")
    if not cache_path.is_file():
        raise FileNotFoundError(f"Embeddings cache not found: {cache_path}")

    data = np.load(cache_path)
    splits = data["splits"]

    # Filter to test subjects only (120 subjects)
    test_mask = splits == "test"
    test_subject_ids = data["subject_ids"][test_mask]
    test_templates = data["enroll_templates"][test_mask]      # (120, 512)
    test_probe_matrix = data["probe_embeddings"][test_mask]   # (120, 3, 512)

    num_test = len(test_subject_ids)
    num_probes = test_probe_matrix.shape[1]
    print(f"Loaded {num_test} test subjects ({num_probes} probes each).")

    # 1. Compute Genuine and Impostor Scores
    genuine_scores_list = []
    impostor_scores_list = []

    for i in range(num_test):
        tmpl_i = test_templates[i]

        # Genuine: template i vs probes i
        for k in range(num_probes):
            score = float(np.dot(tmpl_i, test_probe_matrix[i, k]))
            genuine_scores_list.append(score)

        # Impostor: template i vs probes j (j != i)
        for j in range(num_test):
            if i != j:
                for k in range(num_probes):
                    score = float(np.dot(tmpl_i, test_probe_matrix[j, k]))
                    impostor_scores_list.append(score)

    genuine_scores = np.array(genuine_scores_list, dtype=np.float32)
    impostor_scores = np.array(impostor_scores_list, dtype=np.float32)

    print(f"Total Genuine Scores:  {len(genuine_scores)}")
    print(f"Total Impostor Scores: {len(impostor_scores)}")
    print(f"Genuine Score Mean (Std):  {np.mean(genuine_scores):.4f} ({np.std(genuine_scores):.4f})")
    print(f"Impostor Score Mean (Std): {np.mean(impostor_scores):.4f} ({np.std(impostor_scores):.4f})")

    # Save raw score arrays
    np.save(results_dir / "face_genuine_scores.npy", genuine_scores)
    np.save(results_dir / "face_impostor_scores.npy", impostor_scores)
    print("Saved raw score arrays to results/face_genuine_scores.npy and face_impostor_scores.npy")

    # 2. Compute EER
    eer, eer_threshold, fpr, tpr = compute_eer(genuine_scores, impostor_scores)
    print(f"Face-only EER: {eer * 100:.2f}% (Operating Threshold: {eer_threshold:.4f})")

    # 3. Bootstrap 95% CI over test subjects
    print("Computing 95% Bootstrap CI over test subjects (1000 resamples)...")
    ci_lower, ci_upper = bootstrap_eer_ci(test_templates, test_probe_matrix, n_bootstraps=1000, seed=42)
    print(f"95% Bootstrap CI for EER: [{ci_lower * 100:.2f}%, {ci_upper * 100:.2f}%]")

    # 4. Compute CMC
    cmc = compute_cmc(test_templates, test_probe_matrix, max_rank=20)
    print(f"Rank-1  Identification Accuracy: {cmc[0] * 100:.2f}%")
    print(f"Rank-5  Identification Accuracy: {cmc[4] * 100:.2f}%")
    print(f"Rank-10 Identification Accuracy: {cmc[9] * 100:.2f}%")

    # 5. Plot ROC Curve
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(fpr * 100, tpr * 100, color="#1f77b4", lw=2, label=f"Face Baseline (EER = {eer * 100:.2f}%)")
    ax.plot([0, 100], [100, 0], color="gray", linestyle="--", lw=1, label="EER Reference Line")
    ax.scatter([eer * 100], [(1 - eer) * 100], color="#d62728", zorder=5, label=f"EER Point ({eer * 100:.2f}%)")
    ax.set_title("ROC Curve — Face Recognition Baseline (120 Test Subjects)", fontsize=12)
    ax.set_xlabel("False Match Rate / FAR (%)", fontsize=11)
    ax.set_ylabel("True Acceptance Rate / (1 - FRR) (%)", fontsize=11)
    ax.set_xlim([0, 100])
    ax.set_ylim([0, 105])
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right")
    roc_path = results_dir / "face_roc.png"
    plt.tight_layout()
    plt.savefig(roc_path, dpi=200)
    plt.close()
    print(f"Saved ROC curve to: {roc_path}")

    # 6. Plot CMC Curve
    fig, ax = plt.subplots(figsize=(7, 5))
    ranks = np.arange(1, 21)
    ax.plot(ranks, cmc * 100, marker="o", color="#2ca02c", lw=2, label="Identification Accuracy")
    ax.set_title("CMC Curve — Face Identification (120 Test Subjects)", fontsize=12)
    ax.set_xlabel("Rank", fontsize=11)
    ax.set_ylabel("Rank-k Identification Accuracy (%)", fontsize=11)
    ax.set_xticks(ranks)
    ax.set_ylim([max(0, min(cmc * 100) - 5), 102])
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right")
    cmc_path = results_dir / "face_cmc.png"
    plt.tight_layout()
    plt.savefig(cmc_path, dpi=200)
    plt.close()
    print(f"Saved CMC curve to: {cmc_path}")

    # 7. Plot Score Distributions
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(impostor_scores, bins=60, density=True, alpha=0.6, color="#d62728", label=f"Impostor (n={len(impostor_scores)})")
    ax.hist(genuine_scores, bins=40, density=True, alpha=0.6, color="#1f77b4", label=f"Genuine (n={len(genuine_scores)})")
    ax.axvline(eer_threshold, color="black", linestyle="--", lw=1.5, label=f"EER Threshold = {eer_threshold:.4f}")
    ax.set_title("Score Distributions — Face Cosine Similarity", fontsize=12)
    ax.set_xlabel("Cosine Similarity", fontsize=11)
    ax.set_ylabel("Density", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    dist_path = results_dir / "face_score_dist.png"
    plt.tight_layout()
    plt.savefig(dist_path, dpi=200)
    plt.close()
    print(f"Saved Score Distribution plot to: {dist_path}")

    # 8. Save Metrics JSON for Traceability
    metrics: dict[str, Any] = {
        "model": "InceptionResnetV1",
        "pretrained_dataset": "VGGFace2 (Cao et al., BMVC 2018)",
        "embedding_dim": 512,
        "input_resolution": "112x112 resized to 160x160",
        "normalization": "(x - 127.5) / 128.0",
        "num_test_subjects": num_test,
        "num_genuine_scores": len(genuine_scores),
        "num_impostor_scores": len(impostor_scores),
        "eer": round(eer, 6),
        "eer_percent": round(eer * 100, 2),
        "eer_threshold": round(eer_threshold, 6),
        "eer_ci_95": [round(ci_lower, 6), round(ci_upper, 6)],
        "eer_ci_95_percent": [round(ci_lower * 100, 2), round(ci_upper * 100, 2)],
        "rank_1_accuracy": round(float(cmc[0]), 4),
        "rank_5_accuracy": round(float(cmc[4]), 4),
        "rank_10_accuracy": round(float(cmc[9]), 4),
        "genuine_mean": round(float(np.mean(genuine_scores)), 4),
        "genuine_std": round(float(np.std(genuine_scores)), 4),
        "impostor_mean": round(float(np.mean(impostor_scores)), 4),
        "impostor_std": round(float(np.std(impostor_scores)), 4),
    }

    metrics_path = results_dir / "face_eer.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)
    print(f"Saved metrics JSON to: {metrics_path}")


if __name__ == "__main__":
    main()
