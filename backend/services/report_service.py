from __future__ import annotations

import base64
import html
import json
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from loguru import logger
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import settings
from db.models import AnalysisRecord, Report

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = REPO_ROOT / "frontend" / "src" / "assets" / "logo.png"
IST = ZoneInfo("Asia/Kolkata")

SLATE = colors.HexColor("#172033")
TEXT = colors.HexColor("#263241")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#D9E0EA")
PANEL = colors.HexColor("#F7F9FC")
PANEL_2 = colors.HexColor("#EEF3F8")
CRIMSON = colors.HexColor("#C81E3A")
AMBER = colors.HexColor("#C77700")
GREEN = colors.HexColor("#168A4A")
BLUE = colors.HexColor("#2F6FED")


def _ensure_dir() -> Path:
    path = Path(settings.REPORT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _clamp(value: Any, lo: float = 0.0, hi: float = 100.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = lo
    return max(lo, min(hi, number))


def _clean(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).replace("\x00", "").strip()
    return text or default


def _xml(value: Any, default: str = "") -> str:
    return html.escape(_clean(value, default), quote=True)


def _shorten(value: Any, limit: int = 700) -> str:
    text = " ".join(_clean(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _deepfake_probability(analysis_json: dict[str, Any]) -> int:
    verdict = _as_dict(analysis_json.get("verdict"))
    authenticity = _clamp(verdict.get("authenticity_score", 50))
    return int(round(100 - authenticity))


def _confidence_percent(verdict: dict[str, Any]) -> float:
    confidence = _clamp(verdict.get("model_confidence", 0), 0, 100)
    return confidence * 100 if confidence <= 1 else confidence


def _severity_color(fake_probability: float):
    if fake_probability >= 70:
        return CRIMSON
    if fake_probability >= 40:
        return AMBER
    return GREEN


def _generated_at_ist() -> str:
    return datetime.now(tz=IST).strftime("%d %b %Y, %I:%M %p IST")


def _extract_llm_summary(analysis_json: dict[str, Any]) -> dict[str, Any] | None:
    top = analysis_json.get("llm_summary")
    if isinstance(top, dict) and (top.get("paragraph") or top.get("bullets")):
        return top
    nested = _as_dict(analysis_json.get("explainability")).get("llm_summary")
    if isinstance(nested, dict) and (nested.get("paragraph") or nested.get("bullets")):
        return nested
    return None


def _media_label(media_type: str) -> str:
    return "SCREENSHOT" if media_type == "screenshot" else media_type.upper()


def _resolve_media_path(value: Any) -> Path | None:
    raw = _clean(value)
    if not raw or raw.startswith("data:") or urlparse(raw).scheme in {"http", "https"}:
        return None
    path = Path(raw)
    candidates: list[Path] = []
    if path.is_absolute():
        candidates.append(path)
    stripped = raw.lstrip("/\\")
    candidates.extend(
        [
            REPO_ROOT / stripped,
            BACKEND_ROOT / stripped,
            REPO_ROOT / "backend" / stripped,
        ]
    )
    if stripped.startswith("media/"):
        suffix = stripped[len("media/") :]
        candidates.extend(
            [
                Path(settings.MEDIA_ROOT) / suffix,
                BACKEND_ROOT / "media" / suffix,
                REPO_ROOT / "media" / suffix,
            ]
        )
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            if resolved.exists() and resolved.is_file():
                return resolved
        except OSError:
            continue
    return None


def _image_from_base64(data: Any, max_width: float, max_height: float) -> Image | None:
    raw = _clean(data)
    if not raw:
        return None
    try:
        encoded = raw.split(",", 1)[1] if "," in raw else raw
        blob = base64.b64decode(encoded)
        stream = BytesIO(blob)
        with PILImage.open(BytesIO(blob)) as pil:
            width, height = pil.size
        return _scaled_image(stream, width, height, max_width, max_height)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Unable to render base64 report image: {exc}")
        return None


def _image_from_path(path: Path | None, max_width: float, max_height: float) -> Image | None:
    if path is None:
        return None
    try:
        with PILImage.open(path) as pil:
            width, height = pil.size
        return _scaled_image(str(path), width, height, max_width, max_height)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Unable to render report image {path}: {exc}")
        return None


def _scaled_image(source: Any, width: int, height: int, max_width: float, max_height: float) -> Image:
    scale = min(max_width / max(width, 1), max_height / max(height, 1), 1.0)
    img = Image(source)
    img.drawWidth = width * scale
    img.drawHeight = height * scale
    return img


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DeepShieldTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=22,
            textColor=SLATE,
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "section": ParagraphStyle(
            "DeepShieldSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=SLATE,
            spaceBefore=14,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "DeepShieldBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=13.2,
            textColor=TEXT,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "DeepShieldSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10.5,
            textColor=MUTED,
        ),
        "meta": ParagraphStyle(
            "DeepShieldMeta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=11.5,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
        "badge": ParagraphStyle(
            "DeepShieldBadge",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "quote": ParagraphStyle(
            "DeepShieldQuote",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.5,
            textColor=SLATE,
            leftIndent=8,
            rightIndent=8,
        ),
        "caption": ParagraphStyle(
            "DeepShieldCaption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.7,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "link": ParagraphStyle(
            "DeepShieldLink",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=11.5,
            textColor=BLUE,
        ),
    }


class ScoreGauge(Flowable):
    def __init__(self, score: int, label: str, width: float = 174, height: float = 104):
        super().__init__()
        self.score = int(_clamp(score))
        self.label = label
        self.width = width
        self.height = height
        self.color = _severity_color(self.score)

    def draw(self) -> None:
        c = self.canv
        cx = self.width / 2
        cy = 28
        radius = 60
        bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
        c.saveState()
        c.setLineCap(1)
        c.setStrokeColor(colors.HexColor("#E5EAF1"))
        c.setLineWidth(13)
        c.arc(*bbox, startAng=0, extent=180)
        c.setStrokeColor(self.color)
        c.arc(*bbox, startAng=180 - (180 * self.score / 100), extent=180 * self.score / 100)
        c.setFillColor(SLATE)
        c.setFont("Helvetica-Bold", 25)
        c.drawCentredString(cx, cy + 9, f"{self.score}")
        c.setFont("Helvetica", 7.5)
        c.setFillColor(MUTED)
        c.drawCentredString(cx, cy - 4, "DEEPFAKE PROBABILITY")
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(self.color)
        c.drawCentredString(cx, cy - 18, self.label[:34])
        c.restoreState()


class BarChart(Flowable):
    def __init__(self, metrics: list[tuple[str, float, str]], width: float = 470, row_height: float = 21):
        super().__init__()
        self.metrics = metrics
        self.width = width
        self.row_height = row_height
        self.height = max(1, len(metrics)) * row_height + 7

    def draw(self) -> None:
        c = self.canv
        label_w = 132
        value_w = 54
        bar_w = self.width - label_w - value_w - 18
        y = self.height - self.row_height
        for label, value, value_text in self.metrics:
            pct = _clamp(value)
            color = _severity_color(pct)
            c.setFillColor(SLATE)
            c.setFont("Helvetica", 8.2)
            c.drawString(0, y + 5, label[:35])
            c.setFillColor(colors.HexColor("#E8EDF3"))
            c.roundRect(label_w, y + 5, bar_w, 7, 3, fill=1, stroke=0)
            c.setFillColor(color)
            c.roundRect(label_w, y + 5, max(2, bar_w * pct / 100), 7, 3, fill=1, stroke=0)
            c.setFillColor(MUTED)
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(label_w + bar_w + value_w, y + 4, value_text)
            y -= self.row_height


class PipelineFlow(Flowable):
    def __init__(self, stages: list[str], width: float = 470):
        super().__init__()
        self.stages = [s for s in stages if s][:8]
        self.width = width
        self.height = 58 if self.stages else 20

    def draw(self) -> None:
        c = self.canv
        if not self.stages:
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 8)
            c.drawString(0, 4, "No pipeline stages were recorded.")
            return
        gap = 11
        box_w = min(83, (self.width - gap * (len(self.stages) - 1)) / len(self.stages))
        y = 18
        for idx, stage in enumerate(self.stages):
            x = idx * (box_w + gap)
            c.setFillColor(PANEL_2)
            c.setStrokeColor(LINE)
            c.roundRect(x, y, box_w, 26, 5, fill=1, stroke=1)
            c.setFillColor(SLATE)
            c.setFont("Helvetica-Bold", 6.5)
            c.drawCentredString(x + box_w / 2, y + 15, stage.replace("_", " ")[:18])
            if idx < len(self.stages) - 1:
                ax = x + box_w + 2
                ay = y + 13
                c.setStrokeColor(MUTED)
                c.line(ax, ay, ax + gap - 5, ay)
                c.line(ax + gap - 5, ay, ax + gap - 8, ay + 3)
                c.line(ax + gap - 5, ay, ax + gap - 8, ay - 3)


def _section(title: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(_xml(title), styles["section"])


def _panel(rows: list[list[Any]], col_widths: list[float] | None = None) -> Table:
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E8EDF3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _header(analysis_json: dict[str, Any], generated_at: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
    media_type = _media_label(_clean(analysis_json.get("media_type"), "unknown"))
    report_id = _clean(analysis_json.get("record_id")) or _clean(analysis_json.get("analysis_id"), "N/A")
    logo = _image_from_path(LOGO_PATH if LOGO_PATH.exists() else None, 34 * mm, 16 * mm)
    logo_cell: Any
    if logo:
        logo_cell = logo
    else:
        logo_cell = Paragraph("<b>DeepShield</b>", styles["title"])
    meta = Paragraph(
        f"<b>Report ID:</b> {_xml(report_id)}<br/>"
        f"<b>Generated:</b> {_xml(generated_at)}<br/>"
        f"<b>Media Type:</b> {_xml(media_type)}",
        styles["meta"],
    )
    table = Table([[logo_cell, meta]], colWidths=[85 * mm, 91 * mm])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 1.1, SLATE),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [table, Spacer(1, 8)]


def _badge(text: str, color, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table([[Paragraph(_xml(text), styles["badge"])]], colWidths=[54 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0, color),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _executive_summary(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    verdict = _as_dict(analysis_json.get("verdict"))
    fake_score = _deepfake_probability(analysis_json)
    label = _clean(verdict.get("label"), "Inconclusive")
    color = _severity_color(fake_score)
    confidence = _confidence_percent(verdict)
    llm = _extract_llm_summary(analysis_json)
    summary_text = _clean(
        _as_dict(llm).get("paragraph"),
        "No Gemini explanation summary was saved for this analysis.",
    )
    bullets = _as_list(_as_dict(llm).get("bullets"))
    bullet_html = ""
    if bullets:
        bullet_html = "<br/>" + "<br/>".join(f"- {_xml(b)}" for b in bullets[:4])

    detail = [
        _badge(label, color, styles),
        Spacer(1, 6),
        Paragraph(
            f"<b>Model confidence:</b> {confidence:.1f}%<br/>"
            f"<b>Model label:</b> {_xml(verdict.get('model_label'), 'unknown')}<br/>"
            f"<b>AI explanation summary:</b><br/>{_xml(summary_text)}{bullet_html}",
            styles["body"],
        ),
    ]
    table = Table(
        [[ScoreGauge(fake_score, label), detail]],
        colWidths=[64 * mm, 110 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return [_section("Executive Summary: The Verdict", styles), table]


def _media_context(analysis_json: dict[str, Any], record: AnalysisRecord, styles: dict[str, ParagraphStyle]) -> list[Any]:
    media_type = _clean(analysis_json.get("media_type"), record.media_type).lower()
    expl = _as_dict(analysis_json.get("explainability"))
    story: list[Any] = [_section("Analyzed Media Context", styles)]

    if media_type == "text":
        snippet = _shorten(expl.get("original_text"), 950)
        story.append(
            _panel(
                [[Paragraph(f"&ldquo;{_xml(snippet, 'No text snippet was stored.')}&rdquo;", styles["quote"])]],
                [176 * mm],
            )
        )
        return story

    if media_type in {"image", "screenshot", "video"}:
        thumb = _image_from_path(
            _resolve_media_path(analysis_json.get("thumbnail_url") or record.thumbnail_url),
            72 * mm,
            48 * mm,
        )
        original = _image_from_path(
            _resolve_media_path(analysis_json.get("media_path") or record.media_path),
            72 * mm,
            48 * mm,
        )
        image_cell: Any = thumb or original or Paragraph("Original thumbnail unavailable", styles["small"])
        text_value = _shorten(expl.get("extracted_text") or expl.get("transcript"), 800)
        text_label = "Extracted OCR text" if media_type == "screenshot" else "Context notes"
        text_cell = Paragraph(
            f"<b>{text_label}</b><br/>{_xml(text_value, 'No OCR or transcript text was recorded.')}",
            styles["body"],
        )
        table = Table([[image_cell, text_cell]], colWidths=[78 * mm, 98 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                    ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(table)
        return story

    if media_type == "audio":
        transcript = _shorten(expl.get("transcript") or expl.get("extracted_transcript"), 850)
        duration = _clamp(expl.get("duration_s"), 0, 10_000_000)
        fmt = _clean(analysis_json.get("audio_format") or analysis_json.get("format"), "not recorded")
        story.append(
            _panel(
                [
                    [
                        Paragraph("<b>Duration</b>", styles["small"]),
                        Paragraph(f"{duration:.1f} seconds", styles["body"]),
                    ],
                    [
                        Paragraph("<b>Format</b>", styles["small"]),
                        Paragraph(_xml(fmt), styles["body"]),
                    ],
                    [
                        Paragraph("<b>Transcript</b>", styles["small"]),
                        Paragraph(_xml(transcript, "No transcript was recorded."), styles["body"]),
                    ],
                ],
                [42 * mm, 134 * mm],
            )
        )
        return story

    story.append(Paragraph("No media context was recorded for this analysis.", styles["small"]))
    return story


ANOMALY_LABELS = {
    "facial_symmetry": ("Face alignment", "Facial landmarks do not line up as naturally as expected."),
    "skin_texture": ("Skin texture", "Skin detail appears unusually smooth, noisy, or inconsistent."),
    "lighting_consistency": ("Lighting consistency", "The face lighting does not match the surrounding scene."),
    "background_coherence": ("Background coherence", "Edges or background objects look inconsistent with the subject."),
    "anatomy_hands_eyes": ("Eyes and anatomy", "Eye glare, hands, or anatomy show unnatural structure."),
    "context_objects": ("Scene context", "Objects or scene details conflict with the claimed context."),
}


def _xai_rows(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[list[Any]]:
    media_type = _clean(analysis_json.get("media_type")).lower()
    expl = _as_dict(analysis_json.get("explainability"))
    rows: list[list[Any]] = [
        [
            Paragraph("<b>Signal</b>", styles["small"]),
            Paragraph("<b>Strength</b>", styles["small"]),
            Paragraph("<b>Plain-language reason</b>", styles["small"]),
        ]
    ]

    for indicator in _as_list(expl.get("artifact_indicators"))[:8]:
        item = _as_dict(indicator)
        confidence = _clamp(item.get("confidence"), 0, 1) * 100
        rows.append(
            [
                Paragraph(_xml(item.get("type"), "Artifact"), styles["body"]),
                Paragraph(f"{confidence:.0f}%<br/>{_xml(item.get('severity'), 'signal')}", styles["small"]),
                Paragraph(_xml(item.get("description"), "The visual evidence contains an unusual pattern."), styles["body"]),
            ]
        )

    vlm = _as_dict(expl.get("vlm_breakdown"))
    for key, (label, fallback) in ANOMALY_LABELS.items():
        comp = _as_dict(vlm.get(key))
        if not comp:
            continue
        consistency = _clamp(comp.get("score"), 0, 100)
        anomaly = 100 - consistency
        if anomaly < 18 and not comp.get("notes"):
            continue
        reason = _clean(comp.get("notes"), fallback)
        rows.append(
            [
                Paragraph(_xml(label), styles["body"]),
                Paragraph(f"{anomaly:.0f}% anomaly", styles["small"]),
                Paragraph(_xml(reason), styles["body"]),
            ]
        )

    if media_type in {"text", "screenshot"}:
        for indicator in _as_list(expl.get("manipulation_indicators"))[:6]:
            item = _as_dict(indicator)
            rows.append(
                [
                    Paragraph(_xml(item.get("pattern_type"), "Text signal"), styles["body"]),
                    Paragraph(_xml(item.get("severity"), "medium"), styles["small"]),
                    Paragraph(_xml(item.get("description"), "The wording may be manipulative or misleading."), styles["body"]),
                ]
            )
        for phrase in _as_list(expl.get("suspicious_phrases"))[:6]:
            item = _as_dict(phrase)
            rows.append(
                [
                    Paragraph(_xml(item.get("pattern_type"), "Suspicious phrase"), styles["body"]),
                    Paragraph(_xml(item.get("severity"), "medium"), styles["small"]),
                    Paragraph(_xml(item.get("description"), item.get("text", "OCR text was flagged.")), styles["body"]),
                ]
            )
        for anomaly in _as_list(expl.get("layout_anomalies"))[:5]:
            item = _as_dict(anomaly)
            rows.append(
                [
                    Paragraph(_xml(item.get("type"), "Layout anomaly"), styles["body"]),
                    Paragraph(f"{_clamp(item.get('confidence'), 0, 1) * 100:.0f}%", styles["small"]),
                    Paragraph(_xml(item.get("description"), "The screenshot layout is visually inconsistent."), styles["body"]),
                ]
            )

    if media_type in {"audio", "video"}:
        audio = _as_dict(expl.get("audio") or expl)
        if audio:
            rows.append(
                [
                    Paragraph("Audio consistency", styles["body"]),
                    Paragraph(f"{100 - _clamp(audio.get('audio_authenticity_score')):.0f}% anomaly", styles["small"]),
                    Paragraph(_xml(audio.get("notes"), "Audio signal features were compared for voice consistency."), styles["body"]),
                ]
            )

    if len(rows) == 1:
        rows.append(
            [
                Paragraph("No strong anomaly", styles["body"]),
                Paragraph("Low", styles["small"]),
                Paragraph("The saved model output did not include detailed anomaly markers.", styles["body"]),
            ]
        )
    return rows


def _xai_breakdown(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    rows = _xai_rows(analysis_json, styles)
    table = Table(rows, colWidths=[44 * mm, 30 * mm, 102 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PANEL_2),
                ("TEXTCOLOR", (0, 0), (-1, 0), SLATE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EDF1F5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [_section("XAI Detailed Breakdown", styles), table]


def _forensic_visuals(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    media_type = _clean(analysis_json.get("media_type")).lower()
    if media_type not in {"image", "screenshot", "video"}:
        return []
    expl = _as_dict(analysis_json.get("explainability"))
    visuals: list[tuple[str, str, Image | None]] = [
        (
            "Error Level Analysis (ELA)",
            "Heatmap indicating areas of high compression loss, often associated with digital splicing.",
            _image_from_base64(expl.get("ela_base64"), 78 * mm, 58 * mm)
            or _image_from_path(_resolve_media_path(expl.get("ela_url")), 78 * mm, 58 * mm),
        ),
        (
            "Manipulation Region Overlay",
            "Bounding boxes highlight regions the visual model treated as suspicious or manipulated.",
            _image_from_base64(expl.get("boxes_base64"), 78 * mm, 58 * mm)
            or _image_from_path(_resolve_media_path(expl.get("boxes_url")), 78 * mm, 58 * mm),
        ),
    ]
    cells: list[Any] = []
    for title, caption, image in visuals:
        if image is None:
            image = Paragraph("Visual artifact unavailable", styles["small"])
        cells.append(
            [
                Paragraph(f"<b>{_xml(title)}</b>", styles["body"]),
                image,
                Paragraph(_xml(caption), styles["caption"]),
            ]
        )
    table = Table([cells], colWidths=[88 * mm, 88 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [_section("Forensic Visual Evidence", styles), table]


def _text_metric_chart(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    media_type = _clean(analysis_json.get("media_type")).lower()
    if media_type not in {"text", "screenshot"}:
        return []
    expl = _as_dict(analysis_json.get("explainability"))
    sens = _as_dict(expl.get("sensationalism"))
    metrics = [
        ("Deepfake probability", _clamp(expl.get("fake_probability"), 0, 1) * 100, f"{_clamp(expl.get('fake_probability'), 0, 1) * 100:.0f}%"),
        ("Sensationalism score", _clamp(sens.get("score")), f"{_clamp(sens.get('score')):.0f}/100"),
        ("Exclamations", min(_clamp(sens.get("exclamation_count"), 0, 20) * 5, 100), _clean(sens.get("exclamation_count"), "0")),
        ("ALL CAPS words", min(_clamp(sens.get("caps_word_count"), 0, 25) * 4, 100), _clean(sens.get("caps_word_count"), "0")),
        ("Emotional words", min(_clamp(sens.get("emotional_word_count"), 0, 20) * 5, 100), _clean(sens.get("emotional_word_count"), "0")),
        ("Clickbait matches", min(_clamp(sens.get("clickbait_matches"), 0, 10) * 10, 100), _clean(sens.get("clickbait_matches"), "0")),
    ]
    return [
        _section("Text & Metadata Analysis", styles),
        _panel([[BarChart(metrics)]], [176 * mm]),
    ]


def _exif_metadata(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    exif = _as_dict(_as_dict(analysis_json.get("explainability")).get("exif"))
    if not exif:
        return []
    rows = [[Paragraph("<b>Field</b>", styles["small"]), Paragraph("<b>Value</b>", styles["small"])]]
    for key in ["make", "model", "datetime_original", "software", "lens_model", "gps_info", "trust_reason"]:
        value = _clean(exif.get(key))
        if value:
            rows.append([Paragraph(key.replace("_", " ").title(), styles["body"]), Paragraph(_xml(value), styles["body"])])
    rows.append(
        [
            Paragraph("Trust Adjustment", styles["body"]),
            Paragraph(_xml(exif.get("trust_adjustment"), "0"), styles["body"]),
        ]
    )
    table = Table(rows, colWidths=[48 * mm, 128 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PANEL_2),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EDF1F5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [_section("Image Metadata Signals", styles), table]


def _trusted_sources(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    sources = [_as_dict(s) for s in _as_list(analysis_json.get("trusted_sources")) if _as_dict(s).get("url")]
    if not sources:
        return [
            _section("Trusted Source Cross-Reference", styles),
            Paragraph("No trusted news sources were returned for this analysis.", styles["small"]),
        ]
    rows = [
        [
            Paragraph("<b>Source</b>", styles["small"]),
            Paragraph("<b>Title</b>", styles["small"]),
            Paragraph("<b>Relevance Score</b>", styles["small"]),
        ]
    ]
    for source in sources[:10]:
        url = _xml(source.get("url"))
        source_name = _xml(source.get("source_name"), "Source")
        title = _xml(source.get("title"), source.get("url"))
        rows.append(
            [
                Paragraph(f'<link href="{url}" color="#2F6FED">{source_name}</link>', styles["link"]),
                Paragraph(f'<link href="{url}" color="#2F6FED">{title}</link>', styles["link"]),
                Paragraph(f"{_clamp(source.get('relevance_score'), 0, 1) * 100:.0f}%", styles["body"]),
            ]
        )
    table = Table(rows, colWidths=[40 * mm, 104 * mm, 32 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PANEL_2),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EDF1F5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [_section("Trusted Source Cross-Reference", styles), table]


def _processing_pipeline(analysis_json: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    summary = _as_dict(analysis_json.get("processing_summary"))
    stages = [_clean(s) for s in _as_list(summary.get("stages_completed")) if _clean(s)]
    duration = _clamp(summary.get("total_duration_ms"), 0, 10_000_000)
    return [
        _section("Processing Pipeline", styles),
        _panel(
            [
                [PipelineFlow(stages)],
                [
                    Paragraph(
                        f"<b>Total duration:</b> {duration / 1000:.2f}s &nbsp;&nbsp; "
                        f"<b>Model:</b> {_xml(summary.get('model_used'), 'not recorded')}<br/>"
                        f"<b>Stages:</b> {_xml(' -> '.join(stages), 'not recorded')}",
                        styles["body"],
                    )
                ],
            ],
            [176 * mm],
        ),
    ]


def _footer_notice(analysis_json: dict[str, Any]) -> str:
    return _clean(
        analysis_json.get("responsible_ai_notice"),
        "DeepShield Responsible-AI Notice: AI analysis can be wrong; verify before sharing.",
    )


def _draw_footer(canvas, doc, notice: str) -> None:
    canvas.saveState()
    width, _height = A4
    y = 13 * mm
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(doc.leftMargin, y + 8, width - doc.rightMargin, y + 8)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, y, "Expiry Notice: report links expire according to the configured retention policy.")
    canvas.drawRightString(width - doc.rightMargin, y, f"Page {doc.page}")
    canvas.setFont("Helvetica-Bold", 7.2)
    canvas.drawCentredString(width / 2, y + 10, "DeepShield Responsible-AI Notice")
    canvas.setFont("Helvetica", 6.6)
    canvas.drawCentredString(width / 2, y + 1, notice[:128])
    canvas.restoreState()


def _build_story(record: AnalysisRecord, analysis_json: dict[str, Any], generated_at: str) -> list[Any]:
    styles = _styles()
    story: list[Any] = []
    story.extend(_header(analysis_json, generated_at, styles))
    story.extend(_executive_summary(analysis_json, styles))
    story.extend(_media_context(analysis_json, record, styles))
    story.extend(_xai_breakdown(analysis_json, styles))
    story.extend(_forensic_visuals(analysis_json, styles))
    story.extend(_text_metric_chart(analysis_json, styles))
    story.extend(_exif_metadata(analysis_json, styles))
    story.extend(_trusted_sources(analysis_json, styles))
    story.extend(_processing_pipeline(analysis_json, styles))
    return story


def render_html(analysis_json: dict[str, Any]) -> str:
    """Compatibility shim for older callers.

    PDF generation now uses ReportLab directly so hyperlinks, footers, charts,
    and images are reliable. This compact HTML preview is intentionally not the
    source of truth for report rendering.
    """
    verdict = _as_dict(analysis_json.get("verdict"))
    return (
        "<html><body>"
        f"<h1>DeepShield Report</h1>"
        f"<p>Media: {_xml(analysis_json.get('media_type'), 'unknown')}</p>"
        f"<p>Verdict: {_xml(verdict.get('label'), 'Inconclusive')}</p>"
        f"<p>Deepfake probability: {_deepfake_probability(analysis_json)}/100</p>"
        "</body></html>"
    )


def html_to_pdf(html: str, out_path: Path) -> None:
    """Deprecated compatibility entrypoint.

    The modern report pipeline renders from structured analysis JSON. This
    method remains so imports do not break, but it is no longer used internally.
    """
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, pageCompression=0)
    styles = _styles()
    doc.build([Paragraph(_xml(html), styles["body"])])


def _fallback_pdf(record: AnalysisRecord, analysis_json: dict[str, Any], out_path: Path) -> None:
    styles = _styles()
    notice = _footer_notice(analysis_json)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=24 * mm,
        pageCompression=0,
    )
    story = [
        Paragraph("DeepShield Analysis Report", styles["title"]),
        Paragraph(f"Record #{record.id} - {_xml(record.media_type)}", styles["body"]),
        Paragraph(f"Verdict: {_xml(record.verdict)}", styles["body"]),
        Paragraph(f"Deepfake probability: {_deepfake_probability(analysis_json)}/100", styles["body"]),
    ]
    doc.build(story, onFirstPage=lambda c, d: _draw_footer(c, d, notice), onLaterPages=lambda c, d: _draw_footer(c, d, notice))


def generate_report(record: AnalysisRecord) -> Path:
    out_dir = _ensure_dir()
    filename = f"deepshield_{record.id}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = out_dir / filename
    data = json.loads(record.result_json)
    generated_at = _generated_at_ist()
    notice = _footer_notice(data)

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=14 * mm,
        bottomMargin=25 * mm,
        title=f"DeepShield Threat Intelligence Report {record.id}",
        author="DeepShield",
        pageCompression=0,
    )
    try:
        story = _build_story(record, data, generated_at)
        doc.build(
            story,
            onFirstPage=lambda c, d: _draw_footer(c, d, notice),
            onLaterPages=lambda c, d: _draw_footer(c, d, notice),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"ReportLab renderer failed for report {record.id}, using minimal fallback: {exc}")
        _fallback_pdf(record, data, out_path)

    logger.info(f"Report generated id={record.id} path={out_path} size={out_path.stat().st_size}B")
    return out_path


def create_report_row(analysis_id: int, path: Path) -> Report:
    return Report(
        analysis_id=analysis_id,
        file_path=str(path),
        expires_at=datetime.utcnow() + timedelta(seconds=settings.REPORT_TTL_SECONDS),
    )


def cleanup_expired(now: Optional[datetime] = None) -> int:
    """Delete expired PDFs from disk. Returns count deleted."""
    now = now or datetime.utcnow()
    directory = Path(settings.REPORT_DIR)
    if not directory.exists():
        return 0
    deleted = 0
    ttl = timedelta(seconds=settings.REPORT_TTL_SECONDS)
    for path in directory.glob("*.pdf"):
        try:
            mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
            if now - mtime > ttl:
                path.unlink()
                deleted += 1
        except OSError as exc:
            logger.warning(f"Cleanup failed for {path}: {exc}")
    if deleted:
        logger.info(f"Cleaned up {deleted} expired reports")
    return deleted
