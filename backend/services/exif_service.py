"""EXIF Metadata Extraction — Phase 12.2

Extracts camera metadata from uploaded images and computes a trust adjustment
score: presence of authentic camera metadata lowers fake probability, while
evidence of editing software raises it.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from schemas.common import ExifSummary


# Software strings that suggest post-processing / generation
_SUSPICIOUS_SOFTWARE = {
    "adobe photoshop", "photoshop", "gimp", "affinity photo",
    "stable diffusion", "midjourney", "dall-e", "comfyui",
    "automatic1111", "invokeai",
}

# Software strings that are normal camera firmware
_CAMERA_SOFTWARE = {
    "ver.", "firmware", "camera", "dji", "gopro",
}


def _decode_gps(gps_info: dict) -> Optional[str]:
    """Decode EXIF GPSInfo dict into a human-readable lat/lon string."""
    try:
        def _to_decimal(values, ref):
            d, m, s = [float(v) for v in values]
            decimal = d + m / 60.0 + s / 3600.0
            if ref in ("S", "W"):
                decimal = -decimal
            return decimal

        lat = _to_decimal(gps_info.get(2, (0, 0, 0)), gps_info.get(1, "N"))
        lon = _to_decimal(gps_info.get(4, (0, 0, 0)), gps_info.get(3, "E"))
        return f"{lat:.6f}, {lon:.6f}"
    except Exception:
        return None


def extract_exif(pil_img: Image.Image, raw_bytes: bytes) -> ExifSummary:
    """Extract EXIF metadata and compute a trust adjustment score.

    Trust adjustment logic:
    - Valid Make + Model + DateTimeOriginal → -15 (more likely real camera photo)
    - GPS info present → -5 additional (real photos often have GPS)
    - Suspicious editing software detected → +10 (more likely manipulated)
    - No EXIF at all → 0 (inconclusive — many platforms strip EXIF)
    """
    summary = ExifSummary()

    try:
        exif_data = pil_img._getexif()
    except Exception:
        exif_data = None

    if not exif_data:
        # Try exifread as fallback for formats Pillow doesn't handle well
        try:
            import exifread
            from io import BytesIO
            tags = exifread.process_file(BytesIO(raw_bytes), details=False)
            if tags:
                summary.make = str(tags.get("Image Make", "")).strip() or None
                summary.model = str(tags.get("Image Model", "")).strip() or None
                summary.datetime_original = str(tags.get("EXIF DateTimeOriginal", "")).strip() or None
                summary.software = str(tags.get("Image Software", "")).strip() or None
                summary.lens_model = str(tags.get("EXIF LensModel", "")).strip() or None
        except ImportError:
            logger.debug("exifread not installed, skipping fallback EXIF extraction")
        except Exception as e:
            logger.debug(f"exifread fallback failed: {e}")
    else:
        # Decode Pillow EXIF
        decoded = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            decoded[tag_name] = value

        summary.make = str(decoded.get("Make", "")).strip() or None
        summary.model = str(decoded.get("Model", "")).strip() or None
        summary.datetime_original = str(decoded.get("DateTimeOriginal", "")).strip() or None
        summary.software = str(decoded.get("Software", "")).strip() or None
        summary.lens_model = str(decoded.get("LensModel", "")).strip() or None

        # GPS
        gps_raw = decoded.get("GPSInfo")
        if gps_raw and isinstance(gps_raw, dict):
            gps_decoded = {}
            for k, v in gps_raw.items():
                gps_decoded[GPSTAGS.get(k, k)] = v
            summary.gps_info = _decode_gps(gps_decoded)

    # ── Trust adjustment scoring ──
    adjustment = 0
    reasons = []

    has_camera_meta = summary.make and summary.model and summary.datetime_original
    if has_camera_meta:
        adjustment -= 15
        reasons.append("valid camera metadata (Make/Model/DateTime)")

    if summary.gps_info:
        adjustment -= 5
        reasons.append("GPS coordinates present")

    if summary.software:
        sw_lower = summary.software.lower()
        if any(s in sw_lower for s in _SUSPICIOUS_SOFTWARE):
            adjustment += 10
            reasons.append(f"editing software detected: {summary.software}")
        elif any(s in sw_lower for s in _CAMERA_SOFTWARE):
            adjustment -= 2
            reasons.append("camera firmware in Software field")

    summary.trust_adjustment = adjustment
    summary.trust_reason = "; ".join(reasons) if reasons else "no EXIF metadata found"

    logger.info(f"EXIF extracted: make={summary.make}, model={summary.model}, "
                f"adjustment={adjustment} ({summary.trust_reason})")
    return summary
