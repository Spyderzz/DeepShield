from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.database import get_db
from db.models import AnalysisRecord

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/recent")
def get_recent_stats(db: Session = Depends(get_db)):
    """Phase 20.4 — Live Engagement Counter."""
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    count = db.query(func.count(AnalysisRecord.id)).filter(AnalysisRecord.created_at >= twenty_four_hours_ago).scalar()
    return {"count_24h": count or 0}
