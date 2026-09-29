"""experiments/00_inspect_data.py

Phase 1 Dataset Inspection Script.
Per docs/DATASET_PLAN.md and Phase 1 specifications:
- Prints and saves summary to results/data_inspection.txt.
- Inspects tree structure (depth <= 2), file counts by extension.
- Never prints more than 5 sample filenames per folder.
- Uses header-only image inspection (PIL.Image.open without .load()) to verify
  dimensions and detect any unreadable/corrupt images.
- Checks dataset/facial_dataset/ for identity labels or metadata.
- Checks dataset/archive/ (CelebA) for identity_CelebA.txt and CSV metadata.
- Verifies FVC2004 *_A folders contain exactly 800 files named <F>_<I>.tif (F in 1..100, I in 1..8).
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import TextIO

import yaml
from PIL import Image


class OutputDuplicator:
    """Duplicates printed output to both stdout and a log file."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.file: TextIO = open(log_path, "w", encoding="utf-8")  # noqa: SIM115

    def print(self, *args, **kwargs) -> None:
        print(*args, **kwargs)
        print(*args, file=self.file, **kwargs)

    def close(self) -> None:
        self.file.close()


def load_config() -> dict:
    config_path = Path("configs/paths.yaml")
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def inspect_image_header(path: Path) -> tuple[bool, tuple[int, int] | None, str | None]:
    """Header-only image inspection without decoding full pixel data."""
    try:
        with Image.open(path) as img:
            size = img.size  # (width, height)
            img_format = img.format
            return True, size, img_format
    except Exception as exc:
        return False, None, str(exc)


def inspect_directory_tree(out: OutputDuplicator, root: Path, max_depth: int = 2) -> None:
    out.print(f"\n--- Directory Tree & File Counts: {root} ---")
    if not root.exists():
        out.print(f"  [ERROR] Path does not exist: {root}")
        return

    ext_counter: Counter[str] = Counter()
    total_files = 0
    total_dirs = 0

    root_depth = len(root.resolve().parts)

    for item in root.glob("**/*"):
        item_depth = len(item.resolve().parts) - root_depth
        if item.is_dir():
            total_dirs += 1
            if item_depth <= max_depth:
                out.print(f"  [DIR]  {item.relative_to(root)}")
        elif item.is_file():
            total_files += 1
            ext = item.suffix.lower() if item.suffix else "<no_ext>"
            ext_counter[ext] += 1
            if item_depth <= max_depth:
                pass  # Avoid dumping all files; summary below

    out.print(f"\n  Total subdirectories: {total_dirs}")
    out.print(f"  Total files: {total_files}")
    out.print("  File count by extension:")
    for ext, count in ext_counter.most_common():
        out.print(f"    {ext:12s}: {count}")


