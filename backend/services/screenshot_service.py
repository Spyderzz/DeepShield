from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
from loguru import logger
from PIL import Image

from models.model_loader import get_model_loader


@dataclass
class OCRBox:
    text: str
    bbox: List[List[int]]  # 4 points [[x,y],...]
    confidence: float


@dataclass
class SuspiciousPhrase:
    text: str
    bbox: List[List[int]]
    pattern_type: str
    severity: str
    description: str


@dataclass
class LayoutAnomaly:
    type: str  # misalignment / font_mismatch / uneven_spacing
    severity: str
    description: str
    confidence: float


def run_ocr(pil_img: Image.Image) -> List[OCRBox]:
    reader = get_model_loader().load_ocr_engine()
    arr = np.array(pil_img.convert("RGB"))
    results = reader.readtext(arr, detail=1, paragraph=False, mag_ratio=1.5)
    out: List[OCRBox] = []
    for bbox, text, conf in results:
        out.append(OCRBox(
            text=str(text),
            bbox=[[int(p[0]), int(p[1])] for p in bbox],
            confidence=float(conf),
        ))
    logger.info(f"OCR extracted {len(out)} text regions")
    return out


def extract_full_text(boxes: List[OCRBox], min_confidence: float = 0.30) -> str:
    filtered = [b for b in boxes if b.text.strip() and b.confidence >= min_confidence]
    filtered.sort(key=lambda b: (min(p[1] for p in b.bbox), min(p[0] for p in b.bbox)))
    return " ".join(b.text for b in filtered)


def map_phrases_to_boxes(boxes: List[OCRBox], manipulation_indicators) -> List[SuspiciousPhrase]:
    """Map each manipulation indicator to the OCR box whose text contains it."""
    out: List[SuspiciousPhrase] = []
    for mi in manipulation_indicators:
        needle = mi.matched_text.lower()
        for b in boxes:
            if needle in b.text.lower():
                out.append(SuspiciousPhrase(
                    text=mi.matched_text,
                    bbox=b.bbox,
                    pattern_type=mi.pattern_type,
                    severity=mi.severity,
                    description=mi.description,
                ))
                break
    return out


def detect_layout_anomalies(boxes: List[OCRBox]) -> List[LayoutAnomaly]:
    """Heuristic layout checks on OCR bboxes."""
    out: List[LayoutAnomaly] = []
    if len(boxes) < 3:
        return out

    heights = []
    x_lefts = []
    for b in boxes:
        pts = b.bbox
        ys = [p[1] for p in pts]
        xs = [p[0] for p in pts]
        heights.append(max(ys) - min(ys))
        x_lefts.append(min(xs))

    h_arr = np.array(heights, dtype=float)
    if h_arr.mean() > 0:
        cv_h = float(h_arr.std() / h_arr.mean())
        if cv_h > 0.7:
            out.append(LayoutAnomaly(
                type="font_mismatch",
                severity="medium" if cv_h < 1.2 else "high",
                description=f"High variance in text heights (cv={cv_h:.2f}) — mixed fonts/sizes possible",
                confidence=min(cv_h / 1.5, 1.0),
            ))

    x_arr = np.array(x_lefts, dtype=float)
    if x_arr.std() > 0 and len(x_arr) > 4:
        clustered = sum(1 for x in x_arr if abs(x - np.median(x_arr)) < 20)
        align_ratio = clustered / len(x_arr)
        if align_ratio < 0.4:
            out.append(LayoutAnomaly(
                type="misalignment",
                severity="low",
                description=f"Only {align_ratio*100:.0f}% of text blocks share left-alignment — unusual layout",
                confidence=1.0 - align_ratio,
            ))

    if len(boxes) >= 4:
        tops = sorted([min(p[1] for p in b.bbox) for b in boxes])
        gaps = np.diff(tops)
        gaps = gaps[gaps > 0]
        if len(gaps) >= 3 and gaps.mean() > 0:
            cv_g = float(gaps.std() / gaps.mean())
            if cv_g > 1.5:
                out.append(LayoutAnomaly(
                    type="uneven_spacing",
                    severity="low",
                    description=f"Irregular vertical spacing between text blocks (cv={cv_g:.2f})",
                    confidence=min(cv_g / 2.5, 1.0),
                ))

    return out
