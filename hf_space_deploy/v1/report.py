from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import AnalysisRecord, Report
from services.report_service import cleanup_expired, create_report_row, generate_report

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/{analysis_id}")
def generate(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="analysis not found")

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
def download(analysis_id: int, db: Session = Depends(get_db)):
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


@router.post("/cleanup")
def cleanup():
    n = cleanup_expired()
    return {"deleted": n}