def inspect_facial_dataset(out: OutputDuplicator, root: Path) -> None:
    out.print("\n" + "=" * 70)
    out.print("INSPECTION: dataset/facial_dataset/")
    out.print("=" * 70)

    if not root.exists():
        out.print(f"[ERROR] Directory not found: {root}")
        return

    # Check top-level items
    subdirs = [p for p in root.iterdir() if p.is_dir()]
    top_files = [p for p in root.iterdir() if p.is_file()]

    out.print(f"Top-level subdirectories count: {len(subdirs)}")
    out.print(f"Top-level files count: {len(top_files)}")

    if top_files:
        out.print("Top-level files:")
        for f in top_files[:15]:
            out.print(f"  {f.name} ({f.stat().st_size} bytes)")

    # Sample subdirectories (max 5)
    if subdirs:
        out.print("Sample subdirectories (up to 5):")
        for d in sorted(subdirs)[:5]:
            out.print(f"  {d.name}/")

    # Look for metadata files (CSV, TXT, JSON)
    metadata_candidates = list(root.glob("*.csv")) + list(root.glob("*.txt")) + list(root.glob("*.json"))
    out.print(f"\nMetadata candidate files found: {len(metadata_candidates)}")
    for meta in metadata_candidates:
        out.print(f"  Found metadata file: {meta.name} ({meta.stat().st_size} bytes)")
        try:
            with open(meta, encoding="utf-8", errors="replace") as mf:
                lines = [mf.readline().strip() for _ in range(5)]
            out.print("    First few lines:")
            for line in lines:
                out.print(f"      {line}")
        except Exception as e:
            out.print(f"    Could not read {meta.name}: {e}")

    # Inspect structure: Is it organized by subject folders (e.g. subject_id/img.jpg)?
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    images_by_dir: dict[str, list[Path]] = defaultdict(list)
    unreadable_count = 0
    sample_sizes = Counter()

    for p in root.glob("**/*"):
        if p.is_file() and p.suffix.lower() in image_extensions:
            parent_name = p.parent.name
            images_by_dir[parent_name].append(p)
            if len(images_by_dir[parent_name]) <= 2:
                ok, size, _ = inspect_image_header(p)
                if ok and size:
                    sample_sizes[size] += 1
                elif not ok:
                    unreadable_count += 1

    total_images = sum(len(v) for v in images_by_dir.values())
    out.print(f"\nTotal image files discovered: {total_images}")
    out.print(f"Number of containing directories: {len(images_by_dir)}")
    out.print(f"Unreadable image headers encountered: {unreadable_count}")
    if sample_sizes:
        out.print(f"Sample image dimensions observed (width x height): {dict(sample_sizes.most_common(5))}")

    # Analyze if directories correspond to identity classes
    if len(images_by_dir) > 1 and total_images > len(images_by_dir):
        images_per_id = [len(v) for v in images_by_dir.values()]
        out.print("\nDirectory-as-identity analysis:")
        out.print(f"  Min images per folder: {min(images_per_id)}")
        out.print(f"  Max images per folder: {max(images_per_id)}")
        out.print(f"  Avg images per folder: {total_images / len(images_by_dir):.1f}")
        folders_with_10plus = sum(1 for c in images_per_id if c >= 10)
        out.print(f"  Folders with >= 10 images: {folders_with_10plus}")
        # Sample folder contents
        sample_folder = sorted(images_by_dir.keys())[0]
        sample_filenames = [p.name for p in images_by_dir[sample_folder][:5]]
        out.print(f"  Sample folder '{sample_folder}' contents (max 5): {sample_filenames}")
    else:
        out.print("\nStructure does not appear to be subject-subfolder based.")
        # Sample image filenames in root or flat folder
        all_imgs = [p for p in root.glob("*") if p.is_file() and p.suffix.lower() in image_extensions]
        out.print(f"  Flat image files in root (sample max 5): {[p.name for p in all_imgs[:5]]}")


