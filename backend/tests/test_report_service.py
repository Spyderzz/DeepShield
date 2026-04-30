from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

os.environ["DEBUG"] = "false"

from db.models import AnalysisRecord
from services import report_service


def _report_dir() -> Path:
    path = Path("backend") / "test_outputs" / f"reports_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _record(payload: dict) -> AnalysisRecord:
    return AnalysisRecord(
        id=17,
        user_id=1,
        media_type=payload.get("media_type", "text"),
        verdict=payload["verdict"]["label"],
        authenticity_score=float(payload["verdict"]["authenticity_score"]),
        result_json=json.dumps(payload),
    )


def _text_payload() -> dict:
    return {
        "analysis_id": "analysis-text-17",
        "record_id": 17,
        "media_type": "text",
        "timestamp": datetime(2026, 4, 30, 10, 0, tzinfo=timezone.utc).isoformat(),
        "verdict": {
            "label": "Very Likely Fake",
            "severity": "critical",
            "authenticity_score": 14,
            "model_confidence": 0.91,
            "model_label": "fake",
        },
        "explainability": {
            "original_text": "BREAKING!!! THIS SHOCKING claim is spreading without verified sourcing.",
            "fake_probability": 0.86,
            "top_label": "fake",
            "all_scores": {"fake": 0.86, "real": 0.14},
            "keywords": ["claim", "verified sourcing"],
            "sensationalism": {
                "score": 82,
                "level": "High",
                "exclamation_count": 3,
                "caps_word_count": 2,
                "clickbait_matches": 1,
                "emotional_word_count": 1,
                "superlative_count": 0,
            },
            "manipulation_indicators": [
                {
                    "pattern_type": "emotional_manipulation",
                    "matched_text": "SHOCKING",
                    "start_pos": 17,
                    "end_pos": 25,
                    "severity": "high",
                    "description": "Loaded language is used to heighten emotion before evidence is shown.",
                }
            ],
            "detected_language": "en",
        },
        "llm_summary": {
            "paragraph": "The claim uses urgent wording and lacks corroboration from reliable reporting.",
            "bullets": ["High sensationalism", "Trusted-source match is weak"],
            "model_used": "gemini-test",
        },
        "trusted_sources": [
            {
                "source_name": "Reuters",
                "title": "Verified reporting about the event",
                "url": "https://www.reuters.com/world/example-report",
                "description": "Independent report used for comparison.",
                "published_at": "2026-04-29",
                "relevance_score": 0.92,
            }
        ],
        "processing_summary": {
            "stages_completed": ["classification", "keyword_extraction", "news_lookup"],
            "total_duration_ms": 1842,
            "model_used": "test-text-model",
            "models_used": ["test-text-model"],
            "calibrator_applied": False,
        },
        "responsible_ai_notice": "DeepShield Responsible-AI Notice",
    }


def test_generate_report_creates_pdf_with_active_trusted_source_link(monkeypatch):
    monkeypatch.setattr(report_service.settings, "REPORT_DIR", str(_report_dir()))

    path = report_service.generate_report(_record(_text_payload()))

    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert b"/URI (https://www.reuters.com/world/example-report)" in data


def test_report_pdf_contains_required_text_context_and_pipeline(monkeypatch):
    monkeypatch.setattr(report_service.settings, "REPORT_DIR", str(_report_dir()))

    path = report_service.generate_report(_record(_text_payload()))

    text = path.read_bytes().decode("latin-1", errors="ignore")
    assert "Analyzed Media Context" in text
    assert "BREAKING!!! THIS SHOCKING claim" in text
    assert "classification" in text
    assert "news_lookup" in text
