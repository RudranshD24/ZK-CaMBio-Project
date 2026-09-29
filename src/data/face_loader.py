"""src/data/face_loader.py

Face image loader for ZK-CaMBio.
Streams face images directly on demand without persisting pixel caches.
All paths are dynamically resolved via configs/paths.yaml.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from PIL import Image


class FaceLoader:
    """Streams face images from the configured facial dataset."""

    def __init__(self, config_path: str | Path = "configs/paths.yaml") -> None:
        self.config_path = Path(config_path)
        with open(self.config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        self.root = Path(cfg["dataset"]["face_dataset_root"])
        if not self.root.is_absolute():
            # Resolve relative to project root (where config lives)
            project_root = self.config_path.resolve().parent.parent
            self.root = (project_root / self.root).resolve()

    def get_image_path(self, folder_id: str, filename: str) -> Path:
        """Returns the full Path to a specific face image."""
        path = self.root / folder_id / filename
        if not path.is_file():
            raise FileNotFoundError(f"Face image not found: {path}")
        return path

    def load_image(self, folder_id: str, filename: str, mode: str = "RGB") -> Image.Image:
        """Loads and returns an image in memory without caching to disk."""
        path = self.get_image_path(folder_id, filename)
        with Image.open(path) as img:
            return img.convert(mode)

    def load_by_relative_path(self, rel_path: str | Path, mode: str = "RGB") -> Image.Image:
        """Loads an image given relative path under face_dataset_root."""
        path = self.root / rel_path
        if not path.is_file():
            raise FileNotFoundError(f"Face image not found: {path}")
        with Image.open(path) as img:
            return img.convert(mode)
