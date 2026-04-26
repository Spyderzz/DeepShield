from __future__ import annotations

import io
from typing import List

import numpy as np
from loguru import logger
from PIL import Image

from schemas.common import ArtifactIndicator


def _severity_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


# ---------- 1. GAN high-frequency signature (FFT) ----------
def detect_gan_hf_artifact(pil_img: Image.Image) -> ArtifactIndicator | None:
    """Compute high-frequency energy ratio on the luminance channel.
    Real photos typically follow a ~1/f spectrum; many GAN outputs show
    elevated HF energy or spectral peaks.
    """
    try:
        gray = np.asarray(pil_img.convert("L"), dtype=np.float32)
        # downsample for speed
        if max(gray.shape) > 512:
            import cv2

            scale = 512 / max(gray.shape)
            gray = cv2.resize(gray, (int(gray.shape[1] * scale), int(gray.shape[0] * scale)))

        fft = np.fft.fftshift(np.fft.fft2(gray))
        mag = np.abs(fft)
        h, w = mag.shape
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        r_max = np.sqrt(cx * cx + cy * cy)
        hf_mask = r > (0.5 * r_max)

        total = float(mag.sum() + 1e-9)
        hf = float(mag[hf_mask].sum())
        ratio = hf / total

        # Passport/ID portraits often have strong fine detail from hair, fabric,
        # sharpening, and JPEG ringing. Treat this as a weak forensic signal
        # unless it is extreme; the classifier ensemble remains authoritative.
        score = max(0.0, min(1.0, (ratio - 0.24) / 0.28))
        sev = _severity_from_score(score)
        return ArtifactIndicator(
            type="gan_artifact",
            severity=sev,
            description=(
                f"High-frequency energy ratio {ratio:.3f} — "
                + ("elevated fine-detail/compression energy; review with model score" if score > 0.4
                   else "within expected range for a natural photo")
            ),
            confidence=float(score),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"GAN HF detection failed: {e}")
        return None


# ---------- 2. JPEG quantization table anomaly ----------
_STANDARD_Q_SUMS = {  # rough heuristic: camera JPEGs fall in these ranges
    50: (1500, 4500),
    75: (600, 2500),
    90: (200, 1000),
    95: (100, 600),
}


