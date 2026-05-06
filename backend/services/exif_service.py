"""EXIF Metadata Extraction — Phase 12.2

Extracts camera metadata from uploaded images and computes a trust adjustment
score: presence of authentic camera metadata lowers fake probability, while
evidence of editing software raises it.

Phase B3: EXIF acts as a weak modifier (±6 max), not a booster. Positive
adjustments (toward "real") are suppressed when upstream model signals
indicate the image is likely synthetic.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from schemas.common import ExifSummary


# Software strings that suggest post-processing or generative synthesis.
# Extended for Phase B3 to cover modern AI image generators.
_SUSPICIOUS_SOFTWARE = {
    "adobe photoshop", "photoshop", "gimp", "affinity photo",
    "stable diffusion", "midjourney", "dall-e", "comfyui",
    "automatic1111", "invokeai", "firefly", "runway", "sora",
    "flux", "ideogram", "leonardo", "nightcafe", "dreamstudio",
    "adobe firefly", "canva", "fotor",
}

# Software strings that are normal camera firmware
_CAMERA_SOFTWARE = {
    "ver.", "firmware", "camera", "dji", "gopro",
}


def rescore_exif_trust(
    summary: ExifSummary,
    *,
    general_fake_prob: Optional[float] = None,
) -> ExifSummary:
    """Re-run trust-adjustment scoring on an already-extracted ExifSummary.

    Used after classification so the general model's fake probability can
    suppress positive (real-leaning) EXIF boosts (Phase B3).
    Returns the same summary object mutated in-place.
    """
    adjustment = 0
    reasons = []

    is_generative_software = False
    if summary.software:
        sw_lower = summary.software.lower()
        if any(s in sw_lower for s in _SUSPICIOUS_SOFTWARE):
            is_generative_software = True
            adjustment += 6
            reasons.append(f"generative/editing software detected: {summary.software}")
        elif any(s in sw_lower for s in _CAMERA_SOFTWARE):
            adjustment -= 1
            reasons.append("camera firmware in Software field")

    suppress_positive = (
        is_generative_software
        or (general_fake_prob is not None and general_fake_prob >= 0.60)
    )

    has_camera_meta = summary.make and summary.model and summary.datetime_original
    if has_camera_meta and not suppress_positive:
        adjustment -= 5
        reasons.append("valid camera metadata")

    if summary.maker_note and not suppress_positive:
        adjustment -= 4
        reasons.append("proprietary MakerNote present")

    if summary.gps_info and not suppress_positive:
        adjustment -= 2
        reasons.append("GPS coordinates present")

    if summary.lens_model and not suppress_positive:
        adjustment -= 2
        reasons.append("lens model metadata present")

    if suppress_positive and not is_generative_software:
        reasons.append("positive EXIF boost suppressed (synthetic model signal)")

    adjustment = max(-6, min(6, adjustment))
    summary.trust_adjustment = adjustment
    summary.trust_reason = "; ".join(reasons) if reasons else "no EXIF metadata found"
    return summary


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
        if abs(lat) < 1e-9 and abs(lon) < 1e-9:
            return None
        return f"{lat:.6f}, {lon:.6f}"
    except Exception:
        return None


def extract_exif(
    pil_img: Image.Image,
    raw_bytes: bytes,
    *,
    general_fake_prob: Optional[float] = None,
) -> ExifSummary:
    """Extract EXIF metadata and compute a trust adjustment score.

    Phase B3 rules:
    - Max impact capped at ±6 (was ±12) to prevent EXIF alone from swinging verdict.
    - Positive adjustments (toward "real") are suppressed when:
        * general_fake_prob >= 0.60 (upstream model sees strong synthetic signal), OR
        * software field names a generative AI tool.
    - Negative adjustments (toward "fake" for editing software) remain always active.
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
                
                summary.icc_profile = bool(pil_img.info.get("icc_profile"))
                summary.maker_note = bool(tags.get("EXIF MakerNote"))
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

        summary.icc_profile = bool(pil_img.info.get("icc_profile"))
        summary.maker_note = bool(decoded.get("MakerNote"))

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

    # Phase B3: detect generative software early so we can suppress positive boosts.
    is_generative_software = False
    if summary.software:
        sw_lower = summary.software.lower()
        if any(s in sw_lower for s in _SUSPICIOUS_SOFTWARE):
            is_generative_software = True
            adjustment += 6
            reasons.append(f"generative/editing software detected: {summary.software}")
        elif any(s in sw_lower for s in _CAMERA_SOFTWARE):
            adjustment -= 1
            reasons.append("camera firmware in Software field")

    # Suppress positive (real-leaning) adjustments when upstream signals are
    # already strongly synthetic. Negative adjustments stay active in all cases.
    suppress_positive = (
        is_generative_software
        or (general_fake_prob is not None and general_fake_prob >= 0.60)
    )

    has_camera_meta = summary.make and summary.model and summary.datetime_original
    if has_camera_meta and not suppress_positive:
        adjustment -= 5
        reasons.append("valid camera metadata")

    if summary.maker_note and not suppress_positive:
        adjustment -= 4
        reasons.append("proprietary MakerNote present")

    if summary.gps_info and not suppress_positive:
        adjustment -= 2
        reasons.append("GPS coordinates present")

    if summary.lens_model and not suppress_positive:
        adjustment -= 2
        reasons.append("lens model metadata present")

    if suppress_positive and not is_generative_software:
        reasons.append("positive EXIF boost suppressed (synthetic model signal)")

    adjustment = max(-6, min(6, adjustment))

    summary.trust_adjustment = adjustment
    summary.trust_reason = "; ".join(reasons) if reasons else "no EXIF metadata found"

    logger.info(f"EXIF extracted: make={summary.make}, model={summary.model}, "
                f"adjustment={adjustment} ({summary.trust_reason})")
    return summary
