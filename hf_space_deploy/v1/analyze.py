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
from models.heatmap_generator import generate_heatmap_base64, generate_boxes_base64
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
from services.ela_service import generate_ela_base64
from services.exif_service import extract_exif
from services.image_service import load_image_from_bytes
from services.llm_explainer import generate_llm_summary
from schemas.common import ProcessingSummary, Verdict
from services.artifact_detector import scan_artifacts
from services.image_service import preprocess_and_classify
from services.news_lookup import search_news_full
from services.vlm_breakdown import generate_vlm_breakdown
from services.text_service import (
    classify_text,
    detect_language,
    detect_manipulation_indicators,
    extract_entities,
    score_sensationalism,
)
from services.video_service import analyze_video
from services.metadata_writer import write_verdict_metadata
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

    # ── Phase 12: Grad-CAM++ heatmap ──
    heatmap_status = "success"
    heatmap = ""
    try:
        model_family = "efficientnet" if settings.ENSEMBLE_MODE else "vit"
        heatmap, heatmap_source = generate_heatmap_base64(pil, model_family=model_family)
        if not heatmap:
            heatmap_status = heatmap_source  # "none" or "fallback"
        stages.append("heatmap_generation")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Heatmap generation failed, continuing: {e}")
        heatmap_status = "failed"

    # ── Phase 12: ELA (Error Level Analysis) ──
    ela_b64 = ""
    try:
        ela_b64 = generate_ela_base64(pil)
        stages.append("ela_generation")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"ELA generation failed, continuing: {e}")

    # ── Phase 12: Bounding box mode ──
    boxes_b64 = ""
    try:
        boxes_b64 = generate_boxes_base64(pil)
        stages.append("boxes_generation")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Bounding box generation failed, continuing: {e}")

    # ── Phase 12: EXIF extraction + trust adjustment ──
    exif_summary = None
    try:
        exif_summary = extract_exif(pil, raw)
        stages.append("exif_extraction")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"EXIF extraction failed, continuing: {e}")

    score = compute_authenticity_score(clf.confidence, clf.label)

    # Apply EXIF trust adjustment to the score
    if exif_summary and exif_summary.trust_adjustment != 0:
        score = int(round(max(0, min(100, score + exif_summary.trust_adjustment))))

    label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    analysis_id = str(uuid.uuid4())

    response = ImageAnalysisResponse(
        analysis_id=analysis_id,
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
            ela_base64=ela_b64,
            boxes_base64=boxes_b64,
            heatmap_status=heatmap_status,
            artifact_indicators=indicators,
            exif=exif_summary,
        ),
        trusted_sources=[],
        contradicting_evidence=[],
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=settings.IMAGE_MODEL_ID,
            models_used=clf.models_used,
        ),
    )

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="image",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump(
            exclude={"explainability": {"heatmap_base64", "ela_base64", "boxes_base64"}}
        )),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    response.record_id = record.id
    logger.info(f"Saved AnalysisRecord id={record.id} score={score} verdict={label}")

    # ── Phase 12: LLM explainability card (runs after DB save so we have record_id) ──
    try:
        llm_summary = generate_llm_summary(
            payload=response.model_dump(
                exclude={"explainability": {"heatmap_base64", "ela_base64", "boxes_base64"}}
            ),
            record_id=str(record.id),
        )
        response.explainability.llm_summary = llm_summary
        stages.append("llm_explanation")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LLM explainer failed, continuing: {e}")

    # ── Phase 14: VLM detailed breakdown (vision LLM scores 6 perceptual components) ──
    try:
        vlm_bd = generate_vlm_breakdown(pil, record_id=str(record.id))
        if vlm_bd:
            response.explainability.vlm_breakdown = vlm_bd
            stages.append("vlm_breakdown")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"VLM breakdown failed, continuing: {e}")

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
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise

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
            models_used=agg.models_used,
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

    # Write verdict into video metadata (ExifTool, optional — gated by EXIFTOOL_PATH).
    try:
        write_verdict_metadata(
            file_path=path,
            verdict=label,
            authenticity_score=score,
            models_used=agg.models_used,
            analysis_id=str(record.id),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Metadata write failed: {e}")
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    # Phase 12: LLM explainability card
    try:
        response.llm_summary = generate_llm_summary(
            payload=response.model_dump(), record_id=str(record.id),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LLM explainer failed for video: {e}")

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

    # Phase 13: language detection — routes to multilang model when non-English
    lang = detect_language(body.text)
    stages.append("language_detection")

    clf = classify_text(body.text, language=lang)
    stages.append("classification")

    sens = score_sensationalism(body.text)
    stages.append("sensationalism_analysis")

    manip = detect_manipulation_indicators(body.text)
    stages.append("manipulation_detection")

    # Phase 13.1: NER-based keyword extraction (spaCy entities first, frequency fallback)
    keywords = extract_entities(body.text)
    stages.append("ner_keyword_extraction")

    # Phase 13.2: pass original text + current fake_prob for truth-override computation
    news = await search_news_full(
        keywords,
        original_text=body.text,
        current_fake_prob=clf.fake_prob,
    )
    stages.append("news_lookup")

    # Apply truth-override to fake_prob before scoring
    effective_fake_prob = clf.fake_prob
    if news.truth_override and news.truth_override.applied:
        effective_fake_prob = news.truth_override.fake_prob_after
        stages.append("truth_override_applied")

    # Weighted score: 70% classifier + 20% inverse sensationalism + 10% manipulation penalty
    manip_penalty = min(len(manip) * 5, 30)
    raw_score = (1.0 - effective_fake_prob) * 100.0
    weighted = raw_score * 0.70 + max(0, 100 - sens.score) * 0.20 + max(0, 100 - manip_penalty) * 0.10
    score = int(round(max(0.0, min(100.0, weighted))))
    label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    model_used = (
        settings.TEXT_MULTILANG_MODEL_ID if (lang != "en" and settings.TEXT_MULTILANG_MODEL_ID)
        else settings.TEXT_MODEL_ID
    )

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
            fake_probability=effective_fake_prob,
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
            detected_language=lang,
            truth_override=news.truth_override,
        ),
        trusted_sources=news.trusted_sources,
        contradicting_evidence=news.contradicting_evidence,
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=model_used,
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

    # Phase 12: LLM explainability card
    try:
        response.llm_summary = generate_llm_summary(
            payload=response.model_dump(), record_id=str(record.id),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LLM explainer failed for text: {e}")

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

    # Phase 13: language detection on extracted OCR text
    lang = detect_language(full_text) if full_text else "en"
    stages.append("language_detection")

    clf = classify_text(full_text, language=lang) if full_text else None
    stages.append("classification")

    sens = score_sensationalism(full_text)
    stages.append("sensationalism_analysis")

    manip = detect_manipulation_indicators(full_text)
    stages.append("manipulation_detection")

    phrases = map_phrases_to_boxes(ocr_boxes, manip)
    stages.append("phrase_overlay_mapping")

    layout = detect_layout_anomalies(ocr_boxes)
    stages.append("layout_anomaly_detection")

    # Phase 13.1: NER-based keyword extraction
    keywords = extract_entities(full_text)
    stages.append("ner_keyword_extraction")

    fake_prob = clf.fake_prob if clf else 0.0
    model_conf = clf.confidence if clf else 0.0
    model_lbl = clf.label if clf else "no_text"

    # Phase 13.2: truth-override via cosine similarity
    news = await search_news_full(
        keywords,
        original_text=full_text,
        current_fake_prob=fake_prob,
    )
    stages.append("news_lookup")

    effective_fake_prob = fake_prob
    if news.truth_override and news.truth_override.applied:
        effective_fake_prob = news.truth_override.fake_prob_after
        stages.append("truth_override_applied")

    manip_penalty = min(len(manip) * 5, 30)
    layout_penalty = min(len(layout) * 5, 15)
    raw_score = (1.0 - effective_fake_prob) * 100.0
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

    model_used_str = (
        f"{settings.TEXT_MULTILANG_MODEL_ID} + EasyOCR"
        if (lang != "en" and settings.TEXT_MULTILANG_MODEL_ID)
        else f"{settings.TEXT_MODEL_ID} + EasyOCR"
    )

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
            fake_probability=effective_fake_prob,
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
            detected_language=lang,
            truth_override=news.truth_override,
        ),
        trusted_sources=news.trusted_sources,
        contradicting_evidence=news.contradicting_evidence,
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=model_used_str,
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

    # Phase 12: LLM explainability card
    try:
        response.llm_summary = generate_llm_summary(
            payload=response.model_dump(), record_id=str(record.id),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LLM explainer failed for screenshot: {e}")

    return response
