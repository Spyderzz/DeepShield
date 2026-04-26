"""Phase 19.1 — SHA-256 media dedup cache.

Looks up a prior AnalysisRecord by content hash within CACHE_TTL_DAYS, and
returns the cached payload so repeated uploads of the same file skip the
expensive analyzer pipelines.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy.orm import Session

from db.models import AnalysisRecord
from schemas.common import ANALYSIS_CACHE_VERSION

CACHE_TTL_DAYS = int(os.environ.get("CACHE_TTL_DAYS", "30"))


def lookup_cached(
    db: Session,
    *,
    media_hash: str,
    media_type: str,
    user_id: int | None,
) -> AnalysisRecord | None:
    """Return a cached AnalysisRecord for this hash+type if within TTL.

    We scope the cache by user when the user is signed in (their own history
    should return their own cached record) and globally when anonymous.
    """
    if not media_hash:
        return None
    cutoff = datetime.utcnow() - timedelta(days=CACHE_TTL_DAYS)
    q = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.media_hash == media_hash,
            AnalysisRecord.media_type == media_type,
            AnalysisRecord.created_at >= cutoff,
        )
        .order_by(AnalysisRecord.created_at.desc())
    )
    if user_id is not None:
        return q.filter(AnalysisRecord.user_id == user_id).first()
    return q.filter(AnalysisRecord.user_id.is_(None)).first()


def cached_payload(record: AnalysisRecord) -> dict | None:
    """Decode stored result_json and stamp the cached flag."""
    try:
        payload = json.loads(record.result_json)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"cached payload decode failed for record {record.id}: {e}")
        return None
    summary = payload.get("processing_summary") or {}
    if summary.get("analysis_version") != ANALYSIS_CACHE_VERSION:
        logger.info(f"cache stale for record {record.id}: analysis_version mismatch")
        return None
    payload["cached"] = True
    payload["record_id"] = record.id
    return payload
