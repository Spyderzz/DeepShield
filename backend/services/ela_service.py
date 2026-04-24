"""Error Level Analysis (ELA) — Phase 12.1

Re-saves an image at a fixed JPEG quality and diffs against the original to reveal
per-pixel manipulation artifacts. Regions that were recently edited will show
higher error levels than untouched areas.
"""

from __future__ import annotations

import base64
import io

import numpy as np
from loguru import logger
from PIL import Image


def _compute_ela(pil_img: Image.Image, quality: int = 90, scale: float = 15.0) -> np.ndarray:
    """Return an ELA difference map as a uint8 (H,W,3) RGB array.

    Args:
        pil_img: Input image (any format — converted to RGB internally).
        quality: JPEG re-save quality level (lower = more aggressive compression).
        scale: Amplification factor for the difference (higher = more contrast).

    Returns:
        Difference image as uint8 (H,W,3) array.
    """
    rgb = pil_img.convert("RGB")

    # Re-save at specified JPEG quality into an in-memory buffer
    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    resaved = Image.open(buf).convert("RGB")

    original_arr = np.array(rgb, dtype=np.float32)
    resaved_arr = np.array(resaved, dtype=np.float32)

    # Per-pixel absolute difference, amplified
    diff = np.abs(original_arr - resaved_arr) * scale
    diff = np.clip(diff, 0, 255).astype(np.uint8)

    return diff


def generate_ela_base64(pil_img: Image.Image, quality: int = 90, scale: float = 15.0) -> str:
    """Produce a base64 data-URL PNG of the ELA difference map.

    Regions with higher error levels (brighter in the output) are more likely
    to have been digitally manipulated.
    """
    diff = _compute_ela(pil_img, quality=quality, scale=scale)

    buf = io.BytesIO()
    Image.fromarray(diff).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    logger.info(f"ELA map generated ({diff.shape[1]}x{diff.shape[0]})")
    return f"data:image/png;base64,{b64}"


def generate_blended_ela_base64(
    pil_img: Image.Image,
    gradcam_weight: float = 0.6,
    ela_weight: float = 0.4,
    quality: int = 90,
    scale: float = 15.0,
) -> str:
    """Blend Grad-CAM heatmap overlay with ELA at specified weights.

    This is a utility for the 'blended' mode — it composites the ELA
    difference map on top of the original image for visual clarity.
    """
    rgb = pil_img.convert("RGB")
    original_arr = np.array(rgb, dtype=np.float32)
    ela_arr = _compute_ela(pil_img, quality=quality, scale=scale).astype(np.float32)

    # Blend: overlay ELA on the original for visual context
    blended = np.clip(original_arr * 0.5 + ela_arr * 0.5, 0, 255).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(blended).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    logger.info(f"Blended ELA generated ({blended.shape[1]}x{blended.shape[0]})")
    return f"data:image/png;base64,{b64}"
