from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user, optional_current_user
from config import settings
from db.database import get_db
from db.models import AnalysisRecord, User

router = APIRouter(prefix="/history", tags=["history"])


class HistoryItem(BaseModel):
    id: int
    media_type: str
    verdict: str
    authenticity_score: float
    created_at: datetime
    thumbnail_url: str | None = None
    thumbnail_b64: str | None = None  # inline data URL; preferred over thumbnail_url
    media_path: str | None = None
    text_preview: str | None = None


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    cache_hits: int = 0


class HistoryDeleteAllResponse(BaseModel):
    deleted: int


def _analysis_token(record: AnalysisRecord) -> str | None:
    try:
        payload = json.loads(record.result_json)
    except Exception:
        return None
    token = payload.get("analysis_id")
    return str(token) if token else None


def _asset_sig(record_id: int, kind: str, exp: int, token: str | None = None) -> str:
    body = f"{record_id}:{kind}:{exp}:{token or ''}"
    return hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()


def _make_asset_url(record_id: int, kind: str, token: str | None = None) -> str:
    ttl = max(60, int(settings.MEDIA_SIGNED_URL_TTL_SECONDS))
    exp = int(datetime.now().timestamp()) + ttl
    sig = _asset_sig(record_id, kind, exp, token)
    url = f"/api/v1/history/{record_id}/asset/{kind}?exp={exp}&sig={sig}"
    if token:
        url += f"&token={token}"
    return url


def _path_from_media_url(value: str | None) -> Path | None:
    if not value:
        return None
    raw = str(value).replace("\\", "/")
    media_root = Path(settings.MEDIA_ROOT).resolve()

    if raw.startswith("/media/"):
        rel = raw[len("/media/") :].lstrip("/")
        return (media_root / rel).resolve()
    if raw.startswith("media/"):
        rel = raw[len("media/") :].lstrip("/")
        return (media_root / rel).resolve()
    if raw.startswith("./media/"):
        rel = raw[len("./media/") :].lstrip("/")
        return (media_root / rel).resolve()

    p = Path(raw)
    if p.is_absolute():
        return p.resolve()
    return (media_root / raw.lstrip("/")).resolve()


def _guard_media_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    media_root = Path(settings.MEDIA_ROOT).resolve()
    try:
        path.relative_to(media_root)
        return path
    except Exception:
        return None


def _rewrite_secure_urls(record: AnalysisRecord, payload: dict, token: str | None = None) -> dict:
    payload["thumbnail_url"] = _make_asset_url(record.id, "thumbnail", token) if record.thumbnail_url else None
    payload["media_path"] = _make_asset_url(record.id, "media", token) if record.media_path else None

    explainability = payload.get("explainability")
    if isinstance(explainability, dict):
        if explainability.get("heatmap_url"):
            explainability["heatmap_url"] = _make_asset_url(record.id, "heatmap", token)
        if explainability.get("ela_url"):
            explainability["ela_url"] = _make_asset_url(record.id, "ela", token)
        if explainability.get("boxes_url"):
            explainability["boxes_url"] = _make_asset_url(record.id, "boxes", token)
    return payload


def _text_preview_from_json(result_json: str, limit: int = 260) -> str | None:
    try:
        payload = json.loads(result_json)
    except Exception:
        return None
    explainability = payload.get("explainability")
    if not isinstance(explainability, dict):
        return None
    text = " ".join(str(explainability.get("original_text") or "").split())
    if not text:
        return None
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."



def _count_cache_hits(db: Session, user_id: int) -> int:
    """Count analyses whose media_hash matches an earlier record for this user.
    Each duplicate re-submission that was served from cache is a cache hit.
    """
    from sqlalchemy import func, text as sa_text
    try:
        result = db.execute(
            sa_text(
                "SELECT COUNT(*) FROM analyses a1 "
                "WHERE a1.user_id = :uid AND a1.media_hash IS NOT NULL "
                "AND EXISTS ("
                "  SELECT 1 FROM analyses a2 "
                "  WHERE a2.user_id = :uid AND a2.media_hash = a1.media_hash "
                "  AND a2.id < a1.id"
                ")"
            ),
            {"uid": user_id},
        )
        row = result.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


