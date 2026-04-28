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


def _face_bbox_from_detections(frame_data: dict, orig_h: int, orig_w: int) -> Optional[tuple[int,int,int,int]]:
    """Extract (ymin, xmin, ymax, xmax) in pixel coords from BlazeFace frame_data."""
    detections = frame_data.get("detections", [])
    if len(detections) == 0:
        return None
    d = detections[0]  # first (highest-confidence) face
    ymin = int(max(0, d[0]))
    xmin = int(max(0, d[1]))
    ymax = int(min(orig_h, d[2]))
    xmax = int(min(orig_w, d[3]))
    if ymax <= ymin or xmax <= xmin:
        return None
    return ymin, xmin, ymax, xmax


def _compute_gradcam_pp_efficientnet(
    pil_img: Image.Image,
) -> tuple[np.ndarray, Optional[tuple[int,int,int,int]], Literal["attention", "gradcam++"]]:
    """Grad-CAM++ for EfficientNetAutoAttB4.

    Returns (grayscale_cam_224, face_bbox_pixels_or_None, heatmap_source).
    grayscale_cam_224 is in the 224x224 coordinate space of the face crop.
    face_bbox_pixels is (ymin, xmin, ymax, xmax) in original image pixels.
    """
    loader = get_model_loader()
    eff = loader.load_efficientnet()
    if eff is None:
        raise RuntimeError("EfficientNet not loaded")

    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    img_np = np.array(pil_img)
    orig_h, orig_w = img_np.shape[:2]

    frame_data = eff.face_extractor.process_image(img=img_np)
    faces: list = frame_data.get("faces", [])
    if not faces:
        raise ValueError("no_face")

    face_bbox = _face_bbox_from_detections(frame_data, orig_h, orig_w)

    face_t = eff._face_tensor(faces[0]).unsqueeze(0).to(eff.device)

    try:
        net = eff.net
        target_layers = [net.efficientnet._blocks[-1]]
        face_t.requires_grad_(True)
        for p in net.parameters():
            p.requires_grad_(True)
        with GradCAMPlusPlus(model=net, target_layers=target_layers) as cam:
            grayscale_cam = cam(input_tensor=face_t, targets=None)[0]
        return grayscale_cam, face_bbox, "gradcam++"
    except Exception as e:
        logger.warning(f"EfficientNet Grad-CAM++ failed ({e}), using uniform fallback")
        grayscale_cam = np.ones((224, 224), dtype=np.float32) * 0.5
        return grayscale_cam, face_bbox, "gradcam++"


def _cam_to_full_image(
    grayscale_cam: np.ndarray,
    pil_img: Image.Image,
    face_bbox: Optional[tuple[int,int,int,int]] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Resize grayscale_cam to the original image dimensions.

    For EfficientNet (face-crop cam + known bbox): places the cam activation
    at the face location; background activation is 0.
    For ViT (full-image cam): bilinear resize to original dims.

    Returns (cam_full [H,W] float32), orig_np [H,W,3] float32 in [0,1]).
    """
    orig_w, orig_h = pil_img.size
    orig_np = np.array(pil_img.convert("RGB")).astype(np.float32) / 255.0

    if face_bbox is not None:
        ymin, xmin, ymax, xmax = face_bbox
        face_h, face_w = ymax - ymin, xmax - xmin
        cam_full = np.zeros((orig_h, orig_w), dtype=np.float32)
        cam_resized = cv2.resize(grayscale_cam, (face_w, face_h), interpolation=cv2.INTER_LINEAR)
        cam_full[ymin:ymax, xmin:xmax] = cam_resized
    else:
        cam_full = cv2.resize(grayscale_cam, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

    return cam_full, orig_np


def generate_heatmap_base64(
    pil_img: Image.Image,
    target_class_idx: Optional[int] = None,
    model_family: Literal["vit", "efficientnet"] = "vit",
) -> tuple[str, str]:
    """Produce a base64 data-URL PNG of the Grad-CAM++ overlay at original image resolution.

    Returns (base64_png, heatmap_source).
    """
    if model_family == "efficientnet":
        try:
            grayscale_cam, face_bbox, source = _compute_gradcam_pp_efficientnet(pil_img)
            cam_full, orig_np = _cam_to_full_image(grayscale_cam, pil_img, face_bbox)
        except ValueError:
            # BlazeFace found no face — fall back to ViT Grad-CAM on the full image.
            logger.info("EfficientNet heatmap: no face detected — falling back to ViT Grad-CAM++")
            try:
                grayscale_cam, _ = _compute_gradcam_pp(pil_img, target_class_idx)
                cam_full, orig_np = _cam_to_full_image(grayscale_cam, pil_img, None)
                source = "vit_fallback"
            except Exception as fe:
                logger.warning(f"ViT fallback heatmap also failed: {fe}")
                return "", "none"
        except Exception as e:
            logger.warning(f"EfficientNet heatmap failed: {e}")
            return "", "fallback"
    else:
        grayscale_cam, _ = _compute_gradcam_pp(pil_img, target_class_idx)
        source = "gradcam++"
        cam_full, orig_np = _cam_to_full_image(grayscale_cam, pil_img, None)

    # Generate transparent RGBA overlay so CSS can blend it without darkening the base image
    heatmap_colored = cv2.applyColorMap(np.uint8(255 * cam_full), cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    
    alpha = np.clip(cam_full * 1.8 * 255, 0, 255).astype(np.uint8)
    overlay_rgba = np.dstack((heatmap_colored, alpha))
    
    logger.info(f"Heatmap generated ({overlay_rgba.shape[1]}x{overlay_rgba.shape[0]}) source={source}")
    return _encode_overlay_to_base64(overlay_rgba), source


def generate_boxes_base64(
    pil_img: Image.Image,
    target_class_idx: Optional[int] = None,
    top_k: int = 5,
    threshold: float = 0.4,
) -> str:
    """Draw Grad-CAM++ activation bounding boxes on the full original image.

    Uses the ViT cam (full-image coverage), resizes it to original dimensions,
    finds contours, and draws boxes at the correct pixel locations.
    """
    grayscale_cam, _ = _compute_gradcam_pp(pil_img, target_class_idx)

    # Use original image as the canvas — resize cam to match
    orig_w, orig_h = pil_img.size
    base_img = np.array(pil_img.convert("RGB")).copy()
    cam_full = cv2.resize(grayscale_cam, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

    binary = (cam_full >= threshold).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        logger.info("No significant activation regions found for bounding boxes")
        return _encode_overlay_to_base64(base_img)

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:top_k]

    # Scale line width to image size
    line_w = max(2, orig_w // 300)
    font_scale = max(0.5, orig_w / 1200)

    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        region_activation = cam_full[y:y + bh, x:x + bw].mean()

        if region_activation >= 0.7:
            color = (220, 40, 40)
        elif region_activation >= 0.5:
            color = (240, 140, 20)
        else:
            color = (230, 200, 40)

        cv2.rectangle(base_img, (x, y), (x + bw, y + bh), color, line_w)
        label = f"{region_activation * 100:.0f}%"
        cv2.putText(base_img, label, (x, max(y - 6, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, line_w, cv2.LINE_AA)

    logger.info(f"Bounding boxes generated: {len(contours)} regions on {orig_w}x{orig_h} image")
    return _encode_overlay_to_base64(base_img)
