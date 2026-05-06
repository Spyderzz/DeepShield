from __future__ import annotations

import math
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


def _temperature_scale(prob: float, temperature: float) -> float:
    """Apply temperature scaling to a probability via logit space.

    temperature > 1.0 → softer (less confident), < 1.0 → sharper.
    Temperature 1.0 is a no-op.
    """
    if abs(temperature - 1.0) < 1e-6:
        return prob
    prob = max(1e-7, min(1.0 - 1e-7, prob))
    logit = math.log(prob / (1.0 - prob))
    scaled_logit = logit / temperature
    return 1.0 / (1.0 + math.exp(-scaled_logit))


def _run_image_classifier(
    pil_img: Image.Image,
    model,
    processor,
    temperature: float = 1.0,
) -> tuple[float, str, dict[str, float]]:
    """Run a HuggingFace image-classification model and return (fake_prob, top_label, all_scores)."""
    inputs = processor(images=pil_img.convert("RGB"), return_tensors="pt")
    inputs = {k: v.to(settings.DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]

    id2label: dict[int, str] = getattr(model.config, "id2label", {})
    scores = {id2label.get(i, str(i)): float(p.item()) for i, p in enumerate(probs)}
    top_label = max(scores.items(), key=lambda kv: kv[1])[0] if scores else "unknown"
    raw_fake_prob = _fake_probability_from_scores(scores)
    scaled_fake_prob = _temperature_scale(raw_fake_prob, temperature)
    return scaled_fake_prob, top_label, scores


def classify_general_image(pil_img: Image.Image) -> Optional[GeneralImageDetection]:
    """Run the general AI-image detector (umm-maybe/AI-image-detector).

    Phase C2: when the diffusion detector is also available, the two heads are
    ensembled using GENERAL_AI_WEIGHT / DIFFUSION_AI_WEIGHT. This gives the
    system independent evidence from two detectors trained on different AI-image
    distributions (general/GAN vs diffusion/SDXL).
    """
    loader = get_model_loader()
    loaded = loader.load_general_image_model()
    if loaded is None:
        # Try falling back to diffusion detector alone
        return _classify_diffusion_only(pil_img)

    model, processor = loaded
    gen_fake_prob, gen_top_label, gen_scores = _run_image_classifier(
        pil_img, model, processor, temperature=settings.GENERAL_MODEL_TEMPERATURE
    )

    # Phase C2: load second head and ensemble when available
    diff_loaded = loader.load_diffusion_image_model()
    if diff_loaded is not None:
        diff_model, diff_processor = diff_loaded
        diff_fake_prob, diff_top_label, diff_scores = _run_image_classifier(
            pil_img, diff_model, diff_processor, temperature=settings.DIFFUSION_MODEL_TEMPERATURE
        )
        w_gen = settings.GENERAL_AI_WEIGHT
        w_diff = settings.DIFFUSION_AI_WEIGHT
        total = w_gen + w_diff
        blended_fake_prob = (w_gen * gen_fake_prob + w_diff * diff_fake_prob) / total

        # Top label is taken from the higher-confidence head
        top_label = gen_top_label if gen_fake_prob >= diff_fake_prob else diff_top_label

        combined_scores = {f"gen_{k}": v for k, v in gen_scores.items()}
        combined_scores.update({f"diff_{k}": v for k, v in diff_scores.items()})
        combined_scores["blended_fake_prob"] = blended_fake_prob

        model_used = f"{settings.GENERAL_IMAGE_MODEL_ID}+{settings.DIFFUSION_IMAGE_MODEL_ID}"
        logger.debug(
            f"General AI ensemble: gen={gen_fake_prob:.3f} diff={diff_fake_prob:.3f} "
            f"-> blended={blended_fake_prob:.3f}"
        )
        return GeneralImageDetection(
            fake_probability=blended_fake_prob,
            label=top_label,
            all_scores=combined_scores,
            model_used=model_used,
        )

    return GeneralImageDetection(
        fake_probability=gen_fake_prob,
        label=gen_top_label,
        all_scores=gen_scores,
        model_used=settings.GENERAL_IMAGE_MODEL_ID,
    )


def _classify_diffusion_only(pil_img: Image.Image) -> Optional[GeneralImageDetection]:
    """Fallback: run only the diffusion detector when the general model is unavailable."""
    loader = get_model_loader()
    diff_loaded = loader.load_diffusion_image_model()
    if diff_loaded is None:
        return None
    diff_model, diff_processor = diff_loaded
    diff_fake_prob, diff_top_label, diff_scores = _run_image_classifier(
        pil_img, diff_model, diff_processor, temperature=settings.DIFFUSION_MODEL_TEMPERATURE
    )
    return GeneralImageDetection(
        fake_probability=diff_fake_prob,
        label=diff_top_label,
        all_scores=diff_scores,
        model_used=settings.DIFFUSION_IMAGE_MODEL_ID,
    )


def _forensic_fake_probability(
    artifacts: list[ArtifactIndicator],
    *,
    is_video_frame: bool = False,
) -> float:
    if not artifacts:
        return 0.5

    weighted: list[tuple[float, float]] = []
    for artifact in artifacts:
        weight = 1.0
        if artifact.type == "gan_artifact":
            weight = 1.25
        elif artifact.type == "compression":
            # Video frames always have compression artifacts regardless of
            # authenticity — halve the weight so they don't inflate fake prob.
            weight = 0.40 if is_video_frame else 0.85
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
