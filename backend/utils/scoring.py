from __future__ import annotations

from typing import Tuple

TRUST_SCALE = [
    (0, 20, "Very Likely Fake", "critical"),
    (21, 40, "Likely Fake", "danger"),
    (41, 60, "Possibly Manipulated", "warning"),
    (61, 80, "Likely Real", "positive"),
    (81, 100, "Very Likely Real", "safe"),
]


def compute_authenticity_score(model_confidence: float, label: str) -> int:
    """Map (confidence, label) to 0-100 authenticity score.
    Real-ish labels give high score; fake-ish labels give low score.
    """
    label_l = label.lower()
    fake_tokens = ("fake", "deepfake", "manipulated", "ai", "generated", "synthetic")
    if any(tok in label_l for tok in fake_tokens):
        score = (1.0 - float(model_confidence)) * 100.0
    else:
        score = float(model_confidence) * 100.0
    return int(round(max(0.0, min(100.0, score))))


def get_verdict_label(score: int) -> Tuple[str, str]:
    for lo, hi, label, severity in TRUST_SCALE:
        if lo <= score <= hi:
            return label, severity
    return "Unknown", "warning"


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
