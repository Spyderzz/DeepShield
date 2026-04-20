from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from config import settings
from models.model_loader import get_model_loader
from services.image_service import _classify_vit


@dataclass
class FrameAnalysis:
    index: int
    timestamp_s: float
    label: str
    confidence: float
    suspicious_prob: float
    is_suspicious: bool
    has_face: bool = False
    scored: bool = False


@dataclass
class VideoAggregation:
    num_frames_sampled: int
    num_face_frames: int
    num_suspicious_frames: int
    mean_suspicious_prob: float
    max_suspicious_prob: float
    suspicious_ratio: float
    insufficient_faces: bool
    suspicious_timestamps: List[float] = field(default_factory=list)
    frames: List[FrameAnalysis] = field(default_factory=list)
    models_used: List[str] = field(default_factory=list)
    face_detector_used: str = "mediapipe"


FAKE_TOKENS = ("fake", "deepfake", "manipulated", "ai", "generated", "synthetic")


def _is_fake_label(label: str) -> bool:
    l = label.lower()
    return any(tok in l for tok in FAKE_TOKENS)


def extract_frames(video_path: str, num_frames: int = 16) -> List[Tuple[int, float, np.ndarray, Image.Image]]:
    """Uniformly sample num_frames frames from the video.
    Returns list of (frame_index, timestamp_seconds, bgr_numpy, PIL.Image).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if total <= 0:
        cap.release()
        raise RuntimeError("Video appears to have 0 frames")

    n = min(num_frames, total)
    indices = np.linspace(0, max(0, total - 1), num=n, dtype=int).tolist()

    out: List[Tuple[int, float, np.ndarray, Image.Image]] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame_bgr = cap.read()
        if not ok or frame_bgr is None:
            continue
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(frame_rgb)
        ts = (idx / fps) if fps > 0 else 0.0
        out.append((int(idx), float(ts), frame_bgr, pil))

    cap.release()
    logger.info(f"Extracted {len(out)}/{n} frames from video (total={total}, fps={fps:.2f})")
    return out


MIN_FACE_FRAMES = 3


def _has_face_mediapipe(pil: Image.Image) -> bool:
    detector = get_model_loader().load_face_detector()
    arr = np.array(pil)
    res = detector.process(arr)
    return bool(getattr(res, "multi_face_landmarks", None))


def _analyze_with_efficientnet(
    frames: List[Tuple[int, float, np.ndarray, Image.Image]],
) -> Tuple[List[FrameAnalysis], str, List[str]]:
    """Primary path: use EfficientNet + BlazeFace per-frame. Returns (frame_results, detector_used, models_used)."""
    loader = get_model_loader()
    eff = loader.load_efficientnet()

    if eff is None:
        logger.warning("EfficientNet unavailable — falling back to ViT video pipeline")
        return _analyze_with_vit(frames), "mediapipe", [settings.IMAGE_MODEL_ID]

    results: List[FrameAnalysis] = []
    face_detector_used = "blazeface"
    models_used = [f"{settings.EFFICIENTNET_MODEL}_{settings.EFFICIENTNET_TRAIN_DB}"]

    for idx, ts, frame_bgr, pil in frames:
        # Pass RGB to EfficientNet (process_image expects RGB array).
        frame_rgb = frame_bgr[..., ::-1].copy()
        frame_data = eff.face_extractor.process_image(img=frame_rgb)
        faces: list = frame_data.get("faces", [])
        has_face = bool(faces)

        if not has_face:
            # Fallback: check MediaPipe so we don't silently miss faces.
            has_face = _has_face_mediapipe(pil)
            if has_face:
                face_detector_used = "blazeface+mediapipe_fallback"

        fake_prob = 0.0
        label = "unknown"
        if has_face and faces:
            # Run EfficientNet on the best face from BlazeFace.
            face_t = eff._face_tensor(faces[0])
            import torch
            with torch.inference_mode():
                logit = eff.net(face_t.unsqueeze(0).to(eff.device))
                from scipy.special import expit
                fake_prob = float(expit(logit.cpu().numpy().item()))
            label = "Fake" if fake_prob > 0.5 else "Real"
        elif not has_face:
            label = "no_face"

        results.append(
            FrameAnalysis(
                index=idx,
                timestamp_s=ts,
                label=label,
                confidence=fake_prob,
                suspicious_prob=fake_prob,
                is_suspicious=(fake_prob >= 0.5) and has_face,
                has_face=has_face,
                scored=has_face,
            )
        )

    return results, face_detector_used, models_used


def _analyze_with_vit(
    frames: List[Tuple[int, float, np.ndarray, Image.Image]],
) -> List[FrameAnalysis]:
    """Fallback: original ViT-per-frame pipeline (MediaPipe face gate)."""
    results: List[FrameAnalysis] = []
    for idx, ts, _bgr, pil in frames:
        face = _has_face_mediapipe(pil)
        vit_fake_prob, vit_label, _ = _classify_vit(pil)
        results.append(
            FrameAnalysis(
                index=idx,
                timestamp_s=ts,
                label=vit_label,
                confidence=vit_fake_prob,
                suspicious_prob=vit_fake_prob,
                is_suspicious=(vit_fake_prob >= 0.5) and face,
                has_face=face,
                scored=face,
            )
        )
    return results


def aggregate(
    frame_results: List[FrameAnalysis],
    models_used: Optional[List[str]] = None,
    face_detector_used: str = "mediapipe",
) -> VideoAggregation:
    if not frame_results:
        return VideoAggregation(0, 0, 0, 0.0, 0.0, 0.0, True)

    scored = [f for f in frame_results if f.scored]
    num_face = len(scored)
    insufficient = num_face < MIN_FACE_FRAMES

    if insufficient:
        mean_p, max_p, susp_ratio = 0.0, 0.0, 0.0
        susp: List[FrameAnalysis] = []
    else:
        probs = [f.suspicious_prob for f in scored]
        susp = [f for f in scored if f.is_suspicious]
        mean_p = float(np.mean(probs))
        max_p = float(np.max(probs))
        susp_ratio = len(susp) / len(scored)

    return VideoAggregation(
        num_frames_sampled=len(frame_results),
        num_face_frames=num_face,
        num_suspicious_frames=len(susp) if not insufficient else 0,
        mean_suspicious_prob=mean_p,
        max_suspicious_prob=max_p,
        suspicious_ratio=susp_ratio,
        insufficient_faces=insufficient,
        suspicious_timestamps=[round(f.timestamp_s, 2) for f in (susp if not insufficient else [])],
        frames=frame_results,
        models_used=models_used or [settings.IMAGE_MODEL_ID],
        face_detector_used=face_detector_used,
    )


def analyze_video(video_path: str, num_frames: int = 16) -> VideoAggregation:
    frames = extract_frames(video_path, num_frames=num_frames)

    if settings.ENSEMBLE_MODE:
        frame_results, face_detector_used, models_used = _analyze_with_efficientnet(frames)
    else:
        frame_results = _analyze_with_vit(frames)
        face_detector_used = "mediapipe"
        models_used = [settings.IMAGE_MODEL_ID]

    return aggregate(frame_results, models_used=models_used, face_detector_used=face_detector_used)
