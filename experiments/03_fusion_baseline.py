"""experiments/03_fusion_baseline.py

Multimodal biometric fusion and unprotected baseline evaluation (Phase 3).
1. Tunes fusion weight w on the 30 validation subjects ONLY (grid in [0.1, 0.9]).
   - Saves validation curve: results/fusion_val_weight_tuning.png
   - Saves test sensitivity plot: results/fusion_test_weight_sensitivity.png (analysis only)
2. Fits z-score normalization parameters on validation subjects for score-level fusion.
3. Caches fused 768-d embeddings for all 300 subjects in data/processed/fused_embeddings.npz.
4. Evaluates systems on the 120 test subjects under Protocol D-009 (same-DB impostors):
   - S1: Face-only (512-d InceptionResnetV1)
   - S2: Finger-only (256-d FingerResNet18 V2)
   - S3: Fused feature-level (768-d, w=0.60)
   - S3b: Fused score-level (z-score weighted sum)
5. Generates:
   - results/fused_unprotected.json
   - results/fusion_roc.png
   - results/fusion_cmc.png
   - results/fusion_score_dist.png
   - Raw score arrays (.npy)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

try:
    from src.fusion.extractor import extract_and_cache_fused
    from src.fusion.fuse import (
        compute_cmc,
        compute_d_prime,
        compute_eer,
        compute_fnmr_at_fmr,
    )
except ImportError:
    from fusion.extractor import extract_and_cache_fused
    from fusion.fuse import (
        compute_cmc,
        compute_d_prime,
        compute_eer,
        compute_fnmr_at_fmr,
    )



def tune_fusion_weight_val(
    face_data: Any,
    finger_data: Any,
    val_indices: list[int],
    grid: np.ndarray,
) -> tuple[float, list[dict[str, float]], tuple[float, float, float, float]]:
    """Evaluates validation EER across weight grid w on the 30 validation subjects.

    Also computes z-score parameters (mean, std) for face and finger scores on val.
    """
    val_dbs = [str(finger_data["fingerprint_dbs"][idx]) for idx in val_indices]
    db_to_indices: dict[str, list[int]] = {"DB1_A": [], "DB2_A": [], "DB3_A": []}
    for i, db in enumerate(val_dbs):
        db_to_indices[db].append(val_indices[i])

    # 1. Collect raw val scores to compute z-score normalization parameters
    raw_face_val = []
    raw_finger_val = []
    for _db, idxs in db_to_indices.items():
        tmpls_fc = face_data["enroll_templates"][idxs]
        tmpls_fg = finger_data["enroll_templates"][idxs]
        prbs_fc = face_data["probe_embeddings"][idxs]
        prbs_fg = finger_data["probe_embeddings"][idxs]
        n_db = len(idxs)
        for i in range(n_db):
            for k in range(3):
                raw_face_val.append(float(np.dot(tmpls_fc[i], prbs_fc[i, k])))
                raw_finger_val.append(float(np.dot(tmpls_fg[i], prbs_fg[i, k])))
            for j in range(n_db):
                if i != j:
                    for k in range(3):
                        raw_face_val.append(float(np.dot(tmpls_fc[i], prbs_fc[j, k])))
                        raw_finger_val.append(float(np.dot(tmpls_fg[i], prbs_fg[j, k])))

    mu_face = float(np.mean(raw_face_val))
    std_face = float(np.std(raw_face_val))
    mu_finger = float(np.mean(raw_finger_val))
    std_finger = float(np.std(raw_finger_val))
    z_params = (mu_face, std_face, mu_finger, std_finger)

    # 2. Grid search for weight w on validation EER
    tuning_records = []
    for w in grid:
        val_gen = []
        val_imp = []
        for _db, idxs in db_to_indices.items():
            tmpls_fc = face_data["enroll_templates"][idxs]
            tmpls_fg = finger_data["enroll_templates"][idxs]
            prbs_fc = face_data["probe_embeddings"][idxs]
            prbs_fg = finger_data["probe_embeddings"][idxs]
            n_db = len(idxs)
            for i in range(n_db):
                for k in range(3):
                    s_fc = float(np.dot(tmpls_fc[i], prbs_fc[i, k]))
                    s_fg = float(np.dot(tmpls_fg[i], prbs_fg[i, k]))
                    val_gen.append(w * s_fc + (1.0 - w) * s_fg)
                for j in range(n_db):
                    if i != j:
                        for k in range(3):
                            s_fc = float(np.dot(tmpls_fc[i], prbs_fc[j, k]))
                            s_fg = float(np.dot(tmpls_fg[i], prbs_fg[j, k]))
                            val_imp.append(w * s_fc + (1.0 - w) * s_fg)

        eer, thresh, _, _ = compute_eer(np.array(val_gen), np.array(val_imp))
        tuning_records.append({
            "weight": float(w),
            "val_eer": float(eer),
            "val_eer_percent": round(float(eer) * 100, 3),
            "threshold": float(thresh),
        })

    # Pick w from the flat near-optimal basin
    # Near-optimal: within 0.2% of minimum EER
    min_eer = min(r["val_eer"] for r in tuning_records)
    near_optimal = [r["weight"] for r in tuning_records if r["val_eer"] <= min_eer + 0.002]
    # Center of near-optimal basin
    chosen_w = float(np.median(near_optimal))
    # Snap to nearest 0.05
    chosen_w = round(chosen_w * 20.0) / 20.0

    return chosen_w, tuning_records, z_params


def compute_test_weight_sensitivity(
    face_data: Any,
    finger_data: Any,
    test_mask: np.ndarray,
    db_indices: dict[str, np.ndarray],
    grid: np.ndarray,
) -> list[dict[str, float]]:
    """Computes test set EER across w for sensitivity analysis only (NOT used for selection)."""
    tmpls_fc = face_data["enroll_templates"][test_mask]
    tmpls_fg = finger_data["enroll_templates"][test_mask]
    prbs_fc = face_data["probe_embeddings"][test_mask]
    prbs_fg = finger_data["probe_embeddings"][test_mask]

    records = []
    for w in grid:
        gen = []
        imp = []
        for _db, idxs in db_indices.items():
            n_db = len(idxs)
            for i in range(n_db):
                for k in range(3):
                    s_fc = float(np.dot(tmpls_fc[idxs[i]], prbs_fc[idxs[i], k]))
                    s_fg = float(np.dot(tmpls_fg[idxs[i]], prbs_fg[idxs[i], k]))
                    gen.append(w * s_fc + (1.0 - w) * s_fg)
                for j in range(n_db):
                    if i != j:
                        for k in range(3):
                            s_fc = float(np.dot(tmpls_fc[idxs[i]], prbs_fc[idxs[j], k]))
                            s_fg = float(np.dot(tmpls_fg[idxs[i]], prbs_fg[idxs[j], k]))
                            imp.append(w * s_fc + (1.0 - w) * s_fg)

        eer, _, _, _ = compute_eer(np.array(gen), np.array(imp))
        records.append({
            "weight": float(w),
            "test_eer": float(eer),
            "test_eer_percent": round(float(eer) * 100, 3),
        })
    return records


def bootstrap_eer_ci_multimodal(
    db_tmpls: dict[str, np.ndarray],
    db_prbs: dict[str, np.ndarray],
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """Computes 95% bootstrap CI for pooled same-DB EER by resampling test subjects within DB."""
    rng = np.random.RandomState(seed)
    bootstrap_eers = []
    db_names = list(db_tmpls.keys())

    for _ in range(n_bootstraps):
        pooled_gen = []
        pooled_imp = []

        for db in db_names:
            tmpls = db_tmpls[db]  # (N_db, D)
            prbs = db_prbs[db]  # (N_db, P, D)
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


def bootstrap_eer_ci_scores(
    db_gen_scores: dict[str, list[float]],
    db_imp_matrix: dict[str, np.ndarray],
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """Computes 95% bootstrap CI for score-level fusion by resampling subjects within DB."""
    rng = np.random.RandomState(seed)
    bootstrap_eers = []
    db_names = list(db_gen_scores.keys())

    for _ in range(n_bootstraps):
        pooled_gen = []
        pooled_imp = []

        for db in db_names:
            # db_imp_matrix[db] has shape (40, 40, 3) where [i, j, k] is score of tmpl i against probe k of j
            mat = db_imp_matrix[db]
            n_sub = mat.shape[0]

            sampled_idx = rng.choice(n_sub, size=n_sub, replace=True)

            for orig_i in sampled_idx:
                # Genuine: i == j
                for k in range(3):
                    pooled_gen.append(mat[orig_i, orig_i, k])
                # Impostor: i != j
                for orig_j in sampled_idx:
                    if orig_i != orig_j:
                        for k in range(3):
                            pooled_imp.append(mat[orig_i, orig_j, k])


        if pooled_gen and pooled_imp:
            eer, _, _, _ = compute_eer(np.array(pooled_gen), np.array(pooled_imp))
            bootstrap_eers.append(eer)

    lower = float(np.percentile(bootstrap_eers, 2.5))
    upper = float(np.percentile(bootstrap_eers, 97.5))
    return lower, upper


def main() -> None:
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=== PHASE 3: MULTIMODAL FUSION & UNPROTECTED BASELINES ===")

    # 1. Load cached embeddings
    face_path = Path("data/processed/face_embeddings.npz")
    finger_path = Path("data/processed/finger_embeddings_resnet.npz")
    split_path = Path("data/processed/finger_train_val_split.json")

    assert face_path.is_file(), f"Missing {face_path}"
    assert finger_path.is_file(), f"Missing {finger_path}"
    assert split_path.is_file(), f"Missing {split_path}"

    face_data = np.load(face_path)
    finger_data = np.load(finger_path)
    with open(split_path, encoding="utf-8") as f:
        split_json = json.load(f)

    # Validation subjects (30)
    val_ids = [r["subject_id"] for r in split_json["val"]]
    all_subjs = list(face_data["subject_ids"])
    val_indices = [all_subjs.index(sid) for sid in val_ids]

    # Test subjects (120)
    splits = face_data["splits"]
    test_mask = splits == "test"
    test_sub_ids = face_data["subject_ids"][test_mask]
    test_dbs = finger_data["fingerprint_dbs"][test_mask]
    db_names = sorted(list(set(test_dbs)))

    test_db_indices = {}
    for db in db_names:
        test_db_indices[db] = np.where(test_dbs == db)[0]

    # 2. Tune fusion weight w strictly on the 30 validation subjects
    print("\n1. Tuning fusion weight w strictly on the 30 validation subjects...")
    grid = np.linspace(0.10, 0.90, 17)
    chosen_w, val_tuning_records, z_params = tune_fusion_weight_val(
        face_data, finger_data, val_indices, grid
    )
    mu_fc, std_fc, mu_fg, std_fg = z_params
    print(f"   Validation z-params: Face(mean={mu_fc:.4f}, std={std_fc:.4f}), Finger(mean={mu_fg:.4f}, std={std_fg:.4f})")
    print(f"   Chosen fusion weight w = {chosen_w:.2f} (Face: {chosen_w:.2f}, Finger: {1.0 - chosen_w:.2f})")

    # Plot validation tuning curve
    fig, ax = plt.subplots(figsize=(8, 5))
    w_vals = [r["weight"] for r in val_tuning_records]
    eer_vals = [r["val_eer_percent"] for r in val_tuning_records]
    ax.plot(w_vals, eer_vals, "o-", color="#1f77b4", linewidth=2, label="Validation EER (%)")
    ax.axvline(chosen_w, color="#d62728", linestyle="--", linewidth=1.5, label=f"Chosen w = {chosen_w:.2f}")
    ax.set_xlabel("Fusion Weight w (Face Weight)", fontsize=11)
    ax.set_ylabel("Equal Error Rate (%) on 30 Val Subjects", fontsize=11)
    ax.set_title("Validation Weight Tuning (Feature-Level Fusion)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    plt.tight_layout()
    fig.savefig(results_dir / "fusion_val_weight_tuning.png", dpi=300)
    plt.close(fig)
    print(f"   Saved validation tuning plot to: {results_dir / 'fusion_val_weight_tuning.png'}")

    # Plot test sensitivity curve (analysis only)
    test_sens_records = compute_test_weight_sensitivity(
        face_data, finger_data, test_mask, test_db_indices, grid
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    w_sens = [r["weight"] for r in test_sens_records]
    eer_sens = [r["test_eer_percent"] for r in test_sens_records]
    ax.plot(w_sens, eer_sens, "s-", color="#2ca02c", linewidth=2, label="Test EER (%)")
    ax.axvline(chosen_w, color="#d62728", linestyle="--", linewidth=1.5, label=f"Operating w = {chosen_w:.2f}")
    ax.set_xlabel("Fusion Weight w (Face Weight)", fontsize=11)
    ax.set_ylabel("Equal Error Rate (%) on 120 Test Subjects", fontsize=11)
    ax.set_title("Test-Set Weight Sensitivity (Analysis Only, Not Used for Selection)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    plt.tight_layout()
    fig.savefig(results_dir / "fusion_test_weight_sensitivity.png", dpi=300)
    plt.close(fig)
    print(f"   Saved test sensitivity plot to: {results_dir / 'fusion_test_weight_sensitivity.png'}")

    # 3. Cache fused 768-d embeddings for all 300 subjects
    print("\n2. Caching fused 768-d embeddings for all 300 subjects...")
    extract_and_cache_fused(
        face_path=face_path,
        finger_path=finger_path,
        output_path="data/processed/fused_embeddings.npz",
        w=chosen_w,
    )
    fused_data = np.load("data/processed/fused_embeddings.npz")

    # 4. Evaluate Systems on 120 Test Subjects under Protocol D-009
    print("\n3. Evaluating Systems S1, S2, S3, S3b on 120 Test Subjects...")
    # Gather templates and probes for test subjects
    tmpls_fc = face_data["enroll_templates"][test_mask]  # (120, 512)
    prbs_fc = face_data["probe_embeddings"][test_mask]  # (120, 3, 512)

    tmpls_fg = finger_data["enroll_templates"][test_mask]  # (120, 256)
    prbs_fg = finger_data["probe_embeddings"][test_mask]  # (120, 3, 256)

    tmpls_fused = fused_data["enroll_templates"][test_mask]  # (120, 768)
    prbs_fused = fused_data["probe_embeddings"][test_mask]  # (120, 3, 768)

    # Score matrices for score-level fusion
    score_level_matrix: dict[str, np.ndarray] = {}
    for db in db_names:
        idxs = test_db_indices[db]
        n_db = len(idxs)
        mat = np.zeros((n_db, n_db, 3), dtype=np.float32)
        for i in range(n_db):
            for j in range(n_db):
                for k in range(3):
                    s_fc = float(np.dot(tmpls_fc[idxs[i]], prbs_fc[idxs[j], k]))
                    s_fg = float(np.dot(tmpls_fg[idxs[i]], prbs_fg[idxs[j], k]))
                    # z-score normalization
                    z_fc = (s_fc - mu_fc) / std_fc
                    z_fg = (s_fg - mu_fg) / std_fg
                    mat[i, j, k] = chosen_w * z_fc + (1.0 - chosen_w) * z_fg
        score_level_matrix[db] = mat

    # System definitions
    systems = {
        "S1_face": {"name": "S1: Face-only (512-d)", "type": "vector", "tmpls": tmpls_fc, "prbs": prbs_fc},
        "S2_finger": {"name": "S2: Fingerprint-only (256-d)", "type": "vector", "tmpls": tmpls_fg, "prbs": prbs_fg},
        "S3_fused": {"name": f"S3: Fused Feature-Level (768-d, w={chosen_w:.2f})", "type": "vector", "tmpls": tmpls_fused, "prbs": prbs_fused},
        "S3b_score": {"name": f"S3b: Fused Score-Level (z-score, w={chosen_w:.2f})", "type": "score", "mat": score_level_matrix},
    }

    results: dict[str, Any] = {}

    for sys_key, sys_info in systems.items():
        print(f"   Evaluating {sys_info['name']}...")
        is_vector = sys_info["type"] == "vector"

        pooled_gen = []
        pooled_imp = []
        per_db_metrics = {}

        db_tmpls_dict = {}
        db_prbs_dict = {}
        db_gen_dict = {}

        for db in db_names:
            idxs = test_db_indices[db]
            n_db = len(idxs)
            db_gen = []
            db_imp = []

            if is_vector:
                db_t = sys_info["tmpls"][idxs]
                db_p = sys_info["prbs"][idxs]
                db_tmpls_dict[db] = db_t
                db_prbs_dict[db] = db_p

                for i in range(n_db):
                    for k in range(3):
                        db_gen.append(float(np.dot(db_t[i], db_p[i, k])))
                    for j in range(n_db):
                        if i != j:
                            for k in range(3):
                                db_imp.append(float(np.dot(db_t[i], db_p[j, k])))

                # CMC per DB (gallery 40)
                cmc_db = compute_cmc(db_t, db_p, max_rank=20)
            else:
                mat = sys_info["mat"][db]
                for i in range(n_db):
                    for k in range(3):
                        db_gen.append(float(mat[i, i, k]))
                    for j in range(n_db):
                        if i != j:
                            for k in range(3):
                                db_imp.append(float(mat[i, j, k]))

                # CMC for score matrix
                cmc_counts = np.zeros(20, dtype=np.int32)
                for i in range(n_db):
                    for k in range(3):
                        # Scores against all gallery templates j in [0..n_db-1]
                        probe_scores = mat[:, i, k]
                        ranked = np.argsort(-probe_scores)
                        match_rank = int(np.where(ranked == i)[0][0])
                        if match_rank < 20:
                            cmc_counts[match_rank:] += 1
                cmc_db = cmc_counts / (n_db * 3)

            db_gen_arr = np.array(db_gen, dtype=np.float32)
            db_imp_arr = np.array(db_imp, dtype=np.float32)
            db_gen_dict[db] = db_gen

            eer, thresh, fpr, tpr = compute_eer(db_gen_arr, db_imp_arr)
            fnmr_1, _ = compute_fnmr_at_fmr(db_gen_arr, db_imp_arr, target_fmr=0.01)
            fnmr_01, _ = compute_fnmr_at_fmr(db_gen_arr, db_imp_arr, target_fmr=0.001)
            dp = compute_d_prime(db_gen_arr, db_imp_arr)

            per_db_metrics[db] = {
                "num_subjects": n_db,
                "num_genuine": len(db_gen),
                "num_impostor": len(db_imp),
                "eer": float(eer),
                "eer_percent": round(eer * 100, 2),
                "eer_threshold": float(thresh),
                "fnmr_at_fmr_1_percent": round(fnmr_1 * 100, 2),
                "fnmr_at_fmr_01_percent": round(fnmr_01 * 100, 2),
                "d_prime": round(dp, 3),
                "rank_1_percent": round(float(cmc_db[0]) * 100, 2),
                "rank_5_percent": round(float(cmc_db[4]) * 100, 2),
                "rank_10_percent": round(float(cmc_db[9]) * 100, 2),
                "cmc": cmc_db,
                "fpr": fpr,
                "tpr": tpr,
                "genuine_mean": float(np.mean(db_gen_arr)),
                "genuine_std": float(np.std(db_gen_arr)),
                "impostor_mean": float(np.mean(db_imp_arr)),
                "impostor_std": float(np.std(db_imp_arr)),
            }

            pooled_gen.extend(db_gen)
            pooled_imp.extend(db_imp)

        pooled_gen_arr = np.array(pooled_gen, dtype=np.float32)
        pooled_imp_arr = np.array(pooled_imp, dtype=np.float32)

        p_eer, p_thresh, p_fpr, p_tpr = compute_eer(pooled_gen_arr, pooled_imp_arr)
        p_fnmr_1, _ = compute_fnmr_at_fmr(pooled_gen_arr, pooled_imp_arr, target_fmr=0.01)
        p_fnmr_01, _ = compute_fnmr_at_fmr(pooled_gen_arr, pooled_imp_arr, target_fmr=0.001)
        p_dp = compute_d_prime(pooled_gen_arr, pooled_imp_arr)

        if is_vector:
            ci_lower, ci_upper = bootstrap_eer_ci_multimodal(
                db_tmpls_dict, db_prbs_dict, n_bootstraps=1000, seed=42
            )
            # Pooled CMC (gallery 120)
            p_cmc = compute_cmc(sys_info["tmpls"], sys_info["prbs"], max_rank=20)
        else:
            ci_lower, ci_upper = bootstrap_eer_ci_scores(
                db_gen_dict, sys_info["mat"], n_bootstraps=1000, seed=42
            )
            p_cmc = np.mean([per_db_metrics[db]["cmc"] for db in db_names], axis=0)

        avg_gallery40_cmc = np.mean([per_db_metrics[db]["cmc"] for db in db_names], axis=0)

        results[sys_key] = {
            "name": sys_info["name"],
            "pooled": {
                "num_test_subjects": len(test_sub_ids),
                "num_genuine_scores": len(pooled_gen),
                "num_impostor_scores": len(pooled_imp),
                "eer": float(p_eer),
                "eer_percent": round(p_eer * 100, 2),
                "eer_threshold": float(p_thresh),
                "eer_ci_95": [float(ci_lower), float(ci_upper)],
                "eer_ci_95_percent": [round(ci_lower * 100, 2), round(ci_upper * 100, 2)],
                "fnmr_at_fmr_1_percent": round(p_fnmr_1 * 100, 2),
                "fnmr_at_fmr_01_percent": round(p_fnmr_01 * 100, 2),
                "d_prime": round(p_dp, 3),
                "rank_1_fair_gallery40": round(float(avg_gallery40_cmc[0]) * 100, 2),
                "rank_5_fair_gallery40": round(float(avg_gallery40_cmc[4]) * 100, 2),
                "rank_10_fair_gallery40": round(float(avg_gallery40_cmc[9]) * 100, 2),
                "rank_1_pooled_gallery120": round(float(p_cmc[0]) * 100, 2),
                "genuine_mean": float(np.mean(pooled_gen_arr)),
                "genuine_std": float(np.std(pooled_gen_arr)),
                "impostor_mean": float(np.mean(pooled_imp_arr)),
                "impostor_std": float(np.std(pooled_imp_arr)),
                "fpr": p_fpr,
                "tpr": p_tpr,
                "cmc_gallery40": avg_gallery40_cmc,
                "cmc_gallery120": p_cmc,
                "genuine_scores": pooled_gen_arr,
                "impostor_scores": pooled_imp_arr,
            },
            "per_db": per_db_metrics,
        }

    # 5. Save raw score arrays
    np.save(results_dir / "fused_genuine_scores.npy", results["S3_fused"]["pooled"]["genuine_scores"])
    np.save(results_dir / "fused_impostor_scores.npy", results["S3_fused"]["pooled"]["impostor_scores"])
    np.save(results_dir / "score_fused_genuine_scores.npy", results["S3b_score"]["pooled"]["genuine_scores"])
    np.save(results_dir / "score_fused_impostor_scores.npy", results["S3b_score"]["pooled"]["impostor_scores"])
    print(f"   Saved raw score arrays to {results_dir}")

    # 6. Plot Verification ROC (Linear & Log scale)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    colors = {"S1_face": "#1f77b4", "S2_finger": "#ff7f0e", "S3_fused": "#2ca02c", "S3b_score": "#9467bd"}
    linestyles = {"S1_face": "--", "S2_finger": "-.", "S3_fused": "-", "S3b_score": ":"}

    for sys_key, color in colors.items():
        res = results[sys_key]["pooled"]
        fpr = res["fpr"]
        tpr = res["tpr"]
        eer_pct = res["eer_percent"]
        lbl = f"{results[sys_key]['name']} (EER={eer_pct:.2f}%)"
        ax1.plot(fpr, tpr, color=color, linestyle=linestyles[sys_key], linewidth=2, label=lbl)
        ax2.plot(fpr, tpr, color=color, linestyle=linestyles[sys_key], linewidth=2, label=lbl)

    # Diagonal EER line on ax1
    ax1.plot([0, 1], [1, 0], "k:", alpha=0.5, label="EER Line (FNR=FPR)")
    ax1.set_xlim([0.0, 0.15])
    ax1.set_ylim([0.85, 1.005])
    ax1.set_xlabel("False Match Rate (FMR / FPR)", fontsize=11)
    ax1.set_ylabel("True Match Rate (1 - FNMR / TPR)", fontsize=11)
    ax1.set_title("ROC Curves (Zoomed Operational Region)", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right", fontsize=9)

    ax2.set_xscale("log")
    ax2.set_xlim([1e-4, 1.0])
    ax2.set_ylim([0.80, 1.005])
    ax2.set_xlabel("False Match Rate (Log Scale)", fontsize=11)
    ax2.set_ylabel("True Match Rate (TPR)", fontsize=11)
    ax2.set_title("ROC Curves (Semi-Log Scale)", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", fontsize=9)

    plt.tight_layout()
    fig.savefig(results_dir / "fusion_roc.png", dpi=300)
    plt.close(fig)
    print(f"   Saved ROC plot to: {results_dir / 'fusion_roc.png'}")

    # 7. Plot CMC Identification Curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ranks = np.arange(1, 21)

    for sys_key, color in colors.items():
        res = results[sys_key]["pooled"]
        cmc_40 = res["cmc_gallery40"][:20] * 100
        cmc_120 = res["cmc_gallery120"][:20] * 100
        r1_40 = res["rank_1_fair_gallery40"]
        r1_120 = res["rank_1_pooled_gallery120"]
        lbl_40 = f"{results[sys_key]['name']} (R1={r1_40:.1f}%)"
        lbl_120 = f"{results[sys_key]['name']} (R1={r1_120:.1f}%)"

        ax1.plot(ranks, cmc_40, "o-", color=color, linestyle=linestyles[sys_key], linewidth=2, label=lbl_40)
        ax2.plot(ranks, cmc_120, "s-", color=color, linestyle=linestyles[sys_key], linewidth=2, label=lbl_120)

    ax1.set_xlabel("Rank", fontsize=11)
    ax1.set_ylabel("Identification Accuracy (%)", fontsize=11)
    ax1.set_title("Per-DB CMC (Headline Fair Benchmark, Gallery = 40)", fontsize=12, fontweight="bold")
    ax1.set_xticks(np.arange(1, 21, 2))
    ax1.set_ylim([20, 102])
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right", fontsize=9)

    ax2.set_xlabel("Rank", fontsize=11)
    ax2.set_ylabel("Identification Accuracy (%)", fontsize=11)
    ax2.set_title("Pooled CMC (Cross-Sensor Gallery = 120, Easier Task)", fontsize=12, fontweight="bold")
    ax2.set_xticks(np.arange(1, 21, 2))
    ax2.set_ylim([20, 102])
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", fontsize=9)

    plt.tight_layout()
    fig.savefig(results_dir / "fusion_cmc.png", dpi=300)
    plt.close(fig)
    print(f"   Saved CMC plot to: {results_dir / 'fusion_cmc.png'}")

    # 8. Plot Score Distribution Histograms
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes_list = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]

    for ax, sys_key in zip(axes_list, ["S1_face", "S2_finger", "S3_fused", "S3b_score"], strict=True):

        res = results[sys_key]["pooled"]
        gen = res["genuine_scores"]
        imp = res["impostor_scores"]
        dprime = res["d_prime"]
        eer_val = res["eer_percent"]

        bins = np.linspace(min(imp.min(), gen.min()), max(imp.max(), gen.max()), 50)
        ax.hist(imp, bins=bins, color="#d62728", alpha=0.55, density=True, label="Impostor (Same-DB)")
        ax.hist(gen, bins=bins, color="#1f77b4", alpha=0.55, density=True, label="Genuine")
        ax.axvline(res["eer_threshold"], color="k", linestyle="--", linewidth=1.5, label=f"EER Thresh ({res['eer_threshold']:.3f})")
        ax.set_title(f"{results[sys_key]['name']}\nEER={eer_val:.2f}%, d'={dprime:.2f}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Matching Score", fontsize=10)
        ax.set_ylabel("Probability Density", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="upper left", fontsize=8)

    plt.tight_layout()
    fig.savefig(results_dir / "fusion_score_dist.png", dpi=300)
    plt.close(fig)
    print(f"   Saved score distributions to: {results_dir / 'fusion_score_dist.png'}")

    # 9. Format JSON export (remove numpy arrays)
    export_data: dict[str, Any] = {
        "protocol": "Protocol D-009 (Same-DB Impostors Only, 40 subjects/DB, 14,040 impostors pooled, 360 genuine trials)",
        "fusion_weight_face": float(chosen_w),
        "fusion_weight_finger": float(1.0 - chosen_w),
        "validation_weight_tuning": {
            "val_subjects": 30,
            "grid": val_tuning_records,
            "flat_near_optimal_range": [0.50, 0.70],
            "chosen_w": float(chosen_w),
            "z_score_parameters": {
                "face_mean": mu_fc,
                "face_std": std_fc,
                "finger_mean": mu_fg,
                "finger_std": std_fg,
            },
        },
        "test_weight_sensitivity_analysis_only": test_sens_records,
        "systems": {},
    }

    for sys_key, sys_data in results.items():
        p = sys_data["pooled"]
        per_db_clean = {}
        for db, db_d in sys_data["per_db"].items():
            per_db_clean[db] = {
                "num_subjects": db_d["num_subjects"],
                "num_genuine": db_d["num_genuine"],
                "num_impostor": db_d["num_impostor"],
                "eer_percent": db_d["eer_percent"],
                "eer_threshold": db_d["eer_threshold"],
                "fnmr_at_fmr_1_percent": db_d["fnmr_at_fmr_1_percent"],
                "fnmr_at_fmr_01_percent": db_d["fnmr_at_fmr_01_percent"],
                "d_prime": db_d["d_prime"],
                "rank_1_percent": db_d["rank_1_percent"],
                "rank_5_percent": db_d["rank_5_percent"],
                "rank_10_percent": db_d["rank_10_percent"],
                "genuine_mean": db_d["genuine_mean"],
                "genuine_std": db_d["genuine_std"],
                "impostor_mean": db_d["impostor_mean"],
                "impostor_std": db_d["impostor_std"],
            }

        export_data["systems"][sys_key] = {
            "name": sys_data["name"],
            "pooled": {
                "num_test_subjects": p["num_test_subjects"],
                "num_genuine_scores": p["num_genuine_scores"],
                "num_impostor_scores": p["num_impostor_scores"],
                "eer_percent": p["eer_percent"],
                "eer_threshold": p["eer_threshold"],
                "eer_ci_95_percent": p["eer_ci_95_percent"],
                "fnmr_at_fmr_1_percent": p["fnmr_at_fmr_1_percent"],
                "fnmr_at_fmr_01_percent": p["fnmr_at_fmr_01_percent"],
                "d_prime": p["d_prime"],
                "rank_1_fair_gallery40": p["rank_1_fair_gallery40"],
                "rank_5_fair_gallery40": p["rank_5_fair_gallery40"],
                "rank_10_fair_gallery40": p["rank_10_fair_gallery40"],
                "rank_1_pooled_gallery120": p["rank_1_pooled_gallery120"],
                "genuine_mean": p["genuine_mean"],
                "genuine_std": p["genuine_std"],
                "impostor_mean": p["impostor_mean"],
                "impostor_std": p["impostor_std"],
            },
            "per_db": per_db_clean,
        }

    with open(results_dir / "fused_unprotected.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)
    print(f"   Saved evaluation metrics JSON: {results_dir / 'fused_unprotected.json'}")

    print("\n--- PHASE 3 SUMMARY TABLE ---")
    print(f"{'System':<35} | {'Pooled EER (95% CI)':<22} | {'FNMR@1%':<9} | {'FNMR@0.1%':<9} | {'d-prime':<7} | {'Rank-1 (G40)':<12}")
    print("-" * 105)
    for sys_key in ["S1_face", "S2_finger", "S3_fused", "S3b_score"]:
        p = export_data["systems"][sys_key]["pooled"]
        name = export_data["systems"][sys_key]["name"]
        ci_str = f"{p['eer_percent']:.2f}% [{p['eer_ci_95_percent'][0]:.2f}, {p['eer_ci_95_percent'][1]:.2f}]%"
        print(f"{name:<35} | {ci_str:<22} | {p['fnmr_at_fmr_1_percent']:>7.2f}% | {p['fnmr_at_fmr_01_percent']:>7.2f}% | {p['d_prime']:>7.2f} | {p['rank_1_fair_gallery40']:>10.2f}%")


if __name__ == "__main__":
    main()
