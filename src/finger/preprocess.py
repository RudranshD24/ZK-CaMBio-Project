"""src/finger/preprocess.py

Fingerprint image preprocessing pipeline for FVC2004:
- Grayscale conversion
- Foreground segmentation & bounding-box crop (block variance)
- CLAHE ridge contrast enhancement
- Intensity normalization
- Common size resize (128x128)

Justification for 128x128:
1. Normalizes disparate FVC sensor resolutions (DB1: 640x480, DB2: 328x364, DB3: 300x480)
   to a unified spatial canvas after cropping sensor borders.
2. Preserves fundamental ridge flow (3-7 px per ridge cycle), sufficient for both
   Gabor spatial frequency analysis and CNN receptive fields.
3. Accelerates feature extraction and CNN training on CPU/GPU by >10x compared to full sensor frames.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def segment_foreground(
    gray: np.ndarray,
    block_size: int = 16,
    var_thresh: float = 100.0,
    margin: int = 8,
) -> tuple[int, int, int, int]:
    """Computes bounding box (ymin, ymax, xmin, xmax) of the fingerprint active area

    using local block standard deviation / variance.
    """
    h, w = gray.shape
    pad_h = (block_size - (h % block_size)) % block_size
    pad_w = (block_size - (w % block_size)) % block_size

    if pad_h > 0 or pad_w > 0:
        padded = np.pad(gray, ((0, pad_h), (0, pad_w)), mode="reflect")
    else:
        padded = gray

    # Compute block variance
    blocks_h = padded.shape[0] // block_size
    blocks_w = padded.shape[1] // block_size

    reshaped = padded.reshape(blocks_h, block_size, blocks_w, block_size)
    block_std = reshaped.std(axis=(1, 3))

    # Adaptive threshold: fraction of max std, or fixed minimum
    thresh = max(var_thresh, 0.15 * float(block_std.max()))
    mask = block_std > thresh

    if not np.any(mask):
        # Fallback to full image if no foreground detected
        return 0, h, 0, w

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    ymin = max(0, rmin * block_size - margin)
    ymax = min(h, (rmax + 1) * block_size + margin)
    xmin = max(0, cmin * block_size - margin)
    xmax = min(w, (cmax + 1) * block_size + margin)

    # Sanity check: must be at least 32x32
    if ymax - ymin < 32 or xmax - xmin < 32:
        return 0, h, 0, w

    return ymin, ymax, xmin, xmax


def preprocess_fingerprint(
    img: Image.Image | np.ndarray,
    target_size: tuple[int, int] = (128, 128),
    clip_limit: float = 2.5,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """Complete preprocessing pipeline for one fingerprint image:

    1. Grayscale conversion (uint8)
    2. Foreground crop
    3. CLAHE enhancement
    4. Intensity normalization
    5. Resize to target_size (default: 128x128)
    Returns: uint8 2D numpy array of shape target_size.
    """
    if isinstance(img, Image.Image):
        arr = np.array(img.convert("L"), dtype=np.uint8)
    elif isinstance(img, np.ndarray):
        arr = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img.astype(np.uint8)
    else:
        raise TypeError(f"Unsupported image type: {type(img)}")

    # 1. Foreground segmentation & crop
    ymin, ymax, xmin, xmax = segment_foreground(arr)
    cropped = arr[ymin:ymax, xmin:xmax]

    # 2. CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced = clahe.apply(cropped)

    # 3. Intensity normalization (stretch to 0..255)
    p_min, p_max = float(enhanced.min()), float(enhanced.max())
    if p_max > p_min:
        normed = ((enhanced.astype(np.float32) - p_min) / (p_max - p_min) * 255.0).astype(np.uint8)
    else:
        normed = enhanced

    # 4. Resize to common target size
    resized = cv2.resize(normed, target_size, interpolation=cv2.INTER_AREA)

    return resized
