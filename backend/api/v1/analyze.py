import json
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, HTTPException, Request, Response, UploadFile, status
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
from services.audio_service import analyze_audio, AudioAnalysis
from services.metadata_writer import write_verdict_metadata
from services.rate_limit import ANON_ANALYZE, AUTH_ANALYZE, is_anon, is_authed, limiter
from services.dedup_cache import lookup_cached, cached_payload
from services.storage import (
    make_image_thumbnail,
    make_video_thumbnail,
    save_bytes,
    save_file,
    sha256_bytes,
    sha256_file,
)
from services.job_queue import registry as job_registry, run_job
from utils.file_handler import read_upload_bytes, save_upload_to_tempfile
from utils.scoring import compute_authenticity_score, get_verdict_label

router = APIRouter(prefix="/analyze", tags=["analyze"])

IMAGE_MAX_MB = 20
VIDEO_MAX_MB = 100
VIDEO_NUM_FRAMES = 16


@router.post("/image", response_model=ImageAnalysisResponse)
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_image(
    request: Request,
    response: Response,
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

    # Phase 19.1 — SHA-256 dedup cache
    media_hash = sha256_bytes(raw)
    cached = lookup_cached(db, media_hash=media_hash, media_type="image", user_id=user.id if user else None)
    if cached is not None:
        payload = cached_payload(cached)
        if payload is not None:
            logger.info(f"cache hit image sha={media_hash[:12]} record={cached.id}")
            return ImageAnalysisResponse.model_validate(payload)

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

    # Phase 19.2 — persist original bytes + thumbnail under content-address
    ext = (mime.split("/")[-1] if mime else "jpg").replace("jpeg", "jpg")
    try:
        media_path = save_bytes(raw, media_hash, ext)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"media save failed: {e}")
        media_path = None
    thumbnail_url = make_image_thumbnail(pil, media_hash)
    response.thumbnail_url = thumbnail_url

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="image",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump(
            exclude={"explainability": {"heatmap_base64", "ela_base64", "boxes_base64"}}
        )),
        media_hash=media_hash,
        media_path=media_path,
        thumbnail_url=thumbnail_url,
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
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_video_endpoint(
    request: Request,
    response: Response,
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

    # Phase 19.1 — dedup cache (hash temp file before running pipeline)
    media_hash = sha256_file(path)
    cached = lookup_cached(db, media_hash=media_hash, media_type="video", user_id=user.id if user else None)
    if cached is not None:
        payload = cached_payload(cached)
        if payload is not None:
            try:
                os.unlink(path)
            except OSError:
                pass
            logger.info(f"cache hit video sha={media_hash[:12]} record={cached.id}")
            return VideoAnalysisResponse.model_validate(payload)

    try:
        agg = analyze_video(path, num_frames=VIDEO_NUM_FRAMES)
        stages.append("frame_extraction")
        stages.append("frame_classification")
        stages.append("aggregation")
        if agg.temporal:
            stages.append("temporal_analysis")
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise

    # Phase 17.2 — audio analysis (needs file path, runs before cleanup)
    audio_result: AudioAnalysis | None = None
    try:
        audio_result = analyze_audio(path)
        if audio_result:
            stages.append("audio_analysis")
    except Exception as _ae:  # noqa: BLE001
        logger.warning(f"Audio analysis failed, continuing: {_ae}")

    # Phase 17.3 — combined verdict formula
    if agg.insufficient_faces:
        score = 50
        label = "Insufficient face content"
        severity = "warning"
    else:
        visual_score = (1.0 - agg.mean_suspicious_prob) * 100.0
        temporal_sc = agg.temporal.temporal_score if agg.temporal else visual_score
        if audio_result and audio_result.has_audio:
            combined = 0.50 * visual_score + 0.30 * temporal_sc + 0.20 * audio_result.audio_authenticity_score
        else:
            combined = 0.70 * visual_score + 0.30 * temporal_sc
        score = int(round(max(0.0, min(100.0, combined))))
        label, severity = get_verdict_label(score)

    duration_ms = int((time.perf_counter() - start) * 1000)

    from schemas.analyze import AudioExplainability
    audio_ex = None
    if audio_result:
        audio_ex = AudioExplainability(
            audio_authenticity_score=audio_result.audio_authenticity_score,
            has_audio=audio_result.has_audio,
            duration_s=audio_result.duration_s,
            silence_ratio=audio_result.silence_ratio,
            spectral_variance=audio_result.spectral_variance,
            rms_consistency=audio_result.rms_consistency,
            notes=audio_result.notes,
        )

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
            temporal_score=agg.temporal.temporal_score if agg.temporal else None,
            optical_flow_variance=agg.temporal.optical_flow_variance if agg.temporal else None,
            flicker_score=agg.temporal.flicker_score if agg.temporal else None,
            blink_rate_anomaly=agg.temporal.blink_rate_anomaly if agg.temporal else None,
            audio=audio_ex,
        ),
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=settings.IMAGE_MODEL_ID,
            models_used=agg.models_used,
        ),
    )

    # Phase 19.2 — persist video + thumbnail frame
    try:
        media_path = save_file(path, media_hash, suffix.lstrip("."))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"video media save failed: {e}")
        media_path = None
    thumbnail_url = make_video_thumbnail(path, media_hash)
    response.thumbnail_url = thumbnail_url

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="video",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump()),
        media_hash=media_hash,
        media_path=media_path,
        thumbnail_url=thumbnail_url,
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
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_text_endpoint(
    request: Request,
    response: Response,
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
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_screenshot_endpoint(
    request: Request,
    response: Response,
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

    # Phase 19.1 — dedup cache
    media_hash = sha256_bytes(raw)
    cached = lookup_cached(db, media_hash=media_hash, media_type="screenshot", user_id=user.id if user else None)
    if cached is not None:
        payload = cached_payload(cached)
        if payload is not None:
            logger.info(f"cache hit screenshot sha={media_hash[:12]} record={cached.id}")
            return ScreenshotAnalysisResponse.model_validate(payload)

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

    # Phase 19.2 — object storage + thumbnail
    ext = (mime.split("/")[-1] if mime else "jpg").replace("jpeg", "jpg")
    try:
        media_path = save_bytes(raw, media_hash, ext)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"screenshot media save failed: {e}")
        media_path = None
    thumbnail_url = make_image_thumbnail(pil, media_hash)
    response.thumbnail_url = thumbnail_url

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="screenshot",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(response.model_dump()),
        media_hash=media_hash,
        media_path=media_path,
        thumbnail_url=thumbnail_url,
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


# ───────────────────────── Phase 19.3 — async video + jobs ─────────────────────────

@router.post("/video/async", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_video_async(
    request: Request,
    response: Response,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
):
    """Queue a video analysis and return a job_id. Poll GET /api/v1/jobs/{job_id}.

    Used by the PipelineVisualizer so it can read real backend stage/progress
    instead of guessing timing.
    """
    suffix = os.path.splitext(file.filename or "")[1].lower() or ".mp4"
    path, _mime = await save_upload_to_tempfile(
        file, settings.ALLOWED_VIDEO_TYPES, max_size_mb=VIDEO_MAX_MB, suffix=suffix
    )

    # Quick cache probe so callers don't wait for queue dispatch on repeats.
    media_hash = sha256_file(path)
    cached = lookup_cached(db, media_hash=media_hash, media_type="video", user_id=user.id if user else None)
    if cached is not None:
        payload = cached_payload(cached)
        try:
            os.unlink(path)
        except OSError:
            pass
        if payload is not None:
            job = job_registry.create()
            job_registry.update(job.id, status="done", stage="done", progress=100, result=payload)
            return {"job_id": job.id, "status": "done", "cached": True}

    user_id = user.id if user else None
    job = job_registry.create()

    def _work(progress):
        from db.database import SessionLocal
        local_db = SessionLocal()
        try:
            progress("frame_extraction", 15)
            agg = analyze_video(path, num_frames=VIDEO_NUM_FRAMES)
            progress("aggregation", 60)

            audio_result = None
            try:
                audio_result = analyze_audio(path)
            except Exception as _ae:  # noqa: BLE001
                logger.warning(f"Audio analysis failed, continuing: {_ae}")
            progress("audio_analysis", 75)

            if agg.insufficient_faces:
                score_val, label_val, sev = 50, "Insufficient face content", "warning"
            else:
                visual_score = (1.0 - agg.mean_suspicious_prob) * 100.0
                temporal_sc = agg.temporal.temporal_score if agg.temporal else visual_score
                if audio_result and audio_result.has_audio:
                    combined = 0.50 * visual_score + 0.30 * temporal_sc + 0.20 * audio_result.audio_authenticity_score
                else:
                    combined = 0.70 * visual_score + 0.30 * temporal_sc
                score_val = int(round(max(0.0, min(100.0, combined))))
                label_val, sev = get_verdict_label(score_val)

            from schemas.analyze import AudioExplainability
            audio_ex = None
            if audio_result:
                audio_ex = AudioExplainability(
                    audio_authenticity_score=audio_result.audio_authenticity_score,
                    has_audio=audio_result.has_audio,
                    duration_s=audio_result.duration_s,
                    silence_ratio=audio_result.silence_ratio,
                    spectral_variance=audio_result.spectral_variance,
                    rms_consistency=audio_result.rms_consistency,
                    notes=audio_result.notes,
                )

            resp = VideoAnalysisResponse(
                analysis_id=str(uuid.uuid4()),
                media_type="video",
                timestamp=datetime.now(timezone.utc).isoformat(),
                verdict=Verdict(
                    label=label_val, severity=sev,
                    authenticity_score=score_val,
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
                            index=f.index, timestamp_s=f.timestamp_s,
                            label=f.label, confidence=f.confidence,
                            suspicious_prob=f.suspicious_prob, is_suspicious=f.is_suspicious,
                            has_face=f.has_face, scored=f.scored,
                        ) for f in agg.frames
                    ],
                    temporal_score=agg.temporal.temporal_score if agg.temporal else None,
                    optical_flow_variance=agg.temporal.optical_flow_variance if agg.temporal else None,
                    flicker_score=agg.temporal.flicker_score if agg.temporal else None,
                    blink_rate_anomaly=agg.temporal.blink_rate_anomaly if agg.temporal else None,
                    audio=audio_ex,
                ),
                processing_summary=ProcessingSummary(
                    stages_completed=["frame_extraction", "classification", "aggregation"],
                    total_duration_ms=0,
                    model_used=settings.IMAGE_MODEL_ID,
                    models_used=agg.models_used,
                ),
            )

            progress("storage", 85)
            try:
                media_path = save_file(path, media_hash, suffix.lstrip("."))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"async video media save failed: {e}")
                media_path = None
            thumb = make_video_thumbnail(path, media_hash)
            resp.thumbnail_url = thumb

            rec = AnalysisRecord(
                user_id=user_id,
                media_type="video",
                verdict=label_val,
                authenticity_score=float(score_val),
                result_json=json.dumps(resp.model_dump()),
                media_hash=media_hash,
                media_path=media_path,
                thumbnail_url=thumb,
            )
            local_db.add(rec)
            local_db.commit()
            local_db.refresh(rec)
            resp.record_id = rec.id
            progress("persist", 95)

            return resp.model_dump()
        finally:
            local_db.close()
            try:
                os.unlink(path)
            except OSError:
                pass

    stages = ["queued", "frame_extraction", "aggregation", "audio_analysis", "storage", "persist", "done"]
    background.add_task(run_job, job.id, stages, _work)
    return {"job_id": job.id, "status": "queued", "cached": False}


jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


@jobs_router.get("/{job_id}")
def get_job(job_id: str):
    j = job_registry.get(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": j.id,
        "status": j.status,
        "stage": j.stage,
        "progress": j.progress,
        "error": j.error,
        "result": j.result if j.status == "done" else None,
    }
