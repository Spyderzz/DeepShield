from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch
from loguru import logger
from PIL import Image

from config import settings
from models.model_loader import get_model_loader
from schemas.common import ArtifactIndicator, ExifSummary, VLMBreakdown
from services.general_image_service import classify_general_image, fuse_no_face_evidence


@dataclass
class ImageClassification:
    label: str
    confidence: float
    all_scores: dict[str, float]
    models_used: List[str] = field(default_factory=list)
    ensemble_method: Optional[str] = None
    calibrator_applied: bool = False
    no_face_analysis: Optional[dict] = None


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


def _crop_face_for_face_model(pil_img: Image.Image) -> Image.Image:
    """Best-effort face crop for FFPP-style classifiers trained on face crops."""
    rgb = np.asarray(pil_img.convert("RGB"))
    h, w = rgb.shape[:2]

    def crop(x0: int, y0: int, x1: int, y1: int, margin: float = 0.24) -> Image.Image:
        bw = max(1, x1 - x0)
        bh = max(1, y1 - y0)
        pad = int(max(bw, bh) * margin)
        x0c = max(0, x0 - pad)
        y0c = max(0, y0 - pad)
        x1c = min(w, x1 + pad)
        y1c = min(h, y1 + pad)
        if x1c <= x0c + 8 or y1c <= y0c + 8:
            return pil_img
        return Image.fromarray(rgb[y0c:y1c, x0c:x1c])

    try:
        from models.model_loader import get_model_loader

        detector = get_model_loader().load_face_detector()
        result = detector.process(rgb) if detector is not None else None
        if result is not None and getattr(result, "multi_face_landmarks", None):
            landmarks = result.multi_face_landmarks[0].landmark
            xs = [lm.x * w for lm in landmarks]
            ys = [lm.y * h for lm in landmarks]
            return crop(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"FFPP MediaPipe face crop failed: {exc}")

    try:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(32, 32))
        if len(faces) > 0:
            x, y, fw, fh = max(faces, key=lambda box: box[2] * box[3])
            return crop(int(x), int(y), int(x + fw), int(y + fh))
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"FFPP OpenCV face crop failed: {exc}")

    return pil_img


def _classify_ffpp(pil_img: Image.Image) -> Optional[Tuple[float, dict[str, float]]]:
    """Run the FFPP-fine-tuned ViT (Phase 11.3). Returns (fake_prob, all_scores) or None."""
    loader = get_model_loader()
    loaded = loader.load_ffpp_model()
    if loaded is None:
        return None
    model, processor = loaded

    face_img = _crop_face_for_face_model(pil_img)
    inputs = processor(images=face_img, return_tensors="pt")
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


def _has_face_for_routing(pil_img: Image.Image) -> bool:
    rgb = np.asarray(pil_img.convert("RGB"))
    try:
        detector = get_model_loader().load_face_detector()
        result = detector.process(rgb) if detector is not None else None
        if result is not None and getattr(result, "multi_face_landmarks", None):
            return True
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"MediaPipe face route check failed: {exc}")

    try:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(32, 32))
        return len(faces) > 0
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"OpenCV face route check failed: {exc}")
        return False


def _classify_no_face(
    pil_img: Image.Image,
    *,
    artifact_indicators: Optional[list[ArtifactIndicator]] = None,
    exif: ExifSummary | None = None,
    vlm_breakdown: VLMBreakdown | None = None,
) -> ImageClassification:
    general = classify_general_image(pil_img)
    fused = fuse_no_face_evidence(
        general_fake_prob=general.fake_probability if general else None,
        artifacts=artifact_indicators or [],
        exif=exif,
        vlm=vlm_breakdown,
    )
    scores = {
        f"no_face_{name}": score
        for name, score in fused.components.items()
    }
    scores.update({
        f"no_face_weight_{name}": weight
        for name, weight in fused.weights.items()
    })
    if general is not None:
        scores.update({f"general_{k}": v for k, v in general.all_scores.items()})

    analysis = {
        "method": fused.method,
        "components": fused.components,
        "weights": fused.weights,
        "general_model": general.model_used if general else None,
        "general_label": general.label if general else "unavailable",
        "general_unavailable": general is None,
    }
    models_used = [general.model_used if general else "no-face-forensic-fusion"]
    return ImageClassification(
        label=fused.label,
        confidence=fused.fake_probability,
        all_scores=scores,
        models_used=models_used,
        ensemble_method=fused.method,
        no_face_analysis=analysis,
    )


def classify_image(
    pil_img: Image.Image,
    *,
    artifact_indicators: Optional[list[ArtifactIndicator]] = None,
    exif: ExifSummary | None = None,
    vlm_breakdown: VLMBreakdown | None = None,
) -> ImageClassification:
    """Run deepfake classification. Weighted ensemble across:
      - FFPP-fine-tuned ViT (Phase 11.3, face-trained) — highest weight when present
      - EfficientNetAutoAttB4 (face-gated DFDC model)
      - Generic ViT (prithivMLmods)
    Falls back gracefully when individual models are unavailable.
    """
    face_present_for_route = _has_face_for_routing(pil_img)
    if not face_present_for_route and settings.ENSEMBLE_MODE:
        result = _classify_no_face(
            pil_img,
            artifact_indicators=artifact_indicators,
            exif=exif,
            vlm_breakdown=vlm_breakdown,
        )
        logger.info(
            f"Image classify ({result.ensemble_method}) â†’ {result.label} "
            f"@ {result.confidence:.3f}"
        )
        return result

    vit_fake_prob, vit_label, vit_scores = _classify_vit(pil_img)
    models_used = [settings.IMAGE_MODEL_ID]
    scores_out: dict[str, float] = {f"vit_{k}": v for k, v in vit_scores.items()}

    # FFPP inference (may be None if disabled / checkpoint missing).
    ffpp_fake_prob: Optional[float] = None
    ffpp_res = _classify_ffpp(pil_img) if settings.FFPP_ENABLED and face_present_for_route else None
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
    face_present = face_present_for_route
    if eff_detector is not None:
        eff_result = eff_detector.detect_image(pil_img)
        if not eff_result.get("error") and eff_result.get("score") is not None:
            eff_fake_prob = float(eff_result["score"])
            face_present = True
            models_used.append(eff_result["model"])
            scores_out["efficientnet_fake"] = eff_fake_prob
            scores_out["efficientnet_real"] = 1.0 - eff_fake_prob
            scores_out["efficientnet_calibrator_applied"] = 1.0 if eff_result.get("calibrator_applied") else 0.0

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
    else:
        ensemble_prob = vit_fake_prob
        method = "vit_only_no_face"

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
        calibrator_applied=bool(scores_out.get("efficientnet_calibrator_applied", 0.0)),
    )


def preprocess_and_classify(raw_bytes: bytes) -> Tuple[Image.Image, ImageClassification]:
    """Convenience: decode bytes → PIL → classify. Returns the PIL image too so
    downstream steps (heatmap, artifact scan) can reuse it.
    """
    pil = load_image_from_bytes(raw_bytes)
    result = classify_image(pil)
    return pil, result
