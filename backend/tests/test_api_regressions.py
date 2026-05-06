from __future__ import annotations

import json
import os
import asyncio
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DEBUG"] = "false"

from api.v1.analyze import _find_existing_llm_summary, _persist_response_payload, _store_llm_summary
from api.v1 import auth as auth_module
from api.v1.history import get_history_detail, list_history
from db.models import AnalysisRecord
from db.database import Base
from schemas.analyze import TextAnalysisResponse, TextExplainability
from schemas.common import LLMExplainabilitySummary, ProcessingSummary, Verdict
from services.llm_explainer import _build_llm_payload


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_anonymous_history_detail_accepts_matching_analysis_token(db_session):
    payload = {
        "analysis_id": "public-token",
        "media_type": "text",
        "verdict": {"label": "Likely Real", "authenticity_score": 80},
    }
    record = AnalysisRecord(
        user_id=None,
        media_type="text",
        verdict="Likely Real",
        authenticity_score=80,
        result_json=json.dumps(payload),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    result = get_history_detail(record.id, token="public-token", user=None, db=db_session)

    assert result["analysis_id"] == "public-token"


def test_anonymous_history_detail_rejects_missing_analysis_token(db_session):
    record = AnalysisRecord(
        user_id=None,
        media_type="text",
        verdict="Likely Real",
        authenticity_score=80,
        result_json=json.dumps({"analysis_id": "public-token"}),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    with pytest.raises(Exception):
        get_history_detail(record.id, token=None, user=None, db=db_session)


def test_history_list_includes_text_preview_from_saved_analysis(db_session):
    payload = {
        "analysis_id": "analysis-text-preview",
        "media_type": "text",
        "verdict": {"label": "Likely Real", "authenticity_score": 81},
        "explainability": {
            "original_text": "Government confirms a new public health advisory after verified reports.",
        },
    }
    record = AnalysisRecord(
        user_id=3,
        media_type="text",
        verdict="Likely Real",
        authenticity_score=81,
        result_json=json.dumps(payload),
    )
    db_session.add(record)
    db_session.commit()

    result = list_history(limit=50, offset=0, user=type("UserStub", (), {"id": 3})(), db=db_session)

    assert result.items[0].text_preview == payload["explainability"]["original_text"]


def test_persist_response_payload_keeps_postprocessing_fields_for_reload(db_session):
    record = AnalysisRecord(
        user_id=1,
        media_type="text",
        verdict="Likely Real",
        authenticity_score=80,
        result_json="{}",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    resp = TextAnalysisResponse(
        analysis_id="analysis-1",
        record_id=record.id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        verdict=Verdict(
            label="Likely Real",
            severity="positive",
            authenticity_score=80,
            model_confidence=0.2,
            model_label="real",
        ),
        explainability=TextExplainability(fake_probability=0.2, top_label="real"),
        llm_summary=LLMExplainabilitySummary(paragraph="Persisted explanation"),
        processing_summary=ProcessingSummary(
            stages_completed=["classification", "llm_explanation"],
            total_duration_ms=12,
            model_used="test-model",
        ),
    )

    _persist_response_payload(db_session, record, resp)

    db_session.refresh(record)
    stored = json.loads(record.result_json)
    assert stored["record_id"] == record.id
    assert stored["llm_summary"]["paragraph"] == "Persisted explanation"
    assert stored["processing_summary"]["stages_completed"] == ["classification", "llm_explanation"]


def test_llm_prompt_payload_keeps_core_evidence_but_drops_heavy_fields():
    payload = {
        "analysis_id": "analysis-1",
        "record_id": 7,
        "media_type": "video",
        "verdict": {"label": "Suspicious", "authenticity_score": 42, "model_confidence": 0.8},
        "trusted_sources": [{"title": f"source {i}", "url": f"https://example.com/{i}", "relevance_score": 0.9} for i in range(8)],
        "processing_summary": {"stages_completed": ["frame_extraction", "classification"], "total_duration_ms": 1234},
        "explainability": {
            "heatmap_base64": "x" * 10000,
            "ela_base64": "x" * 10000,
            "ocr_boxes": [{"text": "box", "bbox": [[0, 0]], "confidence": 0.9}] * 30,
            "frames": [{"index": i, "suspicious_prob": 0.9, "timestamp_s": i} for i in range(20)],
            "artifact_indicators": [{"type": f"artifact {i}", "description": "desc", "confidence": 0.7} for i in range(8)],
        },
    }

    compact = _build_llm_payload(payload)

    assert compact["verdict"]["label"] == "Suspicious"
    assert "heatmap_base64" not in compact["explainability"]
    assert "ela_base64" not in compact["explainability"]
    assert len(compact["trusted_sources"]) == 5
    assert len(compact["explainability"]["frames"]) == 6
    assert len(compact["explainability"]["ocr_boxes"]) == 8


def test_llm_summary_reuse_finds_top_level_and_nested_payloads():
    top_level = {"llm_summary": {"paragraph": "Already generated"}}
    nested = {"explainability": {"llm_summary": {"paragraph": "Nested generated"}}}

    assert _find_existing_llm_summary(top_level)["paragraph"] == "Already generated"
    assert _find_existing_llm_summary(nested)["paragraph"] == "Nested generated"


def test_store_llm_summary_uses_media_specific_location_without_duplication():
    image_payload = {"media_type": "image", "explainability": {}}
    text_payload = {"media_type": "text", "explainability": {}}
    summary = {"paragraph": "Generated", "bullets": []}

    _store_llm_summary(image_payload, summary)
    _store_llm_summary(text_payload, summary)

    assert image_payload["explainability"]["llm_summary"] == summary
    assert "llm_summary" not in image_payload
    assert text_payload["llm_summary"] == summary


class _FakeRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}

    def url_for(self, _name: str, provider: str) -> str:
        return f"http://localhost:8000/api/v1/auth/oauth/{provider}/callback"


def test_oauth_start_signs_frontend_origin_from_allowed_request_origin(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth_module.settings, "GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(auth_module.settings, "PUBLIC_APP_URL", "")
    monkeypatch.setattr(auth_module.settings, "PUBLIC_API_URL", "")
    monkeypatch.setattr(auth_module.settings, "CORS_ORIGINS", ["http://localhost:5173"])

    result = auth_module.oauth_start(
        "google",
        _FakeRequest({"origin": "http://localhost:5173"}),
        redirect_to="/history",
        remember=False,
    )

    params = parse_qs(urlparse(result["authorization_url"]).query)
    payload = auth_module._state_verify(params["state"][0])

    assert params["redirect_uri"] == ["http://localhost:8000/api/v1/auth/oauth/google/callback"]
    assert payload["frontend_origin"] == "http://localhost:5173"
    assert payload["redirect_to"] == "/history"
    assert payload["remember"] is False


def test_oauth_callback_redirects_to_signed_frontend_origin(db_session, monkeypatch):
    async def fake_fetch_google_profile(_code: str, _redirect_uri: str) -> dict[str, str]:
        return {"email": "oauth@example.com", "name": "OAuth User"}

    monkeypatch.setattr(auth_module, "_fetch_google_profile", fake_fetch_google_profile)
    monkeypatch.setattr(auth_module.settings, "PUBLIC_API_URL", "")
    monkeypatch.setattr(auth_module.settings, "PUBLIC_APP_URL", "")
    state = auth_module._state_sign({
        "provider": "google",
        "redirect_to": "/analyze",
        "remember": True,
        "frontend_origin": "http://localhost:5173",
        "exp": int(datetime.now(timezone.utc).timestamp()) + 60,
    })

    response = asyncio.run(auth_module.oauth_callback(
        "google",
        code="auth-code",
        state=state,
        request=_FakeRequest(),
        db=db_session,
    ))

    location = response.headers["location"]
    assert location.startswith("http://localhost:5173/auth/callback?")
    params = parse_qs(urlparse(location).query)
    assert params["next"] == ["/analyze"]
    assert params["remember"] == ["1"]
    assert params["token"]


def test_oauth_callback_url_uses_public_api_url_without_duplicate_api_prefix(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "PUBLIC_API_URL", "https://api.example.com/api/v1")

    assert (
        auth_module._oauth_callback_url("google", _FakeRequest())
        == "https://api.example.com/api/v1/auth/oauth/google/callback"
    )
