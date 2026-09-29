"""src/finger/preprocess.py

Fingerprint image preprocessing pipeline for FVC2004:
Supports two variants:
- V1: Adaptive foreground bounding-box crop with aspect-ratio-preserving padding.
- V2 (Recommended): Fixed physical scale factor per DB centered on foreground centroid,
  cropping/padding to a fixed spatial window with single constant padding (255) and tighter
  DB2 platen window strictly excluding slanted trapezoid edges.

Justification for V2 scale factors and window sizes (target 128x128):
- DB1 (Optical, 640x480, 500 dpi): Typical foreground is ~250-300px wide by ~350-390px high.
  Fixed window = 384x384 (scale factor s = 128/384 = 0.333) comfortably contains the entire active
  print while guaranteeing 100% identical ridge frequency across all DB1 images.
- DB2 (Optical, 328x364, 500 dpi): The optical platen casing introduces slanted trapezoid borders
  in columns < 42 and > 286. Inner platen width is 244px. Window = 256x256 (scale factor s = 128/256 = 0.50),
  centered horizontally at the platen center (x=164) and vertically at the foreground centroid,
  tightly excludes the slanted borders while retaining full core/delta ridge structures.
- DB3 (Thermal sweep, 300x480, 512 dpi): Active swipe is ~260px wide by ~420-460px high.
  Fixed window = 384x384 (scale factor s = 128/384 = 0.333), centered at x=150 and the foreground
  centroid, matches DB1's physical ridge scaling.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def segment_foreground(
    gray: np.ndarray,
    db_hint: str | None = None,
) -> tuple[int, int, int, int]:
    """Computes bounding box (ymin, ymax, xmin, xmax) of the active fingerprint area (V1)."""
    h, w = gray.shape

    if db_hint is None:
        if w == 640 and h == 480:
            db_hint = "DB1"
        elif w == 328 and h == 364:
            db_hint = "DB2"
        elif w == 300 and h == 480:
            db_hint = "DB3"
        else:
            db_hint = "GENERIC"

    mean = cv2.blur(gray.astype(np.float32), (17, 17))
    sq_mean = cv2.blur(gray.astype(np.float32) ** 2, (17, 17))
    local_std = np.sqrt(np.maximum(0, sq_mean - mean**2))
    max_std = float(local_std.max())

    if "DB1" in db_hint:
        thresh = max(3.5, 0.08 * max_std)
        mask = (local_std > thresh) & (gray < 252)
        min_w_frac, min_h_frac = 0.35, 0.45
    elif "DB2" in db_hint:
        border_mask = gray > 235
        dilated_border = (
            cv2.dilate(
                border_mask.astype(np.uint8),
                cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21)),
            )
            > 0
        )
        thresh = max(6.0, 0.12 * max_std)
        mask = (local_std > thresh) & (~dilated_border)
        mask[:8, :] = False
        mask[-8:, :] = False
        mask[:, :16] = False
        mask[:, -16:] = False
        min_w_frac, min_h_frac = 0.50, 0.55
    elif "DB3" in db_hint:
        thresh = max(10.0, 0.15 * max_std)
        mask = local_std > thresh
        min_w_frac, min_h_frac = 0.55, 0.60
    else:
        thresh = max(5.0, 0.10 * max_std)
        mask = local_std > thresh
        min_w_frac, min_h_frac = 0.40, 0.40

    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    closed = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel_close)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned)
    if num_labels > 1:
        max_idx = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
        bx = int(stats[max_idx, cv2.CC_STAT_LEFT])
        by = int(stats[max_idx, cv2.CC_STAT_TOP])
        bw = int(stats[max_idx, cv2.CC_STAT_WIDTH])
        bh = int(stats[max_idx, cv2.CC_STAT_HEIGHT])
    else:
        bx, by, bw, bh = 0, 0, w, h

    margin_x = max(20, int(0.12 * bw))
    margin_y = max(20, int(0.12 * bh))

    xmin = max(0, bx - margin_x)
    xmax = min(w, bx + bw + margin_x)
    ymin = max(0, by - margin_y)
    ymax = min(h, by + bh + margin_y)

    min_w = int(min_w_frac * w)
    min_h = int(min_h_frac * h)
    if (xmax - xmin) < min_w:
        mid_x = (xmin + xmax) // 2
        xmin = max(0, mid_x - min_w // 2)
        xmax = min(w, xmin + min_w)
    if (ymax - ymin) < min_h:
        mid_y = (ymin + ymax) // 2
        ymin = max(0, mid_y - min_h // 2)
        ymax = min(h, ymin + min_h)

    return ymin, ymax, xmin, xmax


def preprocess_fingerprint_v1(
    img: Image.Image | np.ndarray,
    db_hint: str | None = None,
    target_size: tuple[int, int] = (128, 128),
    clip_limit: float = 2.5,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """Preprocessing V1: Adaptive foreground crop with aspect-ratio-preserving padding."""
    if isinstance(img, Image.Image):
        arr = np.array(img.convert("L"), dtype=np.uint8)
    elif isinstance(img, np.ndarray):
        arr = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img.astype(np.uint8)
    else:
        raise TypeError(f"Unsupported image type: {type(img)}")

    ymin, ymax, xmin, xmax = segment_foreground(arr, db_hint=db_hint)
    cropped = arr[ymin:ymax, xmin:xmax]

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced = clahe.apply(cropped)

    p_min, p_max = float(enhanced.min()), float(enhanced.max())
    if p_max > p_min:
        normed = ((enhanced.astype(np.float32) - p_min) / (p_max - p_min) * 255.0).astype(np.uint8)
    else:
        normed = enhanced

    th, tw = target_size
    ch, cw = normed.shape
    scale = min(th / ch, tw / cw)
    nh, nw = int(round(ch * scale)), int(round(cw * scale))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(normed, (nw, nh), interpolation=interp)

    border_pixels = np.concatenate([normed[0, :], normed[-1, :], normed[:, 0], normed[:, -1]])
    pad_val = int(np.median(border_pixels))

    pad_top = (th - nh) // 2
    pad_bottom = th - nh - pad_top
    pad_left = (tw - nw) // 2
    pad_right = tw - nw - pad_left

    padded = cv2.copyMakeBorder(
        resized,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2.BORDER_CONSTANT,
        value=pad_val,
    )
    return padded


def preprocess_fingerprint_v2(
    img: Image.Image | np.ndarray,
    db_hint: str | None = None,
    target_size: tuple[int, int] = (128, 128),
    clip_limit: float = 2.5,
    tile_grid_size: tuple[int, int] = (8, 8),
    pad_value: int = 255,
) -> np.ndarray:
    """Preprocessing V2: Fixed scale factor per DB centered on foreground centroid,

    cropping/padding to a fixed spatial window with constant padding (255) and tighter DB2 window.
    """
    if isinstance(img, Image.Image):
        arr = np.array(img.convert("L"), dtype=np.uint8)
    elif isinstance(img, np.ndarray):
        arr = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img.astype(np.uint8)
    else:
        raise TypeError(f"Unsupported image type: {type(img)}")

    h, w = arr.shape

    if db_hint is None:
        if w == 640 and h == 480:
            db_hint = "DB1"
        elif w == 328 and h == 364:
            db_hint = "DB2"
        elif w == 300 and h == 480:
            db_hint = "DB3"
        elif w == 288 and h == 384:
            db_hint = "DB4"
        else:
            db_hint = "GENERIC"

    # Fixed window sizes per sensor
    if "DB1" in db_hint:
        win_size = 384  # scale = 128/384 = 0.333
    elif "DB2" in db_hint:
        win_size = 256  # scale = 128/256 = 0.50 (excludes slanted borders <42 and >286)
    elif "DB3" in db_hint:
        win_size = 384  # scale = 128/384 = 0.333
    elif "DB4" in db_hint:
        win_size = 320  # scale = 128/320 = 0.40
    else:
        win_size = 384

    scale = target_size[0] / win_size

    # Compute foreground centroid
    mean = cv2.blur(arr.astype(np.float32), (17, 17))
    sq_mean = cv2.blur(arr.astype(np.float32) ** 2, (17, 17))
    local_std = np.sqrt(np.maximum(0, sq_mean - mean**2))
    max_std = float(local_std.max())

    if "DB1" in db_hint:
        mask = (local_std > max(3.5, 0.08 * max_std)) & (arr < 252)
    elif "DB2" in db_hint:
        mask = local_std > max(6.0, 0.12 * max_std)
        mask[:, :42] = False
        mask[:, 286:] = False
        mask[:10, :] = False
        mask[-10:, :] = False
    elif "DB3" in db_hint:
        mask = local_std > max(10.0, 0.15 * max_std)
    else:
        mask = local_std > max(5.0, 0.10 * max_std)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    cleaned = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    ys, xs = np.where(cleaned)

    if len(ys) > 0:
        cy = int(np.mean(ys))
        cx = int(np.mean(xs))
    else:
        cy, cx = h // 2, w // 2

    if "DB2" in db_hint:
        cx = 164  # center between columns 42 and 286
        cy = max(win_size // 2, min(h - win_size // 2, cy))
    elif "DB3" in db_hint:
        cx = 150  # center of 300px thermal sweep sensor
    elif "DB4" in db_hint:
        cx = 144

    half_win = win_size // 2
    x1, x2 = cx - half_win, cx + half_win
    y1, y2 = cy - half_win, cy + half_win

    src_x1 = max(0, x1)
    src_x2 = min(w, x2)
    src_y1 = max(0, y1)
    src_y2 = min(h, y2)

    crop = arr[src_y1:src_y2, src_x1:src_x2].copy()

    # DB2: blank out any pixels outside platen [42, 286]
    if "DB2" in db_hint:
        for c in range(src_x1, src_x2):
            if c < 42 or c >= 286:
                crop[:, c - src_x1] = 255

    # CLAHE
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced = clahe.apply(crop)

    # Normalize active dynamic range 0..255
    p_min, p_max = float(enhanced.min()), float(enhanced.max())
    if p_max > p_min:
        normed = ((enhanced.astype(np.float32) - p_min) / (p_max - p_min) * 255.0).astype(np.uint8)
    else:
        normed = enhanced

    # Scale using fixed scale factor
    nh = int(round((src_y2 - src_y1) * scale))
    nw = int(round((src_x2 - src_x1) * scale))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(normed, (nw, nh), interpolation=interp)

    # Pad to exact target_size with single constant (pad_value = 255)
    pad_left = int(round(max(0, -x1) * scale))
    pad_top = int(round(max(0, -y1) * scale))
    pad_right = target_size[1] - nw - pad_left
    pad_bottom = target_size[0] - nh - pad_top

    padded = cv2.copyMakeBorder(
        resized,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2.BORDER_CONSTANT,
        value=pad_value,
    )

    if padded.shape != target_size:
        padded = cv2.resize(padded, target_size, interpolation=cv2.INTER_NEAREST)

    return padded


def preprocess_fingerprint(
    img: Image.Image | np.ndarray,
    db_hint: str | None = None,
    target_size: tuple[int, int] = (128, 128),
    variant: str = "v2",
) -> np.ndarray:
    """Unified entry point for fingerprint preprocessing.

    variant: "v1" (adaptive crop) or "v2" (fixed scale, default).
    """
    if variant == "v1":
        return preprocess_fingerprint_v1(img, db_hint=db_hint, target_size=target_size)
    return preprocess_fingerprint_v2(img, db_hint=db_hint, target_size=target_size)
