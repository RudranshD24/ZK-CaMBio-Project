"""experiments/01_generate_contact_sheet.py

Generates results/face_folder_check.png:
A contact sheet showing 4 randomly chosen folders (seed 42) x 8 images each,
one folder per row, to verify visual identity consistency per folder.
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    with open("configs/paths.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    face_root = Path(config["dataset"]["face_dataset_root"])
    seed = config.get("seed", 42)
    results_root = Path(config["results"]["root"])
    results_root.mkdir(parents=True, exist_ok=True)
    out_path = results_root / "face_folder_check.png"

    # Find candidate folders with at least 8 images
    image_exts = {".jpg", ".jpeg", ".png", ".bmp"}
    candidate_folders: list[Path] = []

    for d in sorted(face_root.iterdir()):
        if d.is_dir():
            # Quick check if it has >= 8 images
            imgs = [p for p in d.iterdir() if p.suffix.lower() in image_exts]
            if len(imgs) >= 8:
                candidate_folders.append(d)

    print(f"Total candidate folders with >= 8 images: {len(candidate_folders)}")

    rng = random.Random(seed)
    chosen_folders = rng.sample(candidate_folders, 4)

    tile_w, tile_h = 112, 112
    cols = 8
    rows = 4
    margin_left = 120
    header_top = 40
    padding = 6

    total_w = margin_left + cols * tile_w + (cols + 1) * padding
    total_h = header_top + rows * tile_h + (rows + 1) * padding

    contact_sheet = Image.new("RGB", (total_w, total_h), color=(30, 32, 38))
    draw = ImageDraw.Draw(contact_sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text(
        (margin_left, 12),
        "ZK-CaMBio: Face Folder Identity Check (4 random subjects x 8 images, seed 42)",
        fill=(220, 220, 220),
        font=font,
    )

    for row_idx, folder in enumerate(chosen_folders):
        folder_imgs = sorted([p for p in folder.iterdir() if p.suffix.lower() in image_exts])
        selected_imgs = folder_imgs[:cols]

        y = header_top + padding + row_idx * (tile_h + padding)

        label = f"ID: {folder.name}\n({len(folder_imgs)} imgs)"
        draw.text((12, y + tile_h // 3), label, fill=(180, 200, 230), font=font)

        print(f"\nRow {row_idx + 1} - Folder: {folder.name} (total {len(folder_imgs)} images)")
        for col_idx, img_path in enumerate(selected_imgs):
            print(f"  Col {col_idx + 1}: {img_path.name}")
            x = margin_left + padding + col_idx * (tile_w + padding)
            with Image.open(img_path) as img:
                img_rgb = img.convert("RGB")
                if img_rgb.size != (tile_w, tile_h):
                    img_rgb = img_rgb.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
                contact_sheet.paste(img_rgb, (x, y))

    contact_sheet.save(out_path, format="PNG")
    print(f"\nContact sheet successfully saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
