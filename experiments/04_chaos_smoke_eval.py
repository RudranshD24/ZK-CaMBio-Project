"""experiments/04_chaos_smoke_eval.py
Phase 4 smoke evaluation of C++ Chaos Engine on the 30 VALIDATION subjects
and property checks on the 300 subjects.

IMPORTANT: Does NOT touch the 120 test subjects (strictly reserved for Phase 5).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chaoshash
import matplotlib.pyplot as plt
import numpy as np
from src.chaos.engine import derive_chaos_parameters, quantize_vector
from src.fusion.fuse import compute_eer


def run_property_check(
    enroll_templates: np.ndarray,
    mean_vec: np.ndarray,
    output_path: Path,
) -> dict:
    """Property check on all 300 subjects:
    Normalized Hamming distance vs angle (theta / pi) between original vectors
    for m in {64, 128, 256, 512, 768}.
    """
    print("\n--- Property Check: Hamming Distance vs Angle (theta / pi) ---")
    n_subjs = len(enroll_templates)
    rng = np.random.RandomState(42)

    # Sample 5,000 random subject pairs among the 300 subjects
    pairs = []
    for _ in range(5000):
        i = rng.randint(0, n_subjs)
        j = rng.randint(0, n_subjs)
        while i == j:
            j = rng.randint(0, n_subjs)
        pairs.append((i, j))

    # Compute cosine similarities and angles
    u_list = [enroll_templates[i] for i, _ in pairs]
    v_list = [enroll_templates[j] for _, j in pairs]

    # Angles theta in [0, pi]
    cos_sims = [
        float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)))
        for u, v in zip(u_list, v_list, strict=True)
    ]
    cos_sims = np.clip(cos_sims, -1.0, 1.0)
    thetas_over_pi = np.arccos(cos_sims) / np.pi

    # Fixed key for property check
    master_key = b"\x5a" * 32
    state, r_param = derive_chaos_parameters(master_key, "property_check", 1)

    m_values = [64, 128, 256, 512, 768]
    hd_results = {}

    plt.figure(figsize=(10, 7))
    plt.plot([0, 1], [0, 1], "k--", label=r"Ideal $\mathbb{E}[HD] = \theta / \pi$", linewidth=2)

    # Pre-quantize all 300 enroll vectors
    enroll_q = [quantize_vector(u, mean_vec) for u in enroll_templates]

    for m in m_values:
        # Precompute templates for the 300 subjects once
        templates_m = [chaoshash.transform(u_q, state, r_param, m) for u_q in enroll_q]
        hds = [chaoshash.hamming(templates_m[i], templates_m[j], m) for i, j in pairs]

        hds = np.array(hds)
        # Compute mean curve across angle bins
        bins = np.linspace(0.1, 0.9, 17)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        binned_hd = []
        for b_low, b_high in zip(bins[:-1], bins[1:], strict=True):
            mask = (thetas_over_pi >= b_low) & (thetas_over_pi < b_high)
            if np.sum(mask) > 0:
                binned_hd.append(float(np.mean(hds[mask])))
            else:
                binned_hd.append(np.nan)

        corr = float(np.corrcoef(thetas_over_pi, hds)[0, 1])
        hd_results[f"m_{m}"] = {
            "pearson_r": corr,
            "mean_hd": float(np.mean(hds)),
            "std_hd": float(np.std(hds)),
        }
        plt.plot(bin_centers, binned_hd, marker="o", label=f"m = {m} (r = {corr:.3f})")

    plt.xlabel(r"Normalized Angle $\theta / \pi$ (from original fused vectors)", fontsize=12)
    plt.ylabel("Normalized Hamming Distance (chaotic templates)", fontsize=12)
    plt.title(r"Chaotic Random Projection Metric Preservation ($HD \approx \theta / \pi$)", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved property check plot to {output_path}")

    return hd_results


def run_scenario_k_val(
    fused_data: dict,
    val_indices: list[int],
    val_dbs: list[str],
    mean_vec: np.ndarray,
    output_hist_path: Path,
) -> dict:
    """Scenario K (known key, headline worst-case) on the 30 validation subjects
    with m=512 across 10 random keys.
    """
    print("\n--- Scenario K on 30 Validation Subjects (m=512, 10 keys) ---")
    val_enroll = fused_data["enroll_templates"][val_indices]  # (30, 768)
    val_probes = fused_data["probe_embeddings"][val_indices]  # (30, 3, 768)

    # Stratify by DB
    unique_dbs = sorted(list(set(val_dbs)))
    db_to_indices = {db: [i for i, d in enumerate(val_dbs) if d == db] for db in unique_dbs}

    # Pre-quantize validation embeddings
    val_enroll_q = [quantize_vector(v, mean_vec) for v in val_enroll]
    val_probes_q = [[quantize_vector(p, mean_vec) for p in val_probes[i]] for i in range(len(val_indices))]

    key_eers = []
    all_gen_scores = []
    all_imp_scores = []

    m = 512
    rng = np.random.RandomState(42)

    for k_idx in range(10):
        key = rng.bytes(32)
        state, r_param = derive_chaos_parameters(key, "scenario_k_val", k_idx)

        # Transform enroll and probe templates
        enroll_bits = [chaoshash.transform(v_q, state, r_param, m) for v_q in val_enroll_q]
        probe_bits = [
            [chaoshash.transform(p_q, state, r_param, m) for p_q in val_probes_q[i]]
            for i in range(len(val_indices))
        ]

        # Genuine scores (smaller Hamming distance = more genuine)
        # For compute_eer, higher score = more genuine, so score = 1.0 - HD
        gen_scores = []
        for i in range(len(val_indices)):
            for p_bit in probe_bits[i]:
                hd = chaoshash.hamming(enroll_bits[i], p_bit, m)
                gen_scores.append(1.0 - hd)
                if k_idx == 0:
                    all_gen_scores.append(hd)

        # Impostor scores (same-DB only)
        imp_scores = []
        for _db, indices in db_to_indices.items():
            for _i_idx, i in enumerate(indices):
                for _j_idx, j in enumerate(indices):
                    if i == j:
                        continue
                    # Match subject i's enroll with subject j's probes
                    for p_bit in probe_bits[j]:
                        hd = chaoshash.hamming(enroll_bits[i], p_bit, m)
                        imp_scores.append(1.0 - hd)
                        if k_idx == 0:
                            all_imp_scores.append(hd)

        eer, eer_thresh, _, _ = compute_eer(np.array(gen_scores), np.array(imp_scores))
        key_eers.append(eer)
        print(f"  Key {k_idx + 1:2d}/10: Val EER = {eer * 100:.3f}% (HD threshold = {1.0 - eer_thresh:.4f})")

    mean_eer = float(np.mean(key_eers))
    std_eer = float(np.std(key_eers))
    print(f"\nScenario K Val EER (m=512, 10 keys): {mean_eer * 100:.3f}% +/- {std_eer * 100:.3f}%")

    # Plot genuine vs impostor Hamming distance histogram for representative key
    plt.figure(figsize=(9, 5))
    plt.hist(all_gen_scores, bins=30, alpha=0.7, color="#2b5c8f", density=True, label="Genuine Pairs (same key)")
    plt.hist(all_imp_scores, bins=40, alpha=0.7, color="#c0392b", density=True, label="Impostor Pairs (same key, same-DB)")
    plt.axvline(1.0 - eer_thresh, color="black", linestyle="--", linewidth=1.5, label=f"EER Decision Threshold ({1.0 - eer_thresh:.3f})")
    plt.xlabel("Normalized Hamming Distance", fontsize=12)
    plt.ylabel("Density", fontsize=12)
    plt.title("Scenario K (Known Key) Score Distribution on 30 Validation Subjects (m=512)", fontsize=13)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_hist_path, dpi=300)
    plt.close()
    print(f"Saved Scenario K histogram to {output_hist_path}")

    return {
        "m": m,
        "n_keys": 10,
        "val_subjects": len(val_indices),
        "genuine_trials_per_key": len(gen_scores),
        "impostor_trials_per_key": len(imp_scores),
        "key_eers": [float(e) for e in key_eers],
        "mean_eer": mean_eer,
        "std_eer": std_eer,
        "mean_eer_percent": mean_eer * 100.0,
        "std_eer_percent": std_eer * 100.0,
    }


def benchmark_transform_timing(mean_vec: np.ndarray, d: int = 768, m: int = 512, n_runs: int = 1000) -> float:
    """Measures average timing per transform in milliseconds for d=768, m=512."""
    print(f"\n--- Timing Benchmark: {n_runs} Transforms (d={d}, m={m}) ---")
    rng = np.random.RandomState(42)
    vec = rng.randn(d).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    x_q = quantize_vector(vec, mean_vec)

    master_key = b"T" * 32
    state, r_param = derive_chaos_parameters(master_key, "timing_bench", 1)

    # Warmup
    for _ in range(50):
        chaoshash.transform(x_q, state, r_param, m)

    t0 = time.perf_counter()
    for _ in range(n_runs):
        chaoshash.transform(x_q, state, r_param, m)
    t1 = time.perf_counter()

    total_time_ms = (t1 - t0) * 1000.0
    ms_per_transform = total_time_ms / n_runs
    print(f"Total time for {n_runs} transforms: {total_time_ms:.2f} ms")
    print(f"Timing per transform: {ms_per_transform:.4f} ms")
    return ms_per_transform


def main() -> None:
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    fused_path = Path("data/processed/fused_embeddings.npz")
    split_path = Path("data/processed/finger_train_val_split.json")
    mean_path = Path("data/processed/chaos_mean_vector.npy")

    assert fused_path.is_file(), f"Missing {fused_path}"
    assert split_path.is_file(), f"Missing {split_path}"
    assert mean_path.is_file(), f"Missing {mean_path}"

    fused_data = np.load(fused_path)
    mean_vec = np.load(mean_path)

    with open(split_path, encoding="utf-8") as f:
        split_json = json.load(f)

    # Extract validation subjects
    val_ids = [r["subject_id"] for r in split_json["val"]]
    val_dbs = [r["fingerprint_db"] for r in split_json["val"]]
    all_subjs = list(fused_data["subject_ids"])
    val_indices = [all_subjs.index(sid) for sid in val_ids]

    # 2. Property check on all 300 subjects: HD vs angle
    hd_vs_angle_plot = results_dir / "chaos_hd_vs_angle.png"
    property_results = run_property_check(
        fused_data["enroll_templates"],
        mean_vec,
        hd_vs_angle_plot,
    )

    # 3. Scenario K on the 30 validation subjects
    val_hist_plot = results_dir / "chaos_val_hamming_hist.png"
    scenario_k_results = run_scenario_k_val(
        fused_data,
        val_indices,
        val_dbs,
        mean_vec,
        val_hist_plot,
    )

    # 4. Benchmark transform timing
    ms_per_transform = benchmark_transform_timing(mean_vec, d=768, m=512, n_runs=1000)

    # 5. Save all smoke results
    smoke_summary = {
        "phase": 4,
        "description": "Smoke evaluation of C++ Chaos Engine on 30 validation subjects and property checks",
        "timing_ms_per_transform": ms_per_transform,
        "timing_throughput_transforms_per_sec": 1000.0 / ms_per_transform,
        "property_check": property_results,
        "scenario_k_validation": scenario_k_results,
        "unprotected_val_eer_at_w06": 0.0,
    }

    out_json = results_dir / "chaos_val_smoke.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(smoke_summary, f, indent=2)
    print(f"\nSaved smoke evaluation results to {out_json}")


if __name__ == "__main__":
    main()
