"""Phase 17.1 — Temporal Consistency Module.

Analyses optical flow variance, luminance flicker, and blink timing across
sampled video frames to produce a temporal_score (0–100, higher = more natural).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import cv2
import numpy as np
from loguru import logger


@dataclass
class TemporalAnalysis:
    temporal_score: float           # 0–100, higher = more natural / authentic
    optical_flow_variance: float    # mean inter-frame flow-magnitude variance
    flicker_score: float            # 0–100 (high = suspicious micro-flicker)
    blink_rate_anomaly: bool        # True when blink timing is unnatural
    blink_intervals: List[float] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Optical-flow variance
# ---------------------------------------------------------------------------

def _compute_optical_flow_variance(frames_bgr: List[np.ndarray]) -> float:
    """Mean variance of inter-frame optical-flow magnitudes.

    Real videos show consistent, smooth motion; deepfake temporal inconsistencies
    appear as irregular per-frame flow jumps.
    """
    if len(frames_bgr) < 2:
        return 0.0

    flow_mags: List[float] = []
    for i in range(len(frames_bgr) - 1):
        prev_gray = cv2.cvtColor(frames_bgr[i], cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(frames_bgr[i + 1], cv2.COLOR_BGR2GRAY)

        h, w = prev_gray.shape
        scale = min(1.0, 320.0 / max(h, w, 1))
        if scale < 1.0:
            dsize = (max(1, int(w * scale)), max(1, int(h * scale)))
            prev_gray = cv2.resize(prev_gray, dsize)
            curr_gray = cv2.resize(curr_gray, dsize)

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
        )
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        flow_mags.append(float(np.mean(mag)))

    return float(np.var(flow_mags)) if flow_mags else 0.0


# ---------------------------------------------------------------------------
# Luminance flicker
# ---------------------------------------------------------------------------

def _compute_flicker_score(frames_bgr: List[np.ndarray]) -> float:
    """Flicker score 0–100 derived from inter-frame luminance variance.

    Deepfake GAN generators introduce subtle luminance micro-flicker that
    manifests as high variance in the difference sequence.
    """
    if len(frames_bgr) < 2:
        return 0.0

    mean_lums = [
        float(np.mean(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)))
        for f in frames_bgr
    ]
    diffs = [abs(mean_lums[i + 1] - mean_lums[i]) for i in range(len(mean_lums) - 1)]
    if not diffs:
        return 0.0

    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs))
    flicker_ratio = std_diff / (mean_diff + 1e-6)
    return float(min(100.0, flicker_ratio * 50.0))


# ---------------------------------------------------------------------------
# Blink-rate anomaly (FaceMesh EAR)
# ---------------------------------------------------------------------------

def _compute_blink_anomaly(
    frames_bgr: List[np.ndarray],
    timestamps: List[float],
) -> Tuple[bool, List[float]]:
    """Detect unnatural blink timing using MediaPipe FaceMesh eye-aspect-ratio.

    Returns (anomaly_detected, blink_interval_list_seconds).
    Natural blink rate: ~15–20/min → intervals ~3–4 s.
    Anomalies: perfectly regular cadence (std < 0.05 s) or rate > 2/s.
    """
    try:
        import mediapipe as mp
        mp_face_mesh = mp.solutions.face_mesh
    except ImportError:
        return False, []

    # Landmark indices for left eye (vertical & horizontal pairs)
    EYE_V = (159, 145)
    EYE_H = (33, 133)
    BLINK_THRESH = 0.25

    ear_seq: List[Tuple[float, float]] = []

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    ) as mesh:
        for frame_bgr, ts in zip(frames_bgr, timestamps):
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            res = mesh.process(rgb)
            if not (res and res.multi_face_landmarks):
                continue
            lm = res.multi_face_landmarks[0].landmark
            h, w = frame_bgr.shape[:2]

            def pt(idx: int) -> np.ndarray:
                return np.array([lm[idx].x * w, lm[idx].y * h])

            v = float(np.linalg.norm(pt(EYE_V[0]) - pt(EYE_V[1])))
            h_dist = float(np.linalg.norm(pt(EYE_H[0]) - pt(EYE_H[1])))
            ear = v / (h_dist + 1e-6)
            ear_seq.append((ts, ear))

    if len(ear_seq) < 3:
        return False, []

    blink_times: List[float] = []
    in_blink = False
    for ts, ear in ear_seq:
        if ear < BLINK_THRESH and not in_blink:
            blink_times.append(ts)
            in_blink = True
        elif ear >= BLINK_THRESH:
            in_blink = False

    if len(blink_times) < 2:
        return False, []

    intervals = [
        round(blink_times[i + 1] - blink_times[i], 3)
        for i in range(len(blink_times) - 1)
    ]
    mean_iv = float(np.mean(intervals))
    std_iv = float(np.std(intervals))
    anomaly = (std_iv < 0.05 and len(intervals) > 2) or mean_iv < 0.5
    return bool(anomaly), intervals


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_temporal_score(
    frames_bgr: List[np.ndarray],
    timestamps: List[float],
) -> TemporalAnalysis:
    """Compute temporal consistency for a list of BGR video frames.

    Args:
        frames_bgr:  BGR numpy arrays in temporal order.
        timestamps:  Corresponding timestamps in seconds.

    Returns:
        TemporalAnalysis with temporal_score 0–100 (higher = more authentic).
    """
    if len(frames_bgr) < 2:
        return TemporalAnalysis(
            temporal_score=50.0,
            optical_flow_variance=0.0,
            flicker_score=0.0,
            blink_rate_anomaly=False,
            diagnostics={"frames_analyzed": len(frames_bgr)},
        )

    flow_var = 0.0
    try:
        flow_var = _compute_optical_flow_variance(frames_bgr)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Optical flow failed: {exc}")

    flicker = 0.0
    try:
        flicker = _compute_flicker_score(frames_bgr)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Flicker score failed: {exc}")

    blink_anomaly, blink_intervals = False, []
    try:
        blink_anomaly, blink_intervals = _compute_blink_anomaly(frames_bgr, timestamps)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Blink rate analysis failed: {exc}")

    # Score composition
    # flow_var: real ~0–2; deepfake inconsistencies push higher → penalise
    flow_auth = max(0.0, 100.0 - min(100.0, flow_var * 15.0))
    flicker_auth = 100.0 - flicker
    blink_penalty = 20.0 if blink_anomaly else 0.0

    # Weights: 50% flow, 40% flicker, 10% blink
    raw = 0.50 * flow_auth + 0.40 * flicker_auth + 0.10 * (100.0 - blink_penalty)
    temporal_score = float(max(0.0, min(100.0, raw)))

    logger.info(
        f"Temporal: flow_var={flow_var:.4f} flicker={flicker:.1f} "
        f"blink_anomaly={blink_anomaly} → temporal_score={temporal_score:.1f}"
    )

    return TemporalAnalysis(
        temporal_score=round(temporal_score, 2),
        optical_flow_variance=round(flow_var, 4),
        flicker_score=round(flicker, 2),
        blink_rate_anomaly=blink_anomaly,
        blink_intervals=blink_intervals,
        diagnostics={
            "flow_component": round(flow_auth, 1),
            "flicker_component": round(flicker_auth, 1),
            "frames_analyzed": len(frames_bgr),
        },
    )
