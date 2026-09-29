"""src/data/finger_loader.py

Fingerprint image loader for ZK-CaMBio (FVC2004).
Streams fingerprint images directly on demand without persisting pixel caches.
All paths are dynamically resolved via configs/paths.yaml.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from PIL import Image


class FingerprintLoader:
    """Streams fingerprint images from the configured FVC2004 dataset."""

    def __init__(self, config_path: str | Path = "configs/paths.yaml") -> None:
        self.config_path = Path(config_path)
        with open(self.config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        self.root = Path(cfg["dataset"]["fingerprint_root"])
        if not self.root.is_absolute():
            project_root = self.config_path.resolve().parent.parent
            self.root = (project_root / self.root).resolve()

    def get_image_path(self, db_name: str, filename: str) -> Path:
        """Returns the full Path to a specific fingerprint image."""
        path = self.root / db_name / filename
        if not path.is_file():
            raise FileNotFoundError(f"Fingerprint image not found: {path}")
        return path

    def load_by_filename(self, db_name: str, filename: str, mode: str = "L") -> Image.Image:
        """Loads and returns a fingerprint image in memory without caching to disk."""
        path = self.get_image_path(db_name, filename)
        with Image.open(path) as img:
            return img.convert(mode)

    def load_impression(
        self, db_name: str, finger_id: int, impression: int, mode: str = "L"
    ) -> Image.Image:
        """Loads a specific finger impression (e.g. finger 1..100, impression 1..8)."""
        filename = f"{finger_id}_{impression}.tif"
        return self.load_by_filename(db_name, filename, mode=mode)
