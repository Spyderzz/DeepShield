from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from models.model_loader import get_model_loader
from services.image_service import classify_image


@dataclass
class FrameAnalysis:
    index: int
    timestamp_s: float
    label: str
    confidence: float
    suspicious_prob: float  # prob of the fake/manipulated class
    is_suspicious: bool
    has_face: bool = False
    scored: bool = False  # contributed to aggregate (face frames only)


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


FAKE_TOKENS = ("fake", "deepfake", "manipulated", "ai", "generated", "synthetic")


def _is_fake_label(label: str) -> bool:
    l = label.lower()
    return any(tok in l for tok in FAKE_TOKENS)


def extract_frames(video_path: str, num_frames: int = 16) -> List[Tuple[int, float, Image.Image]]:
    """Uniformly sample num_frames frames from the video. Returns list of
    (frame_index, timestamp_seconds, PIL.Image).
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

    out: List[Tuple[int, float, Image.Image]] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame_bgr = cap.read()
        if not ok or frame_bgr is None:
            continue
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(frame_rgb)
        ts = (idx / fps) if fps > 0 else 0.0
        out.append((int(idx), float(ts), pil))

    cap.release()
    logger.info(f"Extracted {len(out)}/{n} frames from video (total={total}, fps={fps:.2f})")
    return out


MIN_FACE_FRAMES = 3  # below this we refuse to issue a deepfake verdict


def _has_face(pil: Image.Image) -> bool:
    detector = get_model_loader().load_face_detector()
    arr = np.array(pil)
    res = detector.process(arr)
    return bool(getattr(res, "multi_face_landmarks", None))


def classify_frames(frames: List[Tuple[int, float, Image.Image]]) -> List[FrameAnalysis]:
    results: List[FrameAnalysis] = []
    for idx, ts, pil in frames:
        face = _has_face(pil)
        clf = classify_image(pil)
        fake_prob = 0.0
        for lbl, p in clf.all_scores.items():
            if _is_fake_label(lbl):
                fake_prob = max(fake_prob, float(p))
        results.append(
            FrameAnalysis(
                index=idx,
                timestamp_s=ts,
                label=clf.label,
                confidence=clf.confidence,
                suspicious_prob=fake_prob,
                is_suspicious=(fake_prob >= 0.5) and face,
                has_face=face,
                scored=face,
            )
        )
    return results


def aggregate(frames: List[FrameAnalysis]) -> VideoAggregation:
    if not frames:
        return VideoAggregation(0, 0, 0, 0.0, 0.0, 0.0, True)

    scored = [f for f in frames if f.scored]
    num_face = len(scored)
    insufficient = num_face < MIN_FACE_FRAMES

    if insufficient:
        mean_p = 0.0
        max_p = 0.0
        susp_ratio = 0.0
        susp: List[FrameAnalysis] = []
    else:
        probs = [f.suspicious_prob for f in scored]
        susp = [f for f in scored if f.is_suspicious]
        mean_p = float(np.mean(probs))
        max_p = float(np.max(probs))
        susp_ratio = len(susp) / len(scored)

    return VideoAggregation(
        num_frames_sampled=len(frames),
        num_face_frames=num_face,
        num_suspicious_frames=len(susp),
        mean_suspicious_prob=mean_p,
        max_suspicious_prob=max_p,
        suspicious_ratio=susp_ratio,
        insufficient_faces=insufficient,
        suspicious_timestamps=[round(f.timestamp_s, 2) for f in susp],
        frames=frames,
    )


def analyze_video(video_path: str, num_frames: int = 16) -> VideoAggregation:
    frames = extract_frames(video_path, num_frames=num_frames)
    classified = classify_frames(frames)
    return aggregate(classified)
