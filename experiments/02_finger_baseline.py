"""experiments/02_finger_baseline.py

Evaluates fingerprint baseline models on the 120 test virtual subjects
under Protocol D-009 (same-DB impostors only: 40 subjects per DB).

Evaluates:
- Baseline A (Classical): Gabor filter-bank grid features (256-d)
- Baseline B (Learned): FingerResNet18 fine-tuned with CosFace margin loss (256-d)

Outputs:
- results/finger_eer.json: Complete metrics for Baseline A and B (pooled and per-DB)
- results/finger_roc.png: ROC curves (pooled and per-DB)
- results/finger_cmc.png: CMC curves (per-DB gallery 40, plus pooled gallery 120)
- results/finger_score_dist.png: Score distribution histograms for both models
- results/finger_genuine_scores_gabor.npy, results/finger_impostor_scores_gabor.npy
- results/finger_genuine_scores_resnet.npy, results/finger_impostor_scores_resnet.npy
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


def compute_eer(
    genuine_scores: np.ndarray, impostor_scores: np.ndarray
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


def bootstrap_eer_ci_same_db(
    db_templates: dict[str, np.ndarray],
    db_probes: dict[str, np.ndarray],
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """Computes a 95% bootstrap confidence interval for pooled same-DB EER

    by resampling test subjects within each database.
    """
    rng = np.random.RandomState(seed)
    bootstrap_eers = []

    db_names = list(db_templates.keys())

    for _ in range(n_bootstraps):
        pooled_gen = []
        pooled_imp = []

        for db in db_names:
            tmpls = db_templates[db]  # (N_db, D)
            prbs = db_probes[db]  # (N_db, P, D)
            n_sub = tmpls.shape[0]
            n_prb = prbs.shape[1]

            sampled_idx = rng.choice(n_sub, size=n_sub, replace=True)
            s_tmpls = tmpls[sampled_idx]
            s_prbs = prbs[sampled_idx]

            for i in range(n_sub):
                for k in range(n_prb):
                    pooled_gen.append(float(np.dot(s_tmpls[i], s_prbs[i, k])))
                for j in range(n_sub):
                    if sampled_idx[i] != sampled_idx[j]:
                        for k in range(n_prb):
                            pooled_imp.append(float(np.dot(s_tmpls[i], s_prbs[j, k])))

        if pooled_gen and pooled_imp:
            eer, _, _, _ = compute_eer(np.array(pooled_gen), np.array(pooled_imp))
            bootstrap_eers.append(eer)

    lower = float(np.percentile(bootstrap_eers, 2.5))
    upper = float(np.percentile(bootstrap_eers, 97.5))
    return lower, upper


def evaluate_model(
    cache_path: Path,
    model_name: str,
) -> dict[str, Any]:
    """Evaluates a single model cache under Protocol D-009."""
    data = np.load(cache_path)
    splits = data["splits"]
    test_mask = splits == "test"

    sub_ids = data["subject_ids"][test_mask]
    dbs = data["fingerprint_dbs"][test_mask]
    templates = data["enroll_templates"][test_mask]
    probe_matrix = data["probe_embeddings"][test_mask]

    db_templates: dict[str, np.ndarray] = {}
    db_probes: dict[str, np.ndarray] = {}
    db_names = sorted(list(set(dbs)))

    for db in db_names:
        db_mask = dbs == db
        db_templates[db] = templates[db_mask]
        db_probes[db] = probe_matrix[db_mask]

    # Scores: per-DB and pooled
    per_db_metrics = {}
    pooled_genuine = []
    pooled_impostor = []

    for db in db_names:
        tmpls = db_templates[db]  # (40, D)
        prbs = db_probes[db]  # (40, 3, D)
        n_db = tmpls.shape[0]
        n_prb = prbs.shape[1]

        db_gen = []
        db_imp = []

        for i in range(n_db):
            for k in range(n_prb):
                db_gen.append(float(np.dot(tmpls[i], prbs[i, k])))
            for j in range(n_db):
                if i != j:
                    for k in range(n_prb):
                        db_imp.append(float(np.dot(tmpls[i], prbs[j, k])))

        db_gen_arr = np.array(db_gen, dtype=np.float32)
        db_imp_arr = np.array(db_imp, dtype=np.float32)

        eer, thresh, fpr, tpr = compute_eer(db_gen_arr, db_imp_arr)
        cmc = compute_cmc(tmpls, prbs, max_rank=20)

        per_db_metrics[db] = {
            "num_subjects": n_db,
            "num_genuine": len(db_gen),
            "num_impostor": len(db_imp),
            "eer": float(eer),
            "eer_percent": round(eer * 100, 2),
            "eer_threshold": float(thresh),
            "rank_1_accuracy": float(cmc[0]),
            "rank_1_percent": round(float(cmc[0]) * 100, 2),
            "rank_5_accuracy": float(cmc[4]) if len(cmc) > 4 else float(cmc[-1]),
            "rank_10_accuracy": float(cmc[9]) if len(cmc) > 9 else float(cmc[-1]),
            "genuine_mean": float(np.mean(db_gen_arr)),
            "genuine_std": float(np.std(db_gen_arr)),
            "impostor_mean": float(np.mean(db_imp_arr)),
            "impostor_std": float(np.std(db_imp_arr)),
            "fpr": fpr,
            "tpr": tpr,
            "cmc": cmc,
            "genuine_scores": db_gen_arr,
            "impostor_scores": db_imp_arr,
        }

        pooled_genuine.extend(db_gen)
        pooled_impostor.extend(db_imp)

    pooled_gen_arr = np.array(pooled_genuine, dtype=np.float32)
    pooled_imp_arr = np.array(pooled_impostor, dtype=np.float32)

    p_eer, p_thresh, p_fpr, p_tpr = compute_eer(pooled_gen_arr, pooled_imp_arr)
    ci_lower, ci_upper = bootstrap_eer_ci_same_db(db_templates, db_probes, n_bootstraps=1000, seed=42)

    # Pooled CMC across all 120 gallery (note: cross-DB makes gallery separation easier)
    p_cmc = compute_cmc(templates, probe_matrix, max_rank=20)

    # Average per-DB CMC (fair identification metric, gallery size = 40)
    avg_per_db_cmc = np.mean([per_db_metrics[db]["cmc"] for db in db_names], axis=0)

    pooled_metrics = {
        "num_test_subjects": len(sub_ids),
        "num_genuine_scores": len(pooled_genuine),
        "num_impostor_scores": len(pooled_impostor),
        "eer": float(p_eer),
        "eer_percent": round(p_eer * 100, 2),
        "eer_threshold": float(p_thresh),
        "eer_ci_95": [float(ci_lower), float(ci_upper)],
        "eer_ci_95_percent": [round(ci_lower * 100, 2), round(ci_upper * 100, 2)],
        "rank_1_accuracy_fair_gallery40": float(avg_per_db_cmc[0]),
        "rank_1_percent_fair_gallery40": round(float(avg_per_db_cmc[0]) * 100, 2),
        "rank_5_accuracy_fair_gallery40": float(avg_per_db_cmc[4]),
        "rank_1_accuracy_pooled_gallery120": float(p_cmc[0]),
        "rank_1_percent_pooled_gallery120": round(float(p_cmc[0]) * 100, 2),
        "genuine_mean": float(np.mean(pooled_gen_arr)),
        "genuine_std": float(np.std(pooled_gen_arr)),
        "impostor_mean": float(np.mean(pooled_imp_arr)),
        "impostor_std": float(np.std(pooled_imp_arr)),
        "fpr": p_fpr,
        "tpr": p_tpr,
        "cmc_fair_gallery40": avg_per_db_cmc,
        "cmc_pooled_gallery120": p_cmc,
        "genuine_scores": pooled_gen_arr,
        "impostor_scores": pooled_imp_arr,
    }

    return {
        "model_name": model_name,
        "pooled": pooled_metrics,
        "per_db": per_db_metrics,
    }


def main() -> None:
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    gabor_cache = Path("data/processed/finger_embeddings_gabor.npz")
    resnet_cache = Path("data/processed/finger_embeddings_resnet.npz")

    if not gabor_cache.is_file():
        raise FileNotFoundError(f"Gabor cache not found: {gabor_cache}")
    if not resnet_cache.is_file():
        raise FileNotFoundError(f"ResNet18 cache not found: {resnet_cache}")

    print("Evaluating Baseline A (Gabor 256-d)...")
    res_a = evaluate_model(gabor_cache, "Baseline A: Gabor Filter-Bank (256-d)")

    print("Evaluating Baseline B (FingerResNet18 256-d)...")
    res_b = evaluate_model(resnet_cache, "Baseline B: FingerResNet18 CosFace (256-d)")

    # Save raw score arrays
    np.save(results_dir / "finger_genuine_scores_gabor.npy", res_a["pooled"]["genuine_scores"])
    np.save(results_dir / "finger_impostor_scores_gabor.npy", res_a["pooled"]["impostor_scores"])
    np.save(results_dir / "finger_genuine_scores_resnet.npy", res_b["pooled"]["genuine_scores"])
    np.save(results_dir / "finger_impostor_scores_resnet.npy", res_b["pooled"]["impostor_scores"])
    print("Saved raw score arrays to results/.")

    # 1. Plot ROC Curves
    plt.figure(figsize=(9, 7))
    plt.plot(
        res_a["pooled"]["fpr"],
        res_a["pooled"]["tpr"],
        color="#2b5c8f",
        lw=2.5,
        label=f"Gabor Pooled (EER = {res_a['pooled']['eer_percent']}%)",
    )
    plt.plot(
        res_b["pooled"]["fpr"],
        res_b["pooled"]["tpr"],
        color="#d95f02",
        lw=2.5,
        label=f"ResNet18 Pooled (EER = {res_b['pooled']['eer_percent']}%)",
    )

    # Per DB dashed lines
    colors = {"DB1_A": "#1b9e77", "DB2_A": "#7570b3", "DB3_A": "#e7298a"}
    for db in ["DB1_A", "DB2_A", "DB3_A"]:
        plt.plot(
            res_a["per_db"][db]["fpr"],
            res_a["per_db"][db]["tpr"],
            color=colors[db],
            ls="--",
            alpha=0.6,
            label=f"Gabor {db} (EER = {res_a['per_db'][db]['eer_percent']}%)",
        )
        plt.plot(
            res_b["per_db"][db]["fpr"],
            res_b["per_db"][db]["tpr"],
            color=colors[db],
            ls=":",
            lw=2.0,
            label=f"ResNet18 {db} (EER = {res_b['per_db'][db]['eer_percent']}%)",
        )

    plt.plot([0, 1], [0, 1], color="gray", linestyle="--", alpha=0.5)
    plt.xscale("log")
    plt.xlim([1e-4, 1.0])
    plt.ylim([0.0, 1.02])
    plt.xlabel("False Positive Rate (FPR) [log scale]", fontsize=12)
    plt.ylabel("True Positive Rate (TPR)", fontsize=12)
    plt.title("Fingerprint Verification ROC Curves (Protocol D-009)", fontsize=13, fontweight="bold")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend(loc="lower right", fontsize=9)
    plt.tight_layout()
    roc_plot_path = results_dir / "finger_roc.png"
    plt.savefig(roc_plot_path, dpi=200)
    plt.close()
    print(f"Saved ROC plot: {roc_plot_path}")

    # 2. Plot CMC Curves
    plt.figure(figsize=(9, 7))
    ranks = np.arange(1, 21)
    plt.plot(
        ranks,
        res_a["pooled"]["cmc_fair_gallery40"][:20] * 100,
        "o-",
        color="#2b5c8f",
        lw=2.2,
        label=f"Gabor (Gallery 40, Rank-1 = {res_a['pooled']['rank_1_percent_fair_gallery40']}%)",
    )
    plt.plot(
        ranks,
        res_b["pooled"]["cmc_fair_gallery40"][:20] * 100,
        "s-",
        color="#d95f02",
        lw=2.2,
        label=f"ResNet18 (Gallery 40, Rank-1 = {res_b['pooled']['rank_1_percent_fair_gallery40']}%)",
    )
    plt.plot(
        ranks,
        res_a["pooled"]["cmc_pooled_gallery120"][:20] * 100,
        "--",
        color="#2b5c8f",
        alpha=0.6,
        label=f"Gabor Pooled (Gallery 120 - easier, Rank-1 = {res_a['pooled']['rank_1_percent_pooled_gallery120']}%)",
    )
    plt.plot(
        ranks,
        res_b["pooled"]["cmc_pooled_gallery120"][:20] * 100,
        "--",
        color="#d95f02",
        alpha=0.6,
        label=f"ResNet18 Pooled (Gallery 120 - easier, Rank-1 = {res_b['pooled']['rank_1_percent_pooled_gallery120']}%)",
    )

    plt.xlabel("Rank", fontsize=12)
    plt.ylabel("Recognition Rate (%)", fontsize=12)
    plt.title("Cumulative Match Characteristic (CMC) (Protocol D-009)", fontsize=13, fontweight="bold")
    plt.grid(True, alpha=0.3)
    plt.xticks(np.arange(1, 21, 2))
    plt.legend(loc="lower right", fontsize=9)
    plt.tight_layout()
    cmc_plot_path = results_dir / "finger_cmc.png"
    plt.savefig(cmc_plot_path, dpi=200)
    plt.close()
    print(f"Saved CMC plot: {cmc_plot_path}")

    # 3. Plot Score Distributions
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Gabor
    ax0 = axes[0]
    ax0.hist(
        res_a["pooled"]["impostor_scores"],
        bins=60,
        density=True,
        alpha=0.6,
        color="#c0392b",
        label=f"Impostor (μ={res_a['pooled']['impostor_mean']:.3f}, σ={res_a['pooled']['impostor_std']:.3f})",
    )
    ax0.hist(
        res_a["pooled"]["genuine_scores"],
        bins=60,
        density=True,
        alpha=0.6,
        color="#27ae60",
        label=f"Genuine (μ={res_a['pooled']['genuine_mean']:.3f}, σ={res_a['pooled']['genuine_std']:.3f})",
    )
    ax0.axvline(
        res_a["pooled"]["eer_threshold"],
        color="black",
        linestyle="--",
        lw=1.5,
        label=f"EER Threshold ({res_a['pooled']['eer_threshold']:.3f})",
    )
    ax0.set_title(f"Baseline A: Gabor (EER = {res_a['pooled']['eer_percent']}%)", fontsize=11, fontweight="bold")
    ax0.set_xlabel("Cosine Similarity", fontsize=10)
    ax0.set_ylabel("Density", fontsize=10)
    ax0.legend(loc="upper left", fontsize=8.5)
    ax0.grid(True, alpha=0.3)

    # ResNet18
    ax1 = axes[1]
    ax1.hist(
        res_b["pooled"]["impostor_scores"],
        bins=60,
        density=True,
        alpha=0.6,
        color="#c0392b",
        label=f"Impostor (μ={res_b['pooled']['impostor_mean']:.3f}, σ={res_b['pooled']['impostor_std']:.3f})",
    )
    ax1.hist(
        res_b["pooled"]["genuine_scores"],
        bins=60,
        density=True,
        alpha=0.6,
        color="#27ae60",
        label=f"Genuine (μ={res_b['pooled']['genuine_mean']:.3f}, σ={res_b['pooled']['genuine_std']:.3f})",
    )
    ax1.axvline(
        res_b["pooled"]["eer_threshold"],
        color="black",
        linestyle="--",
        lw=1.5,
        label=f"EER Threshold ({res_b['pooled']['eer_threshold']:.3f})",
    )
    ax1.set_title(f"Baseline B: FingerResNet18 (EER = {res_b['pooled']['eer_percent']}%)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Cosine Similarity", fontsize=10)
    ax1.set_ylabel("Density", fontsize=10)
    ax1.legend(loc="upper left", fontsize=8.5)
    ax1.grid(True, alpha=0.3)

    plt.suptitle("Fingerprint Score Distributions (Protocol D-009 Same-DB Impostors)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    dist_plot_path = results_dir / "finger_score_dist.png"
    plt.savefig(dist_plot_path, dpi=200)
    plt.close()
    print(f"Saved score distribution plot: {dist_plot_path}")

    # Build summary JSON
    def clean_dict(m: dict[str, Any]) -> dict[str, Any]:
        return {
            "pooled": {k: v for k, v in m["pooled"].items() if k not in ("fpr", "tpr", "cmc_fair_gallery40", "cmc_pooled_gallery120", "genuine_scores", "impostor_scores")},
            "per_db": {
                db: {k: v for k, v in db_m.items() if k not in ("fpr", "tpr", "cmc", "genuine_scores", "impostor_scores")}
                for db, db_m in m["per_db"].items()
            },
        }

    winner = "Baseline B (FingerResNet18)" if res_b["pooled"]["eer"] < res_a["pooled"]["eer"] else "Baseline A (Gabor)"
    delta_eer = round((res_a["pooled"]["eer"] - res_b["pooled"]["eer"]) * 100, 2)

    summary_json = {
        "protocol": "D-009 (Same-DB Impostors Only, 40 subjects/DB, 14,040 impostor comparisons pooled)",
        "input_resolution": "128x128 (intensity normalized, block-variance cropped, CLAHE)",
        "embedding_dim": 256,
        "test_subjects": 120,
        "baseline_a_gabor": clean_dict(res_a),
        "baseline_b_resnet18": clean_dict(res_b),
        "comparison": {
            "winner": winner,
            "delta_eer_percent": delta_eer,
            "interpretation": (
                f"ResNet18 achieves {res_b['pooled']['eer_percent']}% EER vs Gabor's {res_a['pooled']['eer_percent']}% EER "
                f"(delta = {delta_eer:+.2f}%). "
                f"ResNet18 Rank-1 on gallery 40 is {res_b['pooled']['rank_1_percent_fair_gallery40']}% vs Gabor's "
                f"{res_a['pooled']['rank_1_percent_fair_gallery40']}%."
            ),
        },
    }

    json_path = results_dir / "finger_eer.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"Saved evaluation metrics JSON: {json_path}")
    print("\n--- STAGE 2B SUMMARY ---")
    print(f"Baseline A (Gabor):      Pooled EER = {res_a['pooled']['eer_percent']}% (95% CI {res_a['pooled']['eer_ci_95_percent']}%), Rank-1 = {res_a['pooled']['rank_1_percent_fair_gallery40']}%")
    print(f"Baseline B (ResNet18):   Pooled EER = {res_b['pooled']['eer_percent']}% (95% CI {res_b['pooled']['eer_ci_95_percent']}%), Rank-1 = {res_b['pooled']['rank_1_percent_fair_gallery40']}%")
    print(f"Winner: {winner}")


if __name__ == "__main__":
    main()
