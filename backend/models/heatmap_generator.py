from __future__ import annotations

import base64
import io
from typing import Optional

import cv2
import numpy as np
import torch
from loguru import logger
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

from config import settings
from models.model_loader import get_model_loader


def _vit_reshape_transform(tensor: torch.Tensor, height: int = 14, width: int = 14) -> torch.Tensor:
    """Grad-CAM expects (B, C, H, W); ViT hidden states are (B, 1+H*W, C).
    Drop the CLS token and reshape tokens into a spatial grid.
    """
    # tensor: (B, 197, C) for 224/16 ViT
    result = tensor[:, 1:, :]
    b, n, c = result.shape
    result = result.reshape(b, height, width, c)
    result = result.permute(0, 3, 1, 2)  # (B, C, H, W)
    return result


def _preprocess_for_cam(pil_img: Image.Image, processor) -> tuple[torch.Tensor, np.ndarray]:
    """Return (input_tensor, rgb_float_224) where rgb_float_224 is a (H,W,3) float
    array in [0,1] matching the model input geometry — needed for overlaying.
    """
    inputs = processor(images=pil_img, return_tensors="pt")
    input_tensor = inputs["pixel_values"].to(settings.DEVICE)

    size = getattr(processor, "size", {"height": 224, "width": 224})
    h = size.get("height", 224) if isinstance(size, dict) else 224
    w = size.get("width", 224) if isinstance(size, dict) else 224

    resized = pil_img.resize((w, h), Image.BILINEAR)
    rgb = np.array(resized).astype(np.float32) / 255.0  # (H,W,3) in [0,1]
    return input_tensor, rgb


def generate_heatmap_base64(
    pil_img: Image.Image,
    target_class_idx: Optional[int] = None,
) -> str:
    """Produce a base64 data-URL PNG of the Grad-CAM overlay for the given image.
    If target_class_idx is None, Grad-CAM will use the model's predicted class.
    """
    loader = get_model_loader()
    model, processor = loader.load_image_model()

    # Grad-CAM needs grads; ensure model is in eval but params require grad
    model.eval()
    for p in model.parameters():
        p.requires_grad_(True)

    input_tensor, rgb_float = _preprocess_for_cam(pil_img, processor)

    # ViT base/16/224: 14x14 patch grid
    grid = int(model.config.image_size / model.config.patch_size)
    target_layers = [model.vit.encoder.layer[-1].layernorm_before]

    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

    targets = None
    if target_class_idx is not None:
        targets = [ClassifierOutputTarget(int(target_class_idx))]

    with GradCAM(
        model=model,
        target_layers=target_layers,
        reshape_transform=lambda t: _vit_reshape_transform(t, grid, grid),
    ) as cam:
        grayscale_cam = cam(input_tensor=input_tensor, targets=targets)[0]  # (H,W) in [0,1]

    overlay = show_cam_on_image(rgb_float, grayscale_cam, use_rgb=True)  # uint8 (H,W,3)

    # Encode to base64 PNG (data URL)
    buf = io.BytesIO()
    Image.fromarray(overlay).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    logger.info(f"Heatmap generated ({overlay.shape[0]}x{overlay.shape[1]})")
    return f"data:image/png;base64,{b64}"