def detect_compression_anomaly(raw_bytes: bytes) -> ArtifactIndicator | None:
    """Inspect JPEG quantization tables. Missing tables, non-standard layouts,
    or re-saved tables often indicate manipulation or re-encoding.
    """
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        if img.format != "JPEG":
            return ArtifactIndicator(
                type="compression",
                severity="low",
                description=f"Non-JPEG format ({img.format}); compression signature not available",
                confidence=0.1,
            )

        q = getattr(img, "quantization", None)
        if not q:
            return ArtifactIndicator(
                type="compression",
                severity="low",
                description="No JPEG quantization tables readable",
                confidence=0.2,
            )

        tables = list(q.values())
        sums = [int(sum(t)) for t in tables]
        num_tables = len(tables)

        # Heuristics: very low sum → very high quality (possibly re-saved);
        # non-standard number of tables; extreme values.
        suspicious = 0.0
        reasons: list[str] = []
        if num_tables not in (1, 2):
            suspicious += 0.4
            reasons.append(f"unusual table count ({num_tables})")
        if any(s < 60 for s in sums):
            suspicious += 0.3
            reasons.append("very low quantization sums (possible re-encoding)")
        if any(s > 8000 for s in sums):
            suspicious += 0.2
            reasons.append("very high quantization sums")

        score = max(0.0, min(1.0, suspicious))
        sev = _severity_from_score(score)
        desc = (
            f"JPEG Q-table sums {sums}"
            + (f"; {', '.join(reasons)}" if reasons else "; within typical camera range")
        )
        return ArtifactIndicator(
            type="compression",
            severity=sev,
            description=desc,
            confidence=float(score),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Compression anomaly detection failed: {e}")
        return None


# ---------- 3. Facial boundary + 4. Lighting (MediaPipe) ----------
def detect_face_based_artifacts(pil_img: Image.Image) -> List[ArtifactIndicator]:
    """If a face is detected, analyze jaw boundary variance and per-quadrant
    luminance balance. Returns 0, 1, or 2 indicators.
    """
    results: List[ArtifactIndicator] = []
    try:
        from models.model_loader import get_model_loader

        detector = get_model_loader().load_face_detector()
        if detector is None:
            return results
        rgb = np.asarray(pil_img.convert("RGB"))
        h, w = rgb.shape[:2]
        mp_result = detector.process(rgb)

        if not mp_result.multi_face_landmarks:
            return results

        landmarks = mp_result.multi_face_landmarks[0].landmark

        # ----- Jaw boundary jitter -----
        # FaceMesh jaw/oval landmark indices (approximate face contour)
        JAW_IDX = [
            10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361,
            288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149,
            150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109,
        ]
        pts = np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in JAW_IDX])
        # Second-difference magnitude = local curvature jitter
        diffs = np.diff(pts, axis=0)
        seconds = np.diff(diffs, axis=0)
        jitter = float(np.linalg.norm(seconds, axis=1).mean()) / max(w, h)
        jitter_score = max(0.0, min(1.0, (jitter - 0.003) / 0.010))
        results.append(
            ArtifactIndicator(
                type="facial_boundary",
                severity=_severity_from_score(jitter_score),
                description=(
                    f"Jaw-contour jitter {jitter:.4f} (normalized) — "
                    + ("inconsistent boundary blending detected" if jitter_score > 0.4
                       else "face boundary appears smooth")
                ),
                confidence=float(jitter_score),
            )
        )

        # ----- Lighting inconsistency (per-quadrant luminance) -----
        xs = np.array([lm.x * w for lm in landmarks])
        ys = np.array([lm.y * h for lm in landmarks])
        x0, x1 = int(max(0, xs.min())), int(min(w, xs.max()))
        y0, y1 = int(max(0, ys.min())), int(min(h, ys.max()))
        if x1 > x0 + 4 and y1 > y0 + 4:
            face_crop = rgb[y0:y1, x0:x1]
            gray = 0.299 * face_crop[..., 0] + 0.587 * face_crop[..., 1] + 0.114 * face_crop[..., 2]
            hh, ww = gray.shape
            quads = [
                gray[: hh // 2, : ww // 2],
                gray[: hh // 2, ww // 2 :],
                gray[hh // 2 :, : ww // 2],
                gray[hh // 2 :, ww // 2 :],
            ]
            means = np.array([q.mean() for q in quads if q.size > 0])
            if means.size == 4 and means.mean() > 1e-3:
                imbalance = float(means.std() / means.mean())
                lighting_score = max(0.0, min(1.0, (imbalance - 0.08) / 0.20))
                results.append(
                    ArtifactIndicator(
                        type="lighting",
                        severity=_severity_from_score(lighting_score),
                        description=(
                            f"Luminance imbalance across face quadrants {imbalance:.3f} — "
                            + ("inconsistent lighting direction" if lighting_score > 0.4
                               else "lighting appears uniform")
                        ),
                        confidence=float(lighting_score),
                    )
                )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Face-based artifact detection failed: {e}")

    return results


# ---------- Orchestrator ----------
def scan_artifacts(pil_img: Image.Image, raw_bytes: bytes) -> List[ArtifactIndicator]:
    indicators: List[ArtifactIndicator] = []
    for fn in (
        lambda: detect_gan_hf_artifact(pil_img),
        lambda: detect_compression_anomaly(raw_bytes),
    ):
        ind = fn()
        if ind is not None:
            indicators.append(ind)
    indicators.extend(detect_face_based_artifacts(pil_img))
    return indicators
