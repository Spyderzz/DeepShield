from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.orm import Session

from api.deps import get_current_user, optional_current_user
from db.database import get_db
from db.models import AnalysisRecord, Report, User
from services.rate_limit import ANON_REPORT, AUTH_REPORT, is_anon, is_authed, limiter
from services.report_service import cleanup_expired, create_report_row, generate_report

router = APIRouter(prefix="/report", tags=["report"])


def _assert_record_access(record: AnalysisRecord, user: User | None, token: str | None = None) -> None:
    """Phase 15.1 — allow access if the requester owns the record, or if the record
    is anonymous (user_id is None) AND they provide the correct UUID token. Everything else is 403."""
    if user is not None and record.user_id == user.id:
        return
    if record.user_id is None:
        if not token:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Anonymous reports require a token")
        try:
            import json
            data = json.loads(record.result_json)
            if data.get("analysis_id") == token:
                return
        except Exception:
            pass
    raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not own this analysis")


@router.post("/{analysis_id}")
@limiter.limit(ANON_REPORT, exempt_when=is_authed)
@limiter.limit(AUTH_REPORT, exempt_when=is_anon)
def generate(
    request: Request,
    analysis_id: int,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
):
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="analysis not found")

    _assert_record_access(record, user, token)

    existing = db.query(Report).filter(Report.analysis_id == analysis_id).first()
    if existing and Path(existing.file_path).exists():
        return {"report_id": existing.id, "analysis_id": analysis_id, "ready": True}

    try:
        path = generate_report(record)
    except Exception as e:  # noqa: BLE001
        logger.exception(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"report generation failed: {e}")

    if existing:
        existing.file_path = str(path)
        db.commit()
        db.refresh(existing)
        return {"report_id": existing.id, "analysis_id": analysis_id, "ready": True}

    row = create_report_row(analysis_id, path)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"report_id": row.id, "analysis_id": analysis_id, "ready": True}


@router.get("/{analysis_id}/download")
@limiter.limit(ANON_REPORT, exempt_when=is_authed)
@limiter.limit(AUTH_REPORT, exempt_when=is_anon)
def download(
    request: Request,
    analysis_id: int,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
):
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="analysis not found")
    _assert_record_access(record, user, token)

    row = db.query(Report).filter(Report.analysis_id == analysis_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="report not found — generate first")
    p = Path(row.file_path)
    if not p.exists():
        raise HTTPException(status_code=410, detail="report expired or missing")
    return FileResponse(
        path=str(p),
        media_type="application/pdf",
        filename=f"deepshield_report_{analysis_id}.pdf",
    )


@router.post("/cleanup", include_in_schema=False)
def cleanup(user: User = Depends(get_current_user)):
    # Phase 15.1 — auth-guarded. Exposed only to authenticated users; an internal
    # scheduler loop in main.py handles periodic cleanup automatically.
    n = cleanup_expired()
    return {"deleted": n}
