from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.database import get_db
from db.models import AnalysisRecord, User

router = APIRouter(prefix="/history", tags=["history"])


class HistoryItem(BaseModel):
    id: int
    media_type: str
    verdict: str
    authenticity_score: float
    created_at: datetime


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int


@router.get("", response_model=HistoryListResponse)
def list_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    q = db.query(AnalysisRecord).filter(AnalysisRecord.user_id == user.id)
    total = q.count()
    rows = q.order_by(AnalysisRecord.created_at.desc()).offset(offset).limit(limit).all()
    items = [
        HistoryItem(
            id=r.id,
            media_type=r.media_type,
            verdict=r.verdict,
            authenticity_score=r.authenticity_score,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return HistoryListResponse(items=items, total=total)


@router.get("/{record_id}")
def get_history_detail(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
    if not r or r.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")
    try:
        payload = json.loads(r.result_json)
        # Inject storage fields from DB columns so the frontend can display full-size media
        if r.media_path and not payload.get("media_path"):
            payload["media_path"] = r.media_path
        if r.thumbnail_url and not payload.get("thumbnail_url"):
            payload["thumbnail_url"] = r.thumbnail_url
        return payload
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Corrupt result payload")


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
    if not r or r.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")
    db.delete(r)
    db.commit()
    return None
