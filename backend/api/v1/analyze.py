from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, File, UploadFile
from pydantic import BaseModel
from loguru import logger
from sqlalchemy.orm import Session

from config import settings
from db.database import get_db
from db.models import AnalysisRecord
from models.heatmap_generator import generate_heatmap_base64
from schemas.analyze import (
    FrameAnalysisOut,
    ImageAnalysisResponse,
    ImageExplainability,
    TextAnalysisResponse,
    TextExplainability,
    VideoAnalysisResponse,
    VideoExplainability,
)
from schemas.common import ProcessingSummary, Verdict
from services.artifact_detector import scan_artifacts
from services.image_service import preprocess_and_classify
from services.news_lookup import search_news
from services.text_service import classify_text, extract_keywords
from services.video_service import analyze_video
from utils.file_handler import read_upload_bytes, save_upload_to_tempfile
from utils.scoring import compute_authenticity_score, get_verdict_label

router = APIRouter(prefix="/analyze", tags=["analyze"])

IMAGE_MAX_MB = 20
VIDEO_MAX_MB = 100
VIDEO_NUM_FRAMES = 16


@router.post("/image", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImageAnalysisResponse:
    start = time.perf_counter()
    stages: list[str] = []

    raw, mime = await read_upload_bytes(
        file, settings.ALLOWED_IMAGE_TYPES, max_size_mb=IMAGE_MAX_MB
    )
    stages.append("validation")

    pil, clf = preprocess_and_classify(raw)
    stages.append("classification")

    indicators = scan_artifacts(pil, raw)
    stages.append("artifact_scanning")

    try:
        heatmap = generate_heatmap_base64(pil)
        stages.append("heatmap_generation")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Heatmap generation failed, continuing: {e}")
        heatmap = ""

    score = compute_authenticity_score(clf.confidence, clf.label)
    label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    response = ImageAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        media_type="image",
        timestamp=datetime.now(timezone.utc).isoformat(),
        verdict=Verdict(
            label=label,
            severity=severity,
            authenticity_score=score,
            model_confidence=clf.confidence,
            model_label=clf.label,
        ),
        explainability=ImageExplainability(
            heatmap_base64=heatmap,
            artifact_indicators=indicators,
        ),
        trusted_sources=[],
        contradicting_evidence=[],
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=settings.IMAGE_MODEL_ID,
        ),
    )

    record = AnalysisRecord(
        media_type="image",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump(exclude={"explainability": {"heatmap_base64"}})),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Saved AnalysisRecord id={record.id} score={score} verdict={label}")

    return response


@router.post("/video", response_model=VideoAnalysisResponse)
async def analyze_video_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> VideoAnalysisResponse:
    start = time.perf_counter()
    stages: list[str] = []

    suffix = os.path.splitext(file.filename or "")[1].lower() or ".mp4"
    path, mime = await save_upload_to_tempfile(
        file, settings.ALLOWED_VIDEO_TYPES, max_size_mb=VIDEO_MAX_MB, suffix=suffix
    )
    stages.append("validation")

    try:
        agg = analyze_video(path, num_frames=VIDEO_NUM_FRAMES)
        stages.append("frame_extraction")
        stages.append("frame_classification")
        stages.append("aggregation")
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if agg.insufficient_faces:
        score = 50
        label = "Insufficient face content"
        severity = "warning"
    else:
        score = int(round(max(0.0, min(100.0, (1.0 - agg.mean_suspicious_prob) * 100.0))))
        label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    response = VideoAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        media_type="video",
        timestamp=datetime.now(timezone.utc).isoformat(),
        verdict=Verdict(
            label=label,
            severity=severity,
            authenticity_score=score,
            model_confidence=float(agg.mean_suspicious_prob),
            model_label="suspicious_mean" if not agg.insufficient_faces else "no_faces",
        ),
        explainability=VideoExplainability(
            num_frames_sampled=agg.num_frames_sampled,
            num_face_frames=agg.num_face_frames,
            num_suspicious_frames=agg.num_suspicious_frames,
            mean_suspicious_prob=agg.mean_suspicious_prob,
            max_suspicious_prob=agg.max_suspicious_prob,
            suspicious_ratio=agg.suspicious_ratio,
            insufficient_faces=agg.insufficient_faces,
            suspicious_timestamps=agg.suspicious_timestamps,
            frames=[
                FrameAnalysisOut(
                    index=f.index,
                    timestamp_s=f.timestamp_s,
                    label=f.label,
                    confidence=f.confidence,
                    suspicious_prob=f.suspicious_prob,
                    is_suspicious=f.is_suspicious,
                    has_face=f.has_face,
                    scored=f.scored,
                )
                for f in agg.frames
            ],
        ),
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=settings.IMAGE_MODEL_ID,
        ),
    )

    record = AnalysisRecord(
        media_type="video",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(
        f"Saved AnalysisRecord id={record.id} video score={score} verdict={label} "
        f"frames={agg.num_frames_sampled} susp={agg.num_suspicious_frames}"
    )

    return response


class TextAnalyzeBody(BaseModel):
    text: str


@router.post("/text", response_model=TextAnalysisResponse)
async def analyze_text_endpoint(
    body: TextAnalyzeBody = Body(...),
    db: Session = Depends(get_db),
) -> TextAnalysisResponse:
    start = time.perf_counter()
    stages: list[str] = []

    clf = classify_text(body.text)
    stages.append("classification")

    keywords = extract_keywords(body.text)
    stages.append("keyword_extraction")

    sources = await search_news(keywords)
    stages.append("news_lookup")

    score = int(round(max(0.0, min(100.0, (1.0 - clf.fake_prob) * 100.0))))
    label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    response = TextAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        media_type="text",
        timestamp=datetime.now(timezone.utc).isoformat(),
        verdict=Verdict(
            label=label,
            severity=severity,
            authenticity_score=score,
            model_confidence=float(clf.confidence),
            model_label=clf.label,
        ),
        explainability=TextExplainability(
            fake_probability=clf.fake_prob,
            top_label=clf.label,
            all_scores=clf.all_scores,
            keywords=keywords,
        ),
        trusted_sources=sources,
        contradicting_evidence=[],
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=settings.TEXT_MODEL_ID,
        ),
    )

    record = AnalysisRecord(
        media_type="text",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Saved AnalysisRecord id={record.id} text score={score} verdict={label}")

    return response
