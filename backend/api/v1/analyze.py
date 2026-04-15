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

from api.deps import optional_current_user
from config import settings
from db.database import get_db
from db.models import AnalysisRecord, User
from models.heatmap_generator import generate_heatmap_base64
from schemas.analyze import (
    FrameAnalysisOut,
    ImageAnalysisResponse,
    ImageExplainability,
    LayoutAnomalyOut,
    ManipulationIndicatorOut,
    OCRBoxOut,
    ScreenshotAnalysisResponse,
    ScreenshotExplainability,
    SensationalismBreakdown,
    SuspiciousPhraseOut,
    TextAnalysisResponse,
    TextExplainability,
    VideoAnalysisResponse,
    VideoExplainability,
)
from services.screenshot_service import (
    detect_layout_anomalies,
    extract_full_text,
    map_phrases_to_boxes,
    run_ocr,
)
from services.image_service import load_image_from_bytes
from schemas.common import ProcessingSummary, Verdict
from services.artifact_detector import scan_artifacts
from services.image_service import preprocess_and_classify
from services.news_lookup import search_news_full
from services.text_service import classify_text, detect_manipulation_indicators, extract_keywords, score_sensationalism
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
    user: User | None = Depends(optional_current_user),
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
        user_id=user.id if user else None,
        media_type="image",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump(exclude={"explainability": {"heatmap_base64"}})),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    response.record_id = record.id
    logger.info(f"Saved AnalysisRecord id={record.id} score={score} verdict={label}")

    return response


@router.post("/video", response_model=VideoAnalysisResponse)
async def analyze_video_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
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
        user_id=user.id if user else None,
        media_type="video",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    response.record_id = record.id
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
    user: User | None = Depends(optional_current_user),
) -> TextAnalysisResponse:
    start = time.perf_counter()
    stages: list[str] = []

    clf = classify_text(body.text)
    stages.append("classification")

    sens = score_sensationalism(body.text)
    stages.append("sensationalism_analysis")

    manip = detect_manipulation_indicators(body.text)
    stages.append("manipulation_detection")

    keywords = extract_keywords(body.text)
    stages.append("keyword_extraction")

    news = await search_news_full(keywords)
    stages.append("news_lookup")

    # Weighted score: 70% classifier + 20% inverse sensationalism + 10% manipulation penalty
    manip_penalty = min(len(manip) * 5, 30)  # up to 30 points penalty
    raw_score = (1.0 - clf.fake_prob) * 100.0
    weighted = raw_score * 0.70 + max(0, 100 - sens.score) * 0.20 + max(0, 100 - manip_penalty) * 0.10
    score = int(round(max(0.0, min(100.0, weighted))))
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
            sensationalism=SensationalismBreakdown(
                score=sens.score,
                level=sens.level,
                exclamation_count=sens.exclamation_count,
                caps_word_count=sens.caps_word_count,
                clickbait_matches=sens.clickbait_matches,
                emotional_word_count=sens.emotional_word_count,
                superlative_count=sens.superlative_count,
            ),
            manipulation_indicators=[
                ManipulationIndicatorOut(
                    pattern_type=m.pattern_type,
                    matched_text=m.matched_text,
                    start_pos=m.start_pos,
                    end_pos=m.end_pos,
                    severity=m.severity,
                    description=m.description,
                )
                for m in manip
            ],
        ),
        trusted_sources=news.trusted_sources,
        contradicting_evidence=news.contradicting_evidence,
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=settings.TEXT_MODEL_ID,
        ),
    )

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="text",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    response.record_id = record.id
    logger.info(f"Saved AnalysisRecord id={record.id} text score={score} verdict={label}")

    return response


@router.post("/screenshot", response_model=ScreenshotAnalysisResponse)
async def analyze_screenshot_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
) -> ScreenshotAnalysisResponse:
    start = time.perf_counter()
    stages: list[str] = []

    raw, mime = await read_upload_bytes(
        file, settings.ALLOWED_IMAGE_TYPES, max_size_mb=IMAGE_MAX_MB
    )
    stages.append("validation")

    pil = load_image_from_bytes(raw)
    ocr_boxes = run_ocr(pil)
    stages.append("ocr")

    full_text = extract_full_text(ocr_boxes)

    clf = classify_text(full_text) if full_text else None
    stages.append("classification")

    sens = score_sensationalism(full_text)
    stages.append("sensationalism_analysis")

    manip = detect_manipulation_indicators(full_text)
    stages.append("manipulation_detection")

    phrases = map_phrases_to_boxes(ocr_boxes, manip)
    stages.append("phrase_overlay_mapping")

    layout = detect_layout_anomalies(ocr_boxes)
    stages.append("layout_anomaly_detection")

    keywords = extract_keywords(full_text)
    stages.append("keyword_extraction")

    news = await search_news_full(keywords)
    stages.append("news_lookup")

    fake_prob = clf.fake_prob if clf else 0.0
    model_conf = clf.confidence if clf else 0.0
    model_lbl = clf.label if clf else "no_text"

    manip_penalty = min(len(manip) * 5, 30)
    layout_penalty = min(len(layout) * 5, 15)
    raw_score = (1.0 - fake_prob) * 100.0
    weighted = (
        raw_score * 0.65
        + max(0, 100 - sens.score) * 0.20
        + max(0, 100 - manip_penalty) * 0.10
        + max(0, 100 - layout_penalty) * 0.05
    )
    if not full_text.strip():
        weighted = 50
    score = int(round(max(0.0, min(100.0, weighted))))
    label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    response = ScreenshotAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        media_type="screenshot",
        timestamp=datetime.now(timezone.utc).isoformat(),
        verdict=Verdict(
            label=label,
            severity=severity,
            authenticity_score=score,
            model_confidence=float(model_conf),
            model_label=model_lbl,
        ),
        explainability=ScreenshotExplainability(
            extracted_text=full_text,
            ocr_boxes=[OCRBoxOut(text=b.text, bbox=b.bbox, confidence=b.confidence) for b in ocr_boxes],
            fake_probability=fake_prob,
            sensationalism=SensationalismBreakdown(
                score=sens.score, level=sens.level,
                exclamation_count=sens.exclamation_count, caps_word_count=sens.caps_word_count,
                clickbait_matches=sens.clickbait_matches, emotional_word_count=sens.emotional_word_count,
                superlative_count=sens.superlative_count,
            ),
            suspicious_phrases=[
                SuspiciousPhraseOut(
                    text=p.text, bbox=p.bbox, pattern_type=p.pattern_type,
                    severity=p.severity, description=p.description,
                ) for p in phrases
            ],
            layout_anomalies=[
                LayoutAnomalyOut(
                    type=la.type, severity=la.severity,
                    description=la.description, confidence=la.confidence,
                ) for la in layout
            ],
            keywords=keywords,
        ),
        trusted_sources=news.trusted_sources,
        contradicting_evidence=news.contradicting_evidence,
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=f"{settings.TEXT_MODEL_ID} + EasyOCR",
        ),
    )

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="screenshot",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    response.record_id = record.id
    logger.info(f"Saved AnalysisRecord id={record.id} screenshot score={score} verdict={label}")

    return response
