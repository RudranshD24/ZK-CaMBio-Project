"""experiments/02_run_val_experiments.py

Runs all validation experiments on the 30 validation fingers (NEVER touching test):
1. Baseline A (Gabor) with Preprocessing V1
2. Baseline A (Gabor) with Preprocessing V2
3. Baseline B (ResNet18, 150 fit fingers) with Preprocessing V1
4. Baseline B (ResNet18, 150 fit fingers) with Preprocessing V2
5. Baseline B (ResNet18, 150 fit + 140 extra fingers) with Preprocessing V2

Saves results to results/finger_val_experiments.json and selects the winning configuration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

try:
    from src.data.finger_loader import FingerprintLoader
    from src.finger.gabor import GaborFeatureExtractor
    from src.finger.preprocess import preprocess_fingerprint
    from src.finger.train_resnet import compute_val_eer, train_finger_resnet18
except ImportError:
    from data.finger_loader import FingerprintLoader
    from finger.gabor import GaborFeatureExtractor
    from finger.preprocess import preprocess_fingerprint
    from finger.train_resnet import compute_val_eer, train_finger_resnet18


def evaluate_gabor_val(val_records: list[dict], loader: FingerprintLoader, variant: str) -> dict:
    extractor = GaborFeatureExtractor()
    templates = []
    probes_list = []

    for rec in val_records:
        db = rec["fingerprint_db"]
        enr_feats = []
        for fn in rec["fingerprint_enroll_files"]:
            raw = loader.load_by_filename(db, fn)
            proc = preprocess_fingerprint(raw, db_hint=db, variant=variant)
            enr_feats.append(extractor.extract(proc))
        tmpl = np.mean(enr_feats, axis=0)
        tmpl = tmpl / np.linalg.norm(tmpl)
        templates.append(tmpl)

        prb_feats = []
        for fn in rec["fingerprint_probe_files"]:
            raw = loader.load_by_filename(db, fn)
            proc = preprocess_fingerprint(raw, db_hint=db, variant=variant)
            prb_feats.append(extractor.extract(proc))
        probes_list.append(np.array(prb_feats))

    db_indices = {"DB1_A": [], "DB2_A": [], "DB3_A": []}
    for idx, rec in enumerate(val_records):
        db_indices[rec["fingerprint_db"]].append(idx)

    gen_scores = []
    imp_scores = []
    for _db, idxs in db_indices.items():
        for i in idxs:
            for k in range(3):
                gen_scores.append(float(np.dot(templates[i], probes_list[i][k])))
            for j in idxs:
                if i != j:
                    for k in range(3):
                        imp_scores.append(float(np.dot(templates[i], probes_list[j][k])))

    gen_arr = np.array(gen_scores, dtype=np.float32)
    imp_arr = np.array(imp_scores, dtype=np.float32)
    sep = float(np.mean(gen_arr) - np.mean(imp_arr))
    eer = compute_val_eer(gen_arr, imp_arr)

    return {
        "model": "Gabor (256-d)",
        "variant": variant,
        "use_extra_data": False,
        "val_separation": float(sep),
        "val_eer": float(eer),
        "val_eer_percent": round(eer * 100, 2),
        "genuine_mean": float(np.mean(gen_arr)),
        "impostor_mean": float(np.mean(imp_arr)),
    }


def main() -> None:
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    with open("data/processed/finger_train_val_split.json", encoding="utf-8") as f:
        split_data = json.load(f)
    val_records = split_data["val"]
    loader = FingerprintLoader()

    print("=== VALIDATION EXPERIMENTS (30 VAL FINGERS ONLY) ===")

    # 1. Gabor V1 vs V2
    print("\n1. Evaluating Gabor on Val (V1)...")
    gabor_v1 = evaluate_gabor_val(val_records, loader, variant="v1")
    print(f"   Gabor V1: Val Sep = {gabor_v1['val_separation']:.4f}, Val EER = {gabor_v1['val_eer_percent']}%")

    print("\n2. Evaluating Gabor on Val (V2)...")
    gabor_v2 = evaluate_gabor_val(val_records, loader, variant="v2")
    print(f"   Gabor V2: Val Sep = {gabor_v2['val_separation']:.4f}, Val EER = {gabor_v2['val_eer_percent']}%")

    # 2. ResNet18 V1 (150 fit fingers)
    print("\n3. Training ResNet18 on Val (V1, 150 fit fingers)...")
    resnet_v1 = train_finger_resnet18(
        checkpoint_path="data/processed/finger_resnet18_v1.pth",
        variant="v1",
        use_extra_data=False,
        epochs=6,
        batch_size=32,
    )

    # 3. ResNet18 V2 (150 fit fingers)
    print("\n4. Training ResNet18 on Val (V2, 150 fit fingers)...")
    resnet_v2 = train_finger_resnet18(
        checkpoint_path="data/processed/finger_resnet18_v2.pth",
        variant="v2",
        use_extra_data=False,
        epochs=6,
        batch_size=32,
    )

    # 4. ResNet18 V2 + Extra Data (150 fit + 140 extra = 290 fingers)
    print("\n5. Training ResNet18 on Val (V2 + Extra Data: 290 fingers)...")
    resnet_v2_extra = train_finger_resnet18(
        checkpoint_path="data/processed/finger_resnet18_v2_extra.pth",
        variant="v2",
        use_extra_data=True,
        epochs=6,
        batch_size=32,
    )

    experiments = {
        "gabor_v1": gabor_v1,
        "gabor_v2": gabor_v2,
        "resnet_v1": resnet_v1,
        "resnet_v2": resnet_v2,
        "resnet_v2_extra": resnet_v2_extra,
    }

    # Determine winner based on validation performance
    # Compare ResNet models
    resnet_candidates = [
        ("ResNet18 V1 (150 fit)", resnet_v1),
        ("ResNet18 V2 (150 fit)", resnet_v2),
        ("ResNet18 V2 + Extra Data (290 fingers)", resnet_v2_extra),
    ]
    # Highest val separation / lowest val EER
    best_name, best_res = max(resnet_candidates, key=lambda c: c[1]["best_val_separation"])

    summary = {
        "validation_protocol": "30 validation fingers (10 per DB), same-sensor impostors only, zero test data contamination",
        "experiments": experiments,
        "chosen_setup": {
            "name": best_name,
            "variant": best_res["variant"],
            "use_extra_data": best_res["use_extra_data"],
            "best_epoch": best_res["best_epoch"],
            "best_val_separation": best_res["best_val_separation"],
            "best_val_eer": best_res["best_val_eer"],
            "checkpoint_path": best_res["checkpoint_path"],
        },
    }

    out_file = results_dir / "finger_val_experiments.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=== VALIDATION RESULTS SUMMARY ===")
    print(f"Gabor V1:                               Val Sep={gabor_v1['val_separation']:.4f}, Val EER={gabor_v1['val_eer_percent']}%")
    print(f"Gabor V2:                               Val Sep={gabor_v2['val_separation']:.4f}, Val EER={gabor_v2['val_eer_percent']}%")
    print(f"ResNet18 V1 (150 fit):                  Val Sep={resnet_v1['best_val_separation']:.4f}, Val EER={resnet_v1['best_val_eer']*100:.2f}% (Epoch {resnet_v1['best_epoch']})")
    print(f"ResNet18 V2 (150 fit):                  Val Sep={resnet_v2['best_val_separation']:.4f}, Val EER={resnet_v2['best_val_eer']*100:.2f}% (Epoch {resnet_v2['best_epoch']})")
    print(f"ResNet18 V2 + Extra (290 fingers):      Val Sep={resnet_v2_extra['best_val_separation']:.4f}, Val EER={resnet_v2_extra['best_val_eer']*100:.2f}% (Epoch {resnet_v2_extra['best_epoch']})")
    print(f"\nWINNER CHOSEN BY VALIDATION: {best_name}")


if __name__ == "__main__":
    main()
