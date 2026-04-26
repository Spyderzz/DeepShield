from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import torch
from loguru import logger
from PIL import Image

from config import settings
from models.model_loader import get_model_loader
from schemas.common import ArtifactIndicator, ExifSummary, VLMBreakdown

_AI_TOKENS = ("ai", "artificial", "fake", "generated", "synthetic")
_REAL_TOKENS = ("real", "human", "natural", "photo", "authentic")


@dataclass
class GeneralImageDetection:
    fake_probability: float
    label: str
    all_scores: dict[str, float]
    model_used: str


@dataclass
class NoFaceFusion:
    fake_probability: float
    label: str
    method: str
    components: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)


def _fake_probability_from_scores(scores: dict[str, float]) -> float:
    ai_scores = [
        p for label, p in scores.items()
        if any(token in label.lower() for token in _AI_TOKENS)
    ]
    if ai_scores:
        return float(max(ai_scores))

    real_scores = [
        p for label, p in scores.items()
        if any(token in label.lower() for token in _REAL_TOKENS)
    ]
    if real_scores:
        return float(1.0 - max(real_scores))

    logger.warning(f"Could not infer AI-generated label from general image labels: {list(scores)}")
    return 0.5


def classify_general_image(pil_img: Image.Image) -> Optional[GeneralImageDetection]:
    loaded = get_model_loader().load_general_image_model()
    if loaded is None:
        return None
    model, processor = loaded

    inputs = processor(images=pil_img.convert("RGB"), return_tensors="pt")
    inputs = {k: v.to(settings.DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]

    id2label: dict[int, str] = getattr(model.config, "id2label", {})
    scores = {id2label.get(i, str(i)): float(p.item()) for i, p in enumerate(probs)}
    top_label = max(scores.items(), key=lambda kv: kv[1])[0] if scores else "unknown"
    return GeneralImageDetection(
        fake_probability=_fake_probability_from_scores(scores),
        label=top_label,
        all_scores=scores,
        model_used=settings.GENERAL_IMAGE_MODEL_ID,
    )


def _forensic_fake_probability(artifacts: list[ArtifactIndicator]) -> float:
    if not artifacts:
        return 0.5

    weighted: list[tuple[float, float]] = []
    for artifact in artifacts:
        weight = 1.0
        if artifact.type == "gan_artifact":
            weight = 1.25
        elif artifact.type == "compression":
            weight = 0.85
        elif artifact.type in {"facial_boundary", "lighting"}:
            weight = 0.60
        weighted.append((weight, float(artifact.confidence)))

    total_weight = sum(w for w, _ in weighted)
    if total_weight <= 0:
        return 0.5
    return max(0.0, min(1.0, sum(w * score for w, score in weighted) / total_weight))


def _exif_fake_probability(exif: ExifSummary | None) -> float:
    if exif is None or exif.trust_adjustment == 0:
        return 0.5
    # trust_adjustment is -12..12; positive means more fake, negative means more real.
    return max(0.0, min(1.0, 0.5 + (float(exif.trust_adjustment) / 24.0)))


def _vlm_fake_probability(vlm: VLMBreakdown | None) -> Optional[float]:
    if vlm is None:
        return None
    scores = [
        vlm.facial_symmetry.score,
        vlm.skin_texture.score,
        vlm.lighting_consistency.score,
        vlm.background_coherence.score,
        vlm.anatomy_hands_eyes.score,
        vlm.context_objects.score,
    ]
    authenticity = sum(float(s) for s in scores) / max(len(scores), 1)
    return max(0.0, min(1.0, 1.0 - authenticity / 100.0))


def fuse_no_face_evidence(
    *,
    general_fake_prob: float | None,
    artifacts: list[ArtifactIndicator],
    exif: ExifSummary | None,
    vlm: VLMBreakdown | None = None,
) -> NoFaceFusion:
    components = {
        "general_detector": 0.5 if general_fake_prob is None else max(0.0, min(1.0, float(general_fake_prob))),
        "forensics": _forensic_fake_probability(artifacts),
        "exif": _exif_fake_probability(exif),
    }

    weights = {
        "general_detector": settings.NOFACE_GENERAL_WEIGHT,
        "forensics": settings.NOFACE_FORENSICS_WEIGHT,
        "exif": settings.NOFACE_EXIF_WEIGHT,
    }

    vlm_prob = _vlm_fake_probability(vlm)
    if vlm_prob is not None:
        components["vlm_consistency"] = vlm_prob
        weights["vlm_consistency"] = settings.NOFACE_VLM_WEIGHT

    total_weight = sum(weights.values())
    if total_weight <= 0:
        fake_prob = components["general_detector"]
    else:
        fake_prob = sum(components[k] * weights[k] for k in weights) / total_weight
    fake_prob = max(0.0, min(1.0, fake_prob))

    return NoFaceFusion(
        fake_probability=fake_prob,
        label="Fake" if fake_prob >= 0.5 else "Real",
        method="no_face_general_forensic_fusion",
        components=components,
        weights=weights,
    )
