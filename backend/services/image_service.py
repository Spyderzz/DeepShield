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


def _classify_ffpp(pil_img: Image.Image) -> Optional[Tuple[float, dict[str, float]]]:
    """Run the FFPP-fine-tuned ViT (Phase 11.3). Returns (fake_prob, all_scores) or None."""
    loader = get_model_loader()
    loaded = loader.load_ffpp_model()
    if loaded is None:
        return None
    model, processor = loaded

    inputs = processor(images=pil_img, return_tensors="pt")
    inputs = {k: v.to(settings.DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]

    id2label: dict[int, str] = getattr(model.config, "id2label", {0: "fake", 1: "real"})
    all_scores = {id2label.get(i, str(i)): float(p.item()) for i, p in enumerate(probs)}
    fake_prob = next(
        (float(v) for k, v in all_scores.items() if k.lower() == "fake"),
        float(probs[0].item()),
    )
    return fake_prob, all_scores


def classify_image(pil_img: Image.Image) -> ImageClassification:
    """Run deepfake classification. Weighted ensemble across:
      - FFPP-fine-tuned ViT (Phase 11.3, face-trained) — highest weight when present
      - EfficientNetAutoAttB4 (face-gated DFDC model)
      - Generic ViT (prithivMLmods)
    Falls back gracefully when individual models are unavailable.
    """
    vit_fake_prob, vit_label, vit_scores = _classify_vit(pil_img)
    models_used = [settings.IMAGE_MODEL_ID]
    scores_out: dict[str, float] = {f"vit_{k}": v for k, v in vit_scores.items()}

    # FFPP inference (may be None if disabled / checkpoint missing).
    ffpp_fake_prob: Optional[float] = None
    ffpp_res = _classify_ffpp(pil_img) if settings.FFPP_ENABLED else None
    if ffpp_res is not None:
        ffpp_fake_prob, ffpp_scores = ffpp_res
        models_used.append("ffpp-vit-local")
        scores_out.update({f"ffpp_{k}": v for k, v in ffpp_scores.items()})

    if not settings.ENSEMBLE_MODE:
        # ViT-only mode, but still blend FFPP when available — it's strictly better.
        if ffpp_fake_prob is not None:
            combined = 0.4 * vit_fake_prob + 0.6 * ffpp_fake_prob
            method = "ffpp_vit_blend"
        else:
            combined = vit_fake_prob
            method = None
        label = "Fake" if combined >= 0.5 else "Real"
        logger.info(f"Image classify (ensemble-off) → {label} @ {combined:.3f}")
        return ImageClassification(
            label=label, confidence=combined, all_scores=scores_out,
            models_used=models_used, ensemble_method=method,
        )

    # EfficientNet inference (face-gated).
    loader = get_model_loader()
    eff_detector = loader.load_efficientnet()
    eff_fake_prob: Optional[float] = None
    face_present = False
    if eff_detector is not None:
        eff_result = eff_detector.detect_image(pil_img)
        if not eff_result.get("error") and eff_result.get("score") is not None:
            eff_fake_prob = float(eff_result["score"])
            face_present = True
            models_used.append(eff_result["model"])
            scores_out["efficientnet_fake"] = eff_fake_prob
            scores_out["efficientnet_real"] = 1.0 - eff_fake_prob

    # Weighted ensemble
    if face_present and eff_fake_prob is not None and ffpp_fake_prob is not None:
        w_ffpp = settings.FFPP_WEIGHT_FACE
        w_vit = settings.VIT_WEIGHT_FACE
        w_eff = settings.EFFNET_WEIGHT_FACE
        total = w_ffpp + w_vit + w_eff
        ensemble_prob = (w_ffpp * ffpp_fake_prob + w_vit * vit_fake_prob + w_eff * eff_fake_prob) / total
        method = "weighted_ffpp_vit_eff"
    elif face_present and eff_fake_prob is not None:
        ensemble_prob = 0.5 * vit_fake_prob + 0.5 * eff_fake_prob
        method = "average_vit_eff"
    elif ffpp_fake_prob is not None:
        w_ffpp = settings.FFPP_WEIGHT_NOFACE
        w_vit = settings.VIT_WEIGHT_NOFACE
        total = w_ffpp + w_vit
        ensemble_prob = (w_ffpp * ffpp_fake_prob + w_vit * vit_fake_prob) / total
        method = "weighted_ffpp_vit_no_face"
    else:
        ensemble_prob = vit_fake_prob
        method = "vit_only"

    label = "Fake" if ensemble_prob >= 0.5 else "Real"
    logger.info(
        f"Image classify ({method}) → {label} | vit={vit_fake_prob:.3f} "
        f"ffpp={ffpp_fake_prob if ffpp_fake_prob is not None else 'n/a'} "
        f"eff={eff_fake_prob if eff_fake_prob is not None else 'n/a'} "
        f"→ {ensemble_prob:.3f}"
    )
    return ImageClassification(
        label=label,
        confidence=ensemble_prob,
        all_scores=scores_out,
        models_used=models_used,
        ensemble_method=method,
    )


def preprocess_and_classify(raw_bytes: bytes) -> Tuple[Image.Image, ImageClassification]:
    """Convenience: decode bytes → PIL → classify. Returns the PIL image too so
    downstream steps (heatmap, artifact scan) can reuse it.
    """
    pil = load_image_from_bytes(raw_bytes)
    result = classify_image(pil)
    return pil, result
