from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import torch
from loguru import logger
from PIL import Image

from config import settings
from models.model_loader import get_model_loader


@dataclass
class ImageClassification:
    label: str
    confidence: float
    all_scores: dict[str, float]
    models_used: List[str] = field(default_factory=list)
    ensemble_method: Optional[str] = None


def load_image_from_bytes(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _classify_vit(pil_img: Image.Image) -> Tuple[float, str, dict[str, float]]:
    """Run the ViT deepfake classifier. Returns (fake_prob, top_label, all_scores)."""
    loader = get_model_loader()
    model, processor = loader.load_image_model()

    inputs = processor(images=pil_img, return_tensors="pt")
    inputs = {k: v.to(settings.DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)[0]

    id2label: dict[int, str] = getattr(model.config, "id2label", {})
    all_scores = {id2label.get(i, str(i)): float(p.item()) for i, p in enumerate(probs)}
    top_idx = int(torch.argmax(probs).item())
    top_label = id2label.get(top_idx, str(top_idx))

    # Identify the fake probability — pick the highest score from fake-labelled classes.
    fake_tokens = ("fake", "deepfake", "manipulated", "ai", "generated", "synthetic")
    fake_prob = max(
        (float(p) for lbl, p in all_scores.items() if any(t in lbl.lower() for t in fake_tokens)),
        default=float(probs[top_idx].item()),
    )
    return fake_prob, top_label, all_scores


def classify_image(pil_img: Image.Image) -> ImageClassification:
    """Run deepfake classification. Uses ensemble (ViT + EfficientNet) when ENSEMBLE_MODE=true,
    falls back to ViT-only when EfficientNet is unavailable or ENSEMBLE_MODE=false.
    """
    vit_fake_prob, vit_label, vit_scores = _classify_vit(pil_img)
    models_used = [settings.IMAGE_MODEL_ID]

    if not settings.ENSEMBLE_MODE:
        logger.info(f"Image classify (ViT-only) → {vit_label} @ fake_p={vit_fake_prob:.3f}")
        label = "Fake" if vit_fake_prob >= 0.5 else "Real"
        return ImageClassification(
            label=label,
            confidence=vit_fake_prob,
            all_scores=vit_scores,
            models_used=models_used,
            ensemble_method=None,
        )

    # Attempt EfficientNet inference.
    loader = get_model_loader()
    eff_detector = loader.load_efficientnet()
    if eff_detector is None:
        logger.warning("EfficientNet unavailable — falling back to ViT-only")
        label = "Fake" if vit_fake_prob >= 0.5 else "Real"
        return ImageClassification(
            label=label,
            confidence=vit_fake_prob,
            all_scores=vit_scores,
            models_used=models_used,
            ensemble_method=None,
        )

    eff_result = eff_detector.detect_image(pil_img)
    if eff_result.get("error") or eff_result.get("score") is None:
        # BlazeFace found no face — trust ViT alone.
        logger.info(f"EfficientNet no-face fallback → using ViT score {vit_fake_prob:.3f}")
        label = "Fake" if vit_fake_prob >= 0.5 else "Real"
        return ImageClassification(
            label=label,
            confidence=vit_fake_prob,
            all_scores=vit_scores,
            models_used=models_used,
            ensemble_method="vit_only_no_face",
        )

    eff_fake_prob: float = eff_result["score"]
    models_used.append(eff_result["model"])

    # Simple average ensemble.
    ensemble_prob = (vit_fake_prob + eff_fake_prob) / 2.0
    label = "Fake" if ensemble_prob >= 0.5 else "Real"
    logger.info(
        f"Image classify (ensemble) → {label} | vit={vit_fake_prob:.3f} eff={eff_fake_prob:.3f} avg={ensemble_prob:.3f}"
    )
    return ImageClassification(
        label=label,
        confidence=ensemble_prob,
        all_scores={
            **{f"vit_{k}": v for k, v in vit_scores.items()},
            f"efficientnet_fake": eff_fake_prob,
            f"efficientnet_real": 1.0 - eff_fake_prob,
        },
        models_used=models_used,
        ensemble_method="average",
    )


def preprocess_and_classify(raw_bytes: bytes) -> Tuple[Image.Image, ImageClassification]:
    """Convenience: decode bytes → PIL → classify. Returns the PIL image too so
    downstream steps (heatmap, artifact scan) can reuse it.
    """
    pil = load_image_from_bytes(raw_bytes)
    result = classify_image(pil)
    return pil, result