@router.get("", response_model=HistoryListResponse)
def list_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    # Project only lightweight columns — result_json is excluded because it can
    # be hundreds of KB per row (full analysis JSON with embedded base64 images).
    base_filter = AnalysisRecord.user_id == user.id
    total = db.query(AnalysisRecord.id).filter(base_filter).count()

    rows = (
        db.query(
            AnalysisRecord.id,
            AnalysisRecord.media_type,
            AnalysisRecord.verdict,
            AnalysisRecord.authenticity_score,
            AnalysisRecord.created_at,
            AnalysisRecord.media_path,
            AnalysisRecord.thumbnail_url,
        )
        .filter(base_filter)
        .order_by(AnalysisRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # For text records only, fetch result_json in one batched query for text previews.
    text_ids = [r.id for r in rows if r.media_type == "text"]
    text_previews: dict[int, str | None] = {}
    if text_ids:
        for rec in (
            db.query(AnalysisRecord.id, AnalysisRecord.result_json)
            .filter(AnalysisRecord.id.in_(text_ids))
            .all()
        ):
            text_previews[rec.id] = _text_preview_from_json(rec.result_json)

    items = [
        HistoryItem(
            id=r.id,
            media_type=r.media_type,
            verdict=r.verdict,
            authenticity_score=r.authenticity_score,
            created_at=r.created_at,
            thumbnail_url=_make_asset_url(r.id, "thumbnail") if r.thumbnail_url else None,
            thumbnail_b64=None,  # omitted from list — signed URL serves the thumbnail
            media_path=_make_asset_url(r.id, "media") if r.media_path else None,
            text_preview=text_previews.get(r.id),
        )
        for r in rows
    ]
    cache_hits = _count_cache_hits(db, user.id)
    return HistoryListResponse(items=items, total=total, cache_hits=cache_hits)


@router.get("/{record_id}")
def get_history_detail(
    record_id: int,
    token: str | None = Query(None),
    user: User | None = Depends(optional_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
    if not r:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")
    if user is None or r.user_id != user.id:
        if r.user_id is not None or not token:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")
        try:
            token_payload = json.loads(r.result_json)
        except Exception:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Corrupt result payload")
        if token_payload.get("analysis_id") != token:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")
    try:
        payload = json.loads(r.result_json)
        # Inject storage fields from DB columns so the frontend can display full-size media
        if r.media_path and not payload.get("media_path"):
            payload["media_path"] = r.media_path
        if r.thumbnail_url and not payload.get("thumbnail_url"):
            payload["thumbnail_url"] = r.thumbnail_url
        signed_token = token if user is None else None
        return _rewrite_secure_urls(r, payload, signed_token)
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Corrupt result payload")


@router.get("/{record_id}/asset/{kind}")
def get_history_asset(
    record_id: int,
    kind: str,
    exp: int = Query(..., ge=1),
    sig: str = Query(..., min_length=16),
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    if exp < int(datetime.now().timestamp()):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Asset link expired")

    r = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
    if not r:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")

    expected = _asset_sig(r.id, kind, exp, token)
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid asset signature")

    if r.user_id is None:
        record_token = _analysis_token(r)
        if not token or not record_token or token != record_token:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")

    explainability = None
    if kind in {"heatmap", "ela", "boxes"}:
        try:
            payload = json.loads(r.result_json)
            explainability = payload.get("explainability") if isinstance(payload, dict) else None
        except Exception:
            explainability = None

    source = None
    if kind == "thumbnail":
        source = r.thumbnail_url
    elif kind == "media":
        source = r.media_path
    elif kind == "heatmap" and isinstance(explainability, dict):
        source = explainability.get("heatmap_url")
    elif kind == "ela" and isinstance(explainability, dict):
        source = explainability.get("ela_url")
    elif kind == "boxes" and isinstance(explainability, dict):
        source = explainability.get("boxes_url")
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")

    path = _guard_media_path(_path_from_media_url(source))
    if path is None or not path.exists() or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")

    return FileResponse(path)


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


@router.delete("", response_model=HistoryDeleteAllResponse)
def delete_all_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryDeleteAllResponse:
    deleted = db.query(AnalysisRecord).filter(AnalysisRecord.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return HistoryDeleteAllResponse(deleted=deleted)
