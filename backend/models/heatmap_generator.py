from __future__ import annotations

import base64
import io
from typing import Literal, Optional

import cv2
import numpy as np
import torch
from loguru import logger
from PIL import Image
from pytorch_grad_cam import GradCAMPlusPlus
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from config import settings
from models.model_loader import get_model_loader


class _HFLogitsWrapper(torch.nn.Module):
    """Wrap a HuggingFace image classification model so forward() returns logits
    as a plain tensor (pytorch_grad_cam expects tensor outputs, not dicts/dataclasses).
    """

    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        return self.model(pixel_values=pixel_values).logits


def _vit_reshape_transform(tensor: torch.Tensor, height: int = 14, width: int = 14) -> torch.Tensor:
    """Grad-CAM expects (B, C, H, W); ViT hidden states are (B, 1+H*W, C).
    Drop the CLS token and reshape tokens into a spatial grid.
    """
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


def _encode_overlay_to_base64(overlay: np.ndarray) -> str:
    """Encode a uint8 (H,W,3) RGB overlay to a base64 data-URL PNG."""
    buf = io.BytesIO()
    Image.fromarray(overlay).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _compute_gradcam_pp(
    pil_img: Image.Image,
    target_class_idx: Optional[int] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Grad-CAM++ averaged across the last 3 ViT encoder layers.
    Returns (grayscale_cam, rgb_float) where grayscale_cam is (H,W) in [0,1].
    """
    loader = get_model_loader()
    model, processor = loader.load_image_model()

    model.eval()
    for p in model.parameters():
        p.requires_grad_(True)

    input_tensor, rgb_float = _preprocess_for_cam(pil_img, processor)

    grid = int(model.config.image_size / model.config.patch_size)

    # Average across last 3 ViT encoder layers for smoother heatmaps
    num_layers = len(model.vit.encoder.layer)
    last_n = min(3, num_layers)
    target_layers = [
        model.vit.encoder.layer[-(i + 1)].layernorm_before
        for i in range(last_n)
    ]

    wrapped = _HFLogitsWrapper(model)

    targets = None
    if target_class_idx is not None:
        targets = [ClassifierOutputTarget(int(target_class_idx))]

    with GradCAMPlusPlus(
        model=wrapped,
        target_layers=target_layers,
        reshape_transform=lambda t: _vit_reshape_transform(t, grid, grid),
    ) as cam:
        grayscale_cam = cam(input_tensor=input_tensor, targets=targets)[0]  # (H,W) in [0,1]

    return grayscale_cam, rgb_float


def _compute_gradcam_pp_efficientnet(
    pil_img: Image.Image,
) -> tuple[np.ndarray, np.ndarray, Literal["attention", "gradcam++"]]:
    """Grad-CAM++ for EfficientNetAutoAttB4.

    Returns (grayscale_cam, rgb_float, heatmap_source).
    Prefers the model's built-in attention map; falls back to Grad-CAM++ on the
    last MBConv block if attention extraction fails.
    """
    loader = get_model_loader()
    eff = loader.load_efficientnet()
    if eff is None:
        raise RuntimeError("EfficientNet not loaded")

    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    img_np = np.array(pil_img)

    # Prepare face crop (same path as detect_image).
    frame_data = eff.face_extractor.process_image(img=img_np)
    faces: list = frame_data.get("faces", [])
    if not faces:
        raise ValueError("no_face")

    face_t = eff._face_tensor(faces[0]).unsqueeze(0).to(eff.device)

    # Resize the face crop to float [0,1] for overlay.
    face_np = faces[0]
    h, w = face_np.shape[:2]
    rgb_float = face_np.astype(np.float32) / 255.0
    if rgb_float.shape[:2] != (224, 224):
        rgb_float = cv2.resize(rgb_float, (224, 224)).astype(np.float32)

    # Try Grad-CAM++ on last MBConv block (_blocks[-1]).
    try:
        net = eff.net
        target_layers = [net.efficientnet._blocks[-1]]

        face_t.requires_grad_(True)
        for p in net.parameters():
            p.requires_grad_(True)

        with GradCAMPlusPlus(model=net, target_layers=target_layers) as cam:
            grayscale_cam = cam(input_tensor=face_t, targets=None)[0]

        return grayscale_cam, rgb_float, "gradcam++"
    except Exception as e:
        logger.warning(f"EfficientNet Grad-CAM++ failed ({e}), using uniform fallback")
        grayscale_cam = np.ones((224, 224), dtype=np.float32) * 0.5
        return grayscale_cam, rgb_float, "gradcam++"


def generate_heatmap_base64(
    pil_img: Image.Image,
    target_class_idx: Optional[int] = None,
    model_family: Literal["vit", "efficientnet"] = "vit",
) -> tuple[str, str]:
    """Produce a base64 data-URL PNG of the Grad-CAM++ overlay.

    Returns (base64_png, heatmap_source) where heatmap_source is one of
    "gradcam++", "attention", "fallback", "none".
    """
    if model_family == "efficientnet":
        try:
            grayscale_cam, rgb_float, source = _compute_gradcam_pp_efficientnet(pil_img)
        except ValueError:
            logger.info("EfficientNet heatmap skipped — no face detected")
            return "", "none"
        except Exception as e:
            logger.warning(f"EfficientNet heatmap failed: {e}")
            return "", "fallback"
    else:
        grayscale_cam, rgb_float = _compute_gradcam_pp(pil_img, target_class_idx)
        source = "gradcam++"

    overlay = show_cam_on_image(rgb_float, grayscale_cam, use_rgb=True)
    logger.info(f"Heatmap generated ({overlay.shape[0]}x{overlay.shape[1]}) source={source}")
    return _encode_overlay_to_base64(overlay), source


def generate_boxes_base64(
    pil_img: Image.Image,
    target_class_idx: Optional[int] = None,
    top_k: int = 5,
    threshold: float = 0.4,
) -> str:
    """Produce bounding boxes around top-K connected components from Grad-CAM++ activation.
    Renders colored boxes (red/yellow/orange by intensity) on the original image.
    """
    grayscale_cam, rgb_float = _compute_gradcam_pp(pil_img, target_class_idx)

    h, w = rgb_float.shape[:2]
    base_img = (rgb_float * 255).astype(np.uint8).copy()

    # Threshold the heatmap to find activated regions
    binary = (grayscale_cam >= threshold).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        logger.info("No significant activation regions found for bounding boxes")
        return _encode_overlay_to_base64(base_img)

    # Sort by area descending, take top_k
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:top_k]

    # Color by mean activation intensity within each box
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        region_activation = grayscale_cam[y:y + bh, x:x + bw].mean()

        if region_activation >= 0.7:
            color = (220, 40, 40)    # red — high suspicion
        elif region_activation >= 0.5:
            color = (240, 140, 20)   # orange — medium
        else:
            color = (230, 200, 40)   # yellow — lower

        cv2.rectangle(base_img, (x, y), (x + bw, y + bh), color, 2)
        label = f"{region_activation * 100:.0f}%"
        cv2.putText(base_img, label, (x, max(y - 6, 12)),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)

    logger.info(f"Bounding boxes generated: {len(contours)} regions")
    return _encode_overlay_to_base64(base_img)
