from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Tuple

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


def load_image_from_bytes(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def classify_image(pil_img: Image.Image) -> ImageClassification:
    """Run the ViT deepfake classifier on a PIL image."""
    loader = get_model_loader()
    model, processor = loader.load_image_model()

    inputs = processor(images=pil_img, return_tensors="pt")
    inputs = {k: v.to(settings.DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits  # (1, num_labels)
        probs = torch.softmax(logits, dim=-1)[0]

    id2label: dict[int, str] = getattr(model.config, "id2label", {})
    all_scores = {id2label.get(i, str(i)): float(p.item()) for i, p in enumerate(probs)}
    top_idx = int(torch.argmax(probs).item())
    top_label = id2label.get(top_idx, str(top_idx))
    top_conf = float(probs[top_idx].item())

    logger.info(f"Image classify → {top_label} @ {top_conf:.3f}")
    return ImageClassification(label=top_label, confidence=top_conf, all_scores=all_scores)


def preprocess_and_classify(raw_bytes: bytes) -> Tuple[Image.Image, ImageClassification]:
    """Convenience: decode bytes → PIL → classify. Returns the PIL image too so
    downstream steps (heatmap, artifact scan) can reuse it.
    """
    pil = load_image_from_bytes(raw_bytes)
    result = classify_image(pil)
    return pil, result
