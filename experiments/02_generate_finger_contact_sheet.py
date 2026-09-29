"""experiments/02_generate_finger_contact_sheet.py

Generates results/finger_preproc_check.png:
A contact sheet showing before/after preprocessing for 3 images per DB
(DB1_A, DB2_A, DB3_A) to visually verify cropping, CLAHE, and normalization.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

try:
    from src.data.finger_loader import FingerprintLoader
    from src.finger.preprocess import preprocess_fingerprint
except ImportError:
    from data.finger_loader import FingerprintLoader
    from finger.preprocess import preprocess_fingerprint


def main() -> None:
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "finger_preproc_check.png"

    loader = FingerprintLoader()
    dbs = ["DB1_A", "DB2_A", "DB3_A"]
    sample_files = ["1_1.tif", "2_1.tif", "3_1.tif"]

    fig, axes = plt.subplots(len(dbs) * len(sample_files), 2, figsize=(8, 18))
    fig.suptitle(
        "FVC2004 Fingerprint Preprocessing Verification\n(Left: Raw Sensor Capture, Right: Preprocessed 128x128 CLAHE + Foreground Crop)",
        fontsize=12,
        fontweight="bold",
        y=0.995,
    )

    row = 0
    for db in dbs:
        for fname in sample_files:
            raw_img = loader.load_by_filename(db, fname)
            raw_arr = np.array(raw_img)

            preproc_arr = preprocess_fingerprint(raw_img, target_size=(128, 128))

            # Left: Raw
            ax_raw = axes[row, 0]
            ax_raw.imshow(raw_arr, cmap="gray")
            ax_raw.set_title(f"{db} - {fname}\nRaw: {raw_arr.shape[1]}x{raw_arr.shape[0]}", fontsize=9)
            ax_raw.axis("off")

            # Right: Preprocessed
            ax_proc = axes[row, 1]
            ax_proc.imshow(preproc_arr, cmap="gray")
            ax_proc.set_title("Preprocessed: 128x128", fontsize=9)
            ax_proc.axis("off")

            row += 1

    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"Fingerprint preprocessing contact sheet saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
