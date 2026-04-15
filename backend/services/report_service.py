from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger
from xhtml2pdf import pisa  # type: ignore

from config import settings
from db.models import AnalysisRecord, Report

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def _score_class(score: int) -> str:
    if score >= 70:
        return "real"
    if score >= 40:
        return "warn"
    return "fake"


def _ensure_dir() -> Path:
    p = Path(settings.REPORT_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def render_html(analysis_json: dict) -> str:
    tmpl = _env.get_template("report.html")
    return tmpl.render(
        analysis_id=analysis_json.get("analysis_id", ""),
        media_type=analysis_json.get("media_type", "unknown"),
        verdict=analysis_json.get("verdict", {}),
        explainability=analysis_json.get("explainability", {}),
        trusted_sources=analysis_json.get("trusted_sources", []),
        contradicting_evidence=analysis_json.get("contradicting_evidence", []),
        processing_summary=analysis_json.get("processing_summary", {}),
        responsible_ai_notice=analysis_json.get(
            "responsible_ai_notice",
            "AI-based analysis may not be 100% accurate.",
        ),
        score_class=_score_class(analysis_json.get("verdict", {}).get("authenticity_score", 50)),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def html_to_pdf(html: str, out_path: Path) -> None:
    with open(out_path, "wb") as f:
        result = pisa.CreatePDF(html, dest=f)
    if result.err:
        raise RuntimeError(f"xhtml2pdf failed with {result.err} errors")


def generate_report(record: AnalysisRecord) -> Path:
    out_dir = _ensure_dir()
    filename = f"deepshield_{record.id}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = out_dir / filename

    data = json.loads(record.result_json)
    html = render_html(data)
    html_to_pdf(html, out_path)
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
    d = Path(settings.REPORT_DIR)
    if not d.exists():
        return 0
    deleted = 0
    ttl = timedelta(seconds=settings.REPORT_TTL_SECONDS)
    for f in d.glob("*.pdf"):
        try:
            mtime = datetime.utcfromtimestamp(f.stat().st_mtime)
            if now - mtime > ttl:
                f.unlink()
                deleted += 1
        except OSError as e:
            logger.warning(f"Cleanup failed for {f}: {e}")
    if deleted:
        logger.info(f"Cleaned up {deleted} expired reports")
    return deleted
