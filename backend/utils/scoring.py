from __future__ import annotations

from typing import Tuple

TRUST_SCALE = [
    (0, 20, "Very Likely Fake", "critical"),
    (21, 40, "Likely Fake", "danger"),
    (41, 60, "Possibly Manipulated", "warning"),
    (61, 80, "Likely Real", "positive"),
    (81, 100, "Very Likely Real", "safe"),
]


def compute_authenticity_score(fake_probability: float, label: str = "") -> int:
    """Map a fake probability [0.0, 1.0] to a 0-100 authenticity score.

    The first argument must always be the model's fake-probability (not the
    top-label confidence). 0.0 (no fake signal) → 100, 1.0 (certain fake) → 0.

    The `label` parameter is accepted for backward compatibility but not used.
    """
    return int(round(max(0.0, min(100.0, (1.0 - float(fake_probability)) * 100.0))))


def get_verdict_label(score: int) -> Tuple[str, str]:
    for lo, hi, label, severity in TRUST_SCALE:
        if lo <= score <= hi:
            return label, severity
    return "Unknown", "warning"


def compute_video_authenticity_score(
    *,
    mean_suspicious_prob: float,
    insufficient_faces: bool,
    temporal_score: float | None = None,
    audio_authenticity_score: float | None = None,
    has_audio: bool = False,
) -> Tuple[int, str, str]:
    """Combine video evidence into an authenticity verdict.

    Face-model evidence is authoritative only when enough face frames were
    scored. If face content is insufficient, use temporal/audio evidence when
    available instead of forcing a neutral result.
    """
    if insufficient_faces:
        evidence: list[tuple[float, float]] = []
        if temporal_score is not None:
            evidence.append((0.60, float(temporal_score)))
        if has_audio and audio_authenticity_score is not None:
            evidence.append((0.40, float(audio_authenticity_score)))

        if not evidence:
            return 50, "Insufficient face content", "warning"

        total_weight = sum(weight for weight, _score in evidence)
        combined = sum(weight * score for weight, score in evidence) / total_weight
        score = int(round(max(0.0, min(100.0, combined))))
        label, severity = get_verdict_label(score)
        return score, label, severity

    visual_score = (1.0 - float(mean_suspicious_prob)) * 100.0
    temporal_sc = float(temporal_score) if temporal_score is not None else visual_score
    if has_audio and audio_authenticity_score is not None:
        combined = 0.50 * visual_score + 0.30 * temporal_sc + 0.20 * float(audio_authenticity_score)
    else:
        combined = 0.70 * visual_score + 0.30 * temporal_sc
    score = int(round(max(0.0, min(100.0, combined))))
    label, severity = get_verdict_label(score)
    return score, label, severity


def get_score_color(score: int) -> str:
    """Linear interpolate Red (#E53935) → Amber (#FFA726) → Green (#43A047)."""
    def lerp(a: int, b: int, t: float) -> int:
        return int(round(a + (b - a) * t))

    score = max(0, min(100, score))
    if score <= 50:
        t = score / 50.0
        r, g, b = lerp(0xE5, 0xFF, t), lerp(0x39, 0xA7, t), lerp(0x35, 0x26, t)
    else:
        t = (score - 50) / 50.0
        r, g, b = lerp(0xFF, 0x43, t), lerp(0xA7, 0xA0, t), lerp(0x26, 0x47, t)
    return f"#{r:02X}{g:02X}{b:02X}"