def inspect_archive_celeba(out: OutputDuplicator, root: Path) -> None:
    out.print("\n" + "=" * 70)
    out.print("INSPECTION: dataset/archive/ (CelebA)")
    out.print("=" * 70)

    if not root.exists():
        out.print(f"[ERROR] Directory not found: {root}")
        return

    # Check for identity_CelebA.txt
    identity_file = root / "identity_CelebA.txt"
    identity_exists = identity_file.is_file()
    out.print(f"identity_CelebA.txt present: {identity_exists}")
    if identity_exists:
        out.print(f"  Size: {identity_file.stat().st_size} bytes")
        with open(identity_file, encoding="utf-8", errors="replace") as f:
            sample_lines = [f.readline().strip() for _ in range(5)]
        out.print("  First 5 lines:")
        for line in sample_lines:
            out.print(f"    {line}")
    else:
        out.print("  [CRITICAL NOTE] identity_CelebA.txt is MISSING from dataset/archive/.")

    # Check CSV files
    csv_files = sorted(root.glob("*.csv"))
    out.print(f"\nCSV files present ({len(csv_files)}):")
    for cf in csv_files:
        line_count = 0
        header = None
        try:
            with open(cf, encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for _ in reader:
                    line_count += 1
            out.print(f"  {cf.name}: {line_count} data rows")
            if header:
                out.print(f"    Columns ({len(header)}): {header[:8]} ...")
        except Exception as e:
            out.print(f"  Could not read {cf.name}: {e}")

    # Inspect images in img_align_celeba if present
    img_dir = root / "img_align_celeba"
    if not img_dir.exists():
        # Check if images are in subfolder
        img_candidates = [d for d in root.iterdir() if d.is_dir() and "img" in d.name.lower()]
        if img_candidates:
            img_dir = img_candidates[0]

    if img_dir.exists():
        out.print(f"\nImage folder found: {img_dir.name}")
        image_files = list(img_dir.glob("*.jpg"))
        out.print(f"  Total .jpg images: {len(image_files)}")
        out.print(f"  Sample filenames (max 5): {[p.name for p in sorted(image_files)[:5]]}")

        # Check headers of sample images
        unreadable_sample = 0
        sizes_seen = Counter()
        for p in image_files[:100]:  # Sample first 100 for header integrity
            ok, size, _ = inspect_image_header(p)
            if ok and size:
                sizes_seen[size] += 1
            else:
                unreadable_sample += 1
        out.print(f"  Sample dimensions from first 100 images: {dict(sizes_seen)}")
        out.print(f"  Unreadable headers in sample of 100: {unreadable_sample}")
    else:
        out.print("  No img_align_celeba subfolder found.")


def inspect_fingerprint_fvc2004(out: OutputDuplicator, root: Path) -> None:
    out.print("\n" + "=" * 70)
    out.print("INSPECTION: dataset/fingerprint_dataset/ (FVC2004)")
    out.print("=" * 70)

    if not root.exists():
        out.print(f"[ERROR] Directory not found: {root}")
        return

    # Check database folders
    subdirs = sorted([p for p in root.iterdir() if p.is_dir()])
    out.print(f"Database folders found ({len(subdirs)}): {[d.name for d in subdirs]}")

    expected_a_folders = ["DB1_A", "DB2_A", "DB3_A", "DB4_A"]

    for d in subdirs:
        out.print(f"\n--- Database folder: {d.name} ---")
        tif_files = sorted(d.glob("*.tif"))
        total_tifs = len(tif_files)
        out.print(f"  Total .tif files: {total_tifs}")
        out.print(f"  Sample filenames (max 5): {[p.name for p in tif_files[:5]]}")

        # Header check on sample of 10 images per DB
        unreadable = 0
        sizes = Counter()
        for p in tif_files:
            # Check header
            ok, size, _ = inspect_image_header(p)
            if ok and size:
                sizes[size] += 1
            else:
                unreadable += 1

        out.print(f"  Image dimensions distribution: {dict(sizes.most_common(3))}")
        out.print(f"  Unreadable headers across all files in {d.name}: {unreadable}")

        # If it is an *_A folder, strictly verify the 800 files rule (100 fingers x 8 impressions)
        if d.name in expected_a_folders or d.name.endswith("_A"):
            expected_keys = {f"{f}_{i}.tif" for f in range(1, 101) for i in range(1, 9)}
            actual_keys = {p.name for p in tif_files}

            missing = expected_keys - actual_keys
            unexpected = actual_keys - expected_keys

            if len(actual_keys) == 800 and not missing and not unexpected:
                out.print("  [PASS] Exactly 800 files matching F_I.tif (finger 1..100, impression 1..8) confirmed.")
            else:
                out.print(f"  [FAIL] Expected 800 files (100x8), found {len(actual_keys)}.")
                if missing:
                    out.print(f"    Missing sample (max 5): {sorted(missing)[:5]}")
                if unexpected:
                    out.print(f"    Unexpected sample (max 5): {sorted(unexpected)[:5]}")


def main() -> None:
    config = load_config()
    out_file = Path(config["results"]["data_inspection"])
    out = OutputDuplicator(out_file)

    try:
        out.print("=" * 70)
        out.print("ZK-CaMBio: Phase 1 Data Inspection Report")
        out.print(f"Generated at: {Path.cwd()}")
        out.print("=" * 70)

        # 1. High-level dataset tree
        dataset_root = Path(config["dataset"]["root"])
        inspect_directory_tree(out, dataset_root, max_depth=2)

        # 2. Inspect facial_dataset
        face_dataset_root = Path(config["dataset"]["face_dataset_root"])
        inspect_facial_dataset(out, face_dataset_root)

        # 3. Inspect archive (CelebA)
        archive_root = Path(config["dataset"]["face_archive_root"])
        inspect_archive_celeba(out, archive_root)

        # 4. Inspect fingerprint dataset (FVC2004)
        finger_root = Path(config["dataset"]["fingerprint_root"])
        inspect_fingerprint_fvc2004(out, finger_root)

        out.print("\n" + "=" * 70)
        out.print("Inspection complete. Output saved to: " + str(out_file))
        out.print("=" * 70)
    finally:
        out.close()


if __name__ == "__main__":
    main()
