"""scripts/reproduce_all.py

Master Reproducibility Pipeline for ZK-CaMBio.
Executes all experimental evaluation pipelines in sequential order from cached embeddings:
1. Face Baseline Evaluation (experiments/01_face_baseline.py)
2. Fingerprint Baseline Evaluation (experiments/02_finger_baseline.py)
3. Multimodal Fusion Evaluation (experiments/03_fusion_baseline.py)
4. Chaos Engine Property Check & Smoke Eval (experiments/04_chaos_smoke_eval.py)
5. Cancelable Biometric Evaluation (experiments/05_cancelable_eval.py)
6. Security & Non-Invertibility Evaluation (experiments/06_security_eval.py)

Regenerates all figures, tables, and JSON result artifacts in results/.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENTS = [
    ("01_face_baseline.py", "Face Recognition Baseline"),
    ("02_finger_baseline.py", "Fingerprint Recognition Baseline"),
    ("03_fusion_baseline.py", "Multimodal Feature & Score Fusion"),
    ("04_chaos_smoke_eval.py", "Chaos Engine Properties & Validation"),
    ("05_cancelable_eval.py", "Cancelable Biometric Evaluation (Scenario K/U, Revocability, Unlinkability)"),
    ("06_security_eval.py", "Security & Non-Invertibility Evaluation (Threats A1, A2, A3)"),
]

def main() -> int:
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    print("=" * 70)
    print("ZK-CaMBio: Master Reproducibility Pipeline")
    print(f"Working Directory: {root}")
    print("=" * 70)

    # 1. Prerequisite checks
    print("\n[Step 0] Checking prerequisites...")
    required_caches = [
        "data/processed/split_manifest.json",
        "data/processed/face_embeddings.npz",
        "data/processed/finger_embeddings_resnet.npz",
        "data/processed/fused_embeddings.npz",
    ]
    missing = [c for c in required_caches if not (root / c).is_file()]
    if missing:
        print(f"ERROR: Missing required cached embeddings: {missing}")
        print("Please ensure data/processed/ contains the required .npz embeddings caches.")
        return 1

    try:
        import chaoshash  # noqa: F401
        print("  [OK] C++ chaoshash extension importable")
    except ImportError:
        print("ERROR: chaoshash extension not found. Compile it first with: pip install -e . or python setup.py build_ext --inplace")
        return 1

    t0_all = time.time()

    # 2. Run experiments in order
    for script_name, description in EXPERIMENTS:
        script_path = root / "experiments" / script_name
        print("\n" + "-" * 70)
        print(f"Running: {script_name} - {description}")
        print("-" * 70)
        t0 = time.time()
        res = subprocess.run([sys.executable, str(script_path)], check=False)
        dt = time.time() - t0
        if res.returncode != 0:
            print(f"ERROR: {script_name} failed with return code {res.returncode}")
            return res.returncode
        print(f"  [OK] Completed in {dt:.2f}s")

    total_time = time.time() - t0_all
    print("\n" + "=" * 70)
    print(f"All experiments completed successfully in {total_time:.1f}s!")
    print("Artifacts regenerated in results/ directory.")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
