from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DEBUG"] = "false"

from api.v1.analyze import _persist_response_payload
from api.v1.history import get_history_detail
from db.models import AnalysisRecord
from db.database import Base
from schemas.analyze import TextAnalysisResponse, TextExplainability
from schemas.common import LLMExplainabilitySummary, ProcessingSummary, Verdict


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
