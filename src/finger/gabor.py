"""src/finger/gabor.py

Baseline A: Classical Gabor filter-bank grid feature extractor (FingerCode-style).
Extracts 256-dimensional L2-normalized feature vectors from preprocessed 128x128 fingerprints.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

try:
    from src.finger.preprocess import preprocess_fingerprint
except ImportError:
    from finger.preprocess import preprocess_fingerprint


class GaborFeatureExtractor:
    """Extracts 256-d FingerCode-style Average Absolute Deviation (AAD) features

    from 128x128 preprocessed fingerprint images.
    """

    def __init__(
        self,
        orientations: tuple[float, ...] = (0.0, np.pi / 4, np.pi / 2, 3 * np.pi / 4),
        kernel_size: tuple[int, int] = (21, 21),
        sigma: float = 4.0,
        lambd: float = 8.0,
        gamma: float = 0.5,
        grid_size: tuple[int, int] = (8, 8),
    ) -> None:
        self.orientations = orientations
        self.grid_size = grid_size
        self.embedding_dim = len(orientations) * grid_size[0] * grid_size[1]  # 4 * 8 * 8 = 256

        self.filters = []
        for theta in orientations:
            kernel = cv2.getGaborKernel(
                kernel_size,
                sigma=sigma,
                theta=theta,
                lambd=lambd,
                gamma=gamma,
                psi=0,
                ktype=cv2.CV_32F,
            )
            self.filters.append(kernel)

    def extract_from_preprocessed(self, arr: np.ndarray) -> np.ndarray:
        """Extracts 256-d feature vector from a (128, 128) preprocessed uint8 image."""
        h, w = arr.shape
        grid_r, grid_c = self.grid_size
        cell_h = h // grid_r
        cell_w = w // grid_c

        arr_f = arr.astype(np.float32)
        features = []

        for kernel in self.filters:
            filtered = cv2.filter2D(arr_f, cv2.CV_32F, kernel)
            for r in range(grid_r):
                for c in range(grid_c):
                    cell = filtered[r * cell_h : (r + 1) * cell_h, c * cell_w : (c + 1) * cell_w]
                    # Average Absolute Deviation (AAD)
                    mean_val = float(np.mean(cell))
                    aad = float(np.mean(np.abs(cell - mean_val)))
                    features.append(aad)

        feat = np.array(features, dtype=np.float32)
        # Zero-center to avoid trivial DC component correlation
        feat = feat - np.mean(feat)
        norm = np.linalg.norm(feat)
        if norm > 0:
            feat = feat / norm
        return feat.astype(np.float32)

    def extract(
        self,
        img: Image.Image | np.ndarray,
        db_hint: str | None = None,
        variant: str = "v2",
    ) -> np.ndarray:
        """Runs preprocessing and extracts 256-d L2-normalized Gabor features."""
        preproc = preprocess_fingerprint(img, db_hint=db_hint, target_size=(128, 128), variant=variant)
        return self.extract_from_preprocessed(preproc)

