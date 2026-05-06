"""DenseNet121 face-GAN inference service.

The model outputs a sigmoid real_probability in [0, 1].
Threshold (from training) is 0.7597 (Youden's J on val ROC):
  score >= threshold → Real,  score < threshold → Fake.

fake_prob is mapped with a piecewise-linear calibration anchored so that:
  score = 1.0      → fake_prob = 0.0   (confident real)
  score = threshold → fake_prob = 0.5  (decision boundary)
  score = 0.0      → fake_prob = 1.0   (confident fake)
This respects the trained threshold without needing an extra isotonic fit.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tvm
from loguru import logger
from PIL import Image


# ── Model architecture (must match convert_densenet_keras_to_pt.py) ──────────
class _FakeHead(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.fc1  = nn.Linear(1024, 256)
        self.relu = nn.ReLU(inplace=True)
        self.bn   = nn.BatchNorm1d(256)
        self.drop = nn.Dropout(0.3)
        self.fc2  = nn.Linear(256, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(self.drop(self.bn(self.relu(self.fc1(x)))))


class DenseNetFaces(nn.Module):
    """DenseNet121 + custom head for face-GAN binary detection."""

    def __init__(self) -> None:
        super().__init__()
        base = tvm.densenet121(weights=None)
        self.features = base.features
        self.head     = _FakeHead()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = torch.nn.functional.relu(self.features(x), inplace=True)
        feat = torch.nn.functional.adaptive_avg_pool2d(feat, (1, 1))
        feat = torch.flatten(feat, 1)
        return self.head(feat)   # (B, 1) raw logit


# ── Preprocessing ─────────────────────────────────────────────────────────────
_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
_STD  = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)


def _preprocess(pil_img: Image.Image, image_size: int, device: str) -> torch.Tensor:
    img = pil_img.convert("RGB").resize((image_size, image_size), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0          # (H, W, 3) → [0, 1]
    t   = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)  # (1, 3, H, W)
    mean = _MEAN.to(device)
    std  = _STD.to(device)
    return (t.to(device) - mean) / std


# ── Calibrated fake_prob ──────────────────────────────────────────────────────
def _calibrated_fake_prob(score_real: float, threshold: float) -> float:
    """Piecewise-linear map: score=threshold → 0.5, score=1 → 0, score=0 → 1."""
    if score_real >= threshold:
        return 0.5 * (1.0 - score_real) / max(1.0 - threshold, 1e-8)
    else:
        return 0.5 + 0.5 * (threshold - score_real) / max(threshold, 1e-8)


# ── Public inference entry point ──────────────────────────────────────────────
def detect_image(
    pil_img: Image.Image,
    model: DenseNetFaces,
    meta: dict,
    device: str = "cpu",
) -> dict:
    """Run DenseNet121 inference on a PIL image.

    Returns:
        score_real  – raw sigmoid output in [0, 1]
        fake_prob   – calibrated fake probability in [0, 1]
        threshold   – Youden's J threshold used for binary verdict
        label       – "Real" or "Fake" based on threshold
    """
    threshold  = float(meta.get("threshold", 0.7597))
    image_size = int(meta.get("image_size", 224))

    tensor = _preprocess(pil_img, image_size, device)

    with torch.no_grad():
        logit      = model(tensor)
        score_real = float(torch.sigmoid(logit).item())

    fake_prob = _calibrated_fake_prob(score_real, threshold)
    label     = "Real" if score_real >= threshold else "Fake"

    return {
        "score_real": score_real,
        "fake_prob":  fake_prob,
        "threshold":  threshold,
        "label":      label,
    }
