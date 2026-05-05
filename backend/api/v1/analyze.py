import asyncio
import json
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
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
    AudioAnalysisResponse,
    AudioStandaloneExplainability,
    AudioMLScore,
)
from services.screenshot_service import (
    detect_layout_anomalies,
    extract_full_text,
    map_phrases_to_boxes,
    run_ocr,
)
from services.ela_service import generate_ela_base64
from services.exif_service import extract_exif
from services.image_service import classify_image, load_image_from_bytes
from services.llm_explainer import generate_llm_summary
from schemas.common import ProcessingSummary, Verdict
from services.artifact_detector import scan_artifacts
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
    save_overlay,
    sha256_bytes,
    sha256_file,
)
from services.job_queue import registry as job_registry, run_job
from utils.file_handler import read_upload_bytes, save_upload_to_tempfile
from utils.scoring import compute_authenticity_score, compute_video_authenticity_score, get_verdict_label

router = APIRouter(prefix="/analyze", tags=["analyze"])

IMAGE_MAX_MB = 20
_VIS_MAX_PX = 1024  # max pixel dimension for forensic visualizations


def _resize_for_vis(pil) -> "Image.Image":
    """Downsample to _VIS_MAX_PX on the longest side, preserving aspect ratio.
    Forensic overlays (heatmap, ELA, boxes) don't need original resolution and
    processing them full-size on large images is the primary latency bottleneck.
    """
    from PIL import Image
    w, h = pil.size
    if max(w, h) <= _VIS_MAX_PX:
        return pil
    scale = _VIS_MAX_PX / max(w, h)
    return pil.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
VIDEO_MAX_MB = 100
VIDEO_NUM_FRAMES = 16

_IMAGE_EXCLUDE = {"explainability": {"heatmap_base64", "ela_base64", "boxes_base64"}}


def _resolve_language_hint(text: str, language_hint: str | None) -> str:
    hint = (language_hint or "auto").strip().lower()
    if hint and hint != "auto":
        return hint
    return detect_language(text)


def _compute_llm_summary(resp, *, record_id: int, user, media_kind: str, exclude: dict | None = None):
    """Build a deterministic instant summary from analysis scores.

    This always returns a meaningful summary — no LLM API call.
    The separate /analyze/{record_id}/llm endpoint upgrades this
    with a Gemini-generated summary when available.
    """
    verdict = resp.verdict
    score = verdict.authenticity_score
    label = verdict.label
    confidence = verdict.model_confidence

    # Media-specific evidence bullets
    bullets: list[str] = []
    if media_kind == "image":
        expl = getattr(resp, "explainability", None)
        if expl:
            n_artifacts = len(getattr(expl, "artifact_indicators", []) or [])
            exif = getattr(expl, "exif", None)
            if n_artifacts:
                bullets.append(f"{n_artifacts} artifact indicator(s) detected in the image")
            if exif and exif.trust_adjustment != 0:
                direction = "strengthens" if exif.trust_adjustment < 0 else "weakens"
                bullets.append(f"EXIF metadata {direction} authenticity ({exif.trust_reason or 'metadata analysis'})")
            no_face = getattr(expl, "no_face_analysis", None)
            if no_face:
                bullets.append("No human face detected — non-facial deepfake analysis applied")
    elif media_kind == "video":
        expl = getattr(resp, "explainability", None)
        if expl:
            bullets.append(f"{getattr(expl, 'num_frames_sampled', 0)} frames analyzed, {getattr(expl, 'num_suspicious_frames', 0)} flagged as suspicious")
            if getattr(expl, "temporal_score", None) is not None:
                bullets.append(f"Temporal consistency score: {expl.temporal_score:.2f}")
            audio = getattr(expl, "audio", None)
            if audio and audio.has_audio:
                bullets.append(f"Audio authenticity: {audio.audio_authenticity_score:.0f}/100")
    elif media_kind in ("text", "screenshot"):
        expl = getattr(resp, "explainability", None)
        if expl:
            sens = getattr(expl, "sensationalism", None)
            if sens and sens.score > 20:
                bullets.append(f"Sensationalism score: {sens.score}/100 ({sens.level})")
            n_manip = len(getattr(expl, "manipulation_indicators", []) or [])
            if n_manip:
                bullets.append(f"{n_manip} manipulation pattern(s) found in the text")
            sources = getattr(resp, "trusted_sources", []) or []
            if sources:
                bullets.append(f"Cross-referenced against {len(sources)} trusted source(s)")
    elif media_kind.startswith("audio"):
        expl = getattr(resp, "explainability", None)
        if expl:
            if getattr(expl, "has_audio", False):
                bullets.append(f"Audio duration: {getattr(expl, 'duration_s', 0):.1f}s")
            ml = getattr(expl, "ml_analysis", None)
            if ml:
                bullets.append(f"Voice ML prediction: {ml.label} (p_fake={ml.fake_probability:.2f})")

    # Always include the score
    bullets.insert(0, f"Overall authenticity score: {score}/100")
    bullets = bullets[:3]  # Cap at 3

    # Generate contextual paragraph
    if score >= 75:
        tone = "appears authentic"
        detail = "No significant manipulation indicators were detected."
    elif score >= 50:
        tone = "shows some inconsistencies"
        detail = "Minor signals were found but are not conclusive — review the evidence below."
    elif score >= 30:
        tone = "raises moderate concern"
        detail = "Multiple indicators suggest possible manipulation — check the detailed breakdown."
    else:
        tone = "is likely manipulated"
        detail = "Strong manipulation indicators were detected across multiple analysis stages."

    # Normalize media_kind for user-facing text
    display_kind = {
        "audio_deepfake_analysis": "audio",
    }.get(media_kind, media_kind)

    paragraph = (
        f"This {display_kind} {tone} with a deepfake probability of {100 - score}/100 "
        f"(model confidence: {confidence:.0%}). {detail}"
    )

    from schemas.common import LLMExplainabilitySummary
    return LLMExplainabilitySummary(
        paragraph=paragraph,
        bullets=bullets,
        model_used="auto-summary",
    )



def _find_existing_llm_summary(payload: dict) -> dict | None:
    """Find persisted LLM summaries regardless of media-specific storage shape."""
    top_level = payload.get("llm_summary")
    if isinstance(top_level, dict) and top_level.get("paragraph"):
        return top_level
    explainability = payload.get("explainability")
    if isinstance(explainability, dict):
        nested = explainability.get("llm_summary")
        if isinstance(nested, dict) and nested.get("paragraph"):
            return nested
    return None


def _store_llm_summary(payload: dict, summary: dict) -> None:
    """Persist generated summaries where the response schemas expect them."""
    media_type = str(payload.get("media_type") or "").lower()
    if media_type == "image":
        payload.setdefault("explainability", {})["llm_summary"] = summary
    else:
        payload["llm_summary"] = summary


@router.post("/{record_id}/llm")
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
def generate_llm_endpoint(
    request: Request,
    response: Response,
    record_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
):
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    if user is None or record.user_id != user.id:
        if record.user_id is not None:
            raise HTTPException(status_code=403, detail="Forbidden")

    payload = json.loads(record.result_json)

    # Return existing real LLM summary if present (skip auto-summaries)
    existing_summary = _find_existing_llm_summary(payload)
    if existing_summary and existing_summary.get("model_used", "") not in ("auto-summary", ""):
        return {"llm_summary": existing_summary}

    media_type = payload.get("media_type", "media")

    try:
        summary_obj = generate_llm_summary(payload=payload, record_id=str(record.id), media_kind=media_type)
        summary_dict = summary_obj.model_dump() if hasattr(summary_obj, "model_dump") else summary_obj

        _store_llm_summary(payload, summary_dict)
        record.result_json = json.dumps(payload)
        db.commit()

        return {"llm_summary": summary_dict}
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        # Return the auto-summary instead of failing with 500
        if existing_summary:
            return {"llm_summary": existing_summary}
        raise HTTPException(status_code=500, detail="LLM generation failed")

def _persist_response_payload(db: Session, record: AnalysisRecord, resp) -> None:
    """Keep reloaded/history responses aligned with the fresh API response."""
    record.result_json = json.dumps(resp.model_dump())
    db.add(record)
    db.commit()


@router.post("/image", response_model=ImageAnalysisResponse)
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_image(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    cache: bool = Query(default=True),
    language_hint: str = Query(default="auto"),
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
    cached = lookup_cached(db, media_hash=media_hash, media_type="image", user_id=user.id if user else None) if cache else None
    if cached is not None:
        payload = cached_payload(cached)
        if payload is not None:
            logger.info(f"cache hit image sha={media_hash[:12]} record={cached.id}")
            return ImageAnalysisResponse.model_validate(payload)

    pil = load_image_from_bytes(raw)
    pil_vis = _resize_for_vis(pil)  # smaller copy for visualization — avoids 20-30s PNG encoding at 4K+

    indicators = scan_artifacts(pil, raw)
    stages.append("artifact_scanning")

    model_family = "efficientnet" if settings.ENSEMBLE_MODE else "vit"

    # ── Run heatmap + ELA + boxes + EXIF in parallel ──
    def _run_heatmap():
        return generate_heatmap_base64(pil_vis, model_family=model_family)

    def _run_ela():
        return generate_ela_base64(pil_vis)

    def _run_boxes():
        return generate_boxes_base64(pil_vis)

    def _run_exif():
        return extract_exif(pil, raw)

    heatmap_result, ela_result, boxes_result, exif_result = await asyncio.gather(
        asyncio.to_thread(_run_heatmap),
        asyncio.to_thread(_run_ela),
        asyncio.to_thread(_run_boxes),
        asyncio.to_thread(_run_exif),
        return_exceptions=True,
    )

    # ── Phase 12: Grad-CAM++ heatmap ──
    heatmap_status = "success"
    heatmap = ""
    if isinstance(heatmap_result, Exception):
        logger.warning(f"Heatmap generation failed, continuing: {heatmap_result}")
        heatmap_status = "failed"
    else:
        heatmap, heatmap_source = heatmap_result
        if not heatmap:
            heatmap_status = heatmap_source
        else:
            stages.append("heatmap_generation")

    # ── Phase 12: ELA (Error Level Analysis) ──
    ela_b64 = ""
    if isinstance(ela_result, Exception):
        logger.warning(f"ELA generation failed, continuing: {ela_result}")
    else:
        ela_b64 = ela_result
        stages.append("ela_generation")

    # ── Phase 12: Bounding box mode ──
    boxes_b64 = ""
    if isinstance(boxes_result, Exception):
        logger.warning(f"Bounding box generation failed, continuing: {boxes_result}")
    else:
        boxes_b64 = boxes_result
        stages.append("boxes_generation")

    # ── Phase 12: EXIF extraction + trust adjustment ──
    exif_summary = None
    if isinstance(exif_result, Exception):
        logger.warning(f"EXIF extraction failed, continuing: {exif_result}")
    else:
        exif_summary = exif_result
        stages.append("exif_extraction")

    clf = classify_image(pil, artifact_indicators=indicators, exif=exif_summary)
    stages.append("classification")

    analysis_id = str(uuid.uuid4())
    vlm_bd = None
    if user is not None and clf.no_face_analysis is not None:
        try:
            vlm_bd = generate_vlm_breakdown(pil, record_id=analysis_id)
            if vlm_bd:
                clf = classify_image(
                    pil,
                    artifact_indicators=indicators,
                    exif=exif_summary,
                    vlm_breakdown=vlm_bd,
                )
                stages.append("vlm_no_face_fusion")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"VLM no-face fusion failed, continuing: {e}")

    score = compute_authenticity_score(clf.confidence, clf.label)

    # Apply EXIF trust adjustment.
    # trust_adjustment convention: negative = more real → subtract to RAISE authenticity score.
    # positive = more fake → subtract to LOWER authenticity score.
    if clf.no_face_analysis is None and exif_summary and exif_summary.trust_adjustment != 0:
        score = int(round(max(0, min(100, score - exif_summary.trust_adjustment))))

    label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    resp = ImageAnalysisResponse(
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
            no_face_analysis=clf.no_face_analysis,
            vlm_breakdown=vlm_bd,
        ),
        trusted_sources=[],
        contradicting_evidence=[],
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=duration_ms,
            model_used=settings.IMAGE_MODEL_ID,
            models_used=clf.models_used,
            calibrator_applied=clf.calibrator_applied,
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
    resp.thumbnail_url = thumbnail_url
    if media_path:
        resp.media_path = media_path

    # Persist overlay images so they survive page reloads (base64 excluded from DB)
    if heatmap:
        url = save_overlay(heatmap, media_hash, "heatmap")
        if url:
            resp.explainability.heatmap_url = url
    if ela_b64:
        url = save_overlay(ela_b64, media_hash, "ela")
        if url:
            resp.explainability.ela_url = url
    if boxes_b64:
        url = save_overlay(boxes_b64, media_hash, "boxes")
        if url:
            resp.explainability.boxes_url = url

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="image",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(resp.model_dump()),
        media_hash=media_hash,
        media_path=media_path,
        thumbnail_url=thumbnail_url,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    resp.record_id = record.id
    logger.info(f"Saved AnalysisRecord id={record.id} score={score} verdict={label}")

    # ── Phase 12: deterministic instant summary (no API call) ──
    llm_summary = _compute_llm_summary(resp, record_id=record.id, user=user, media_kind="image", exclude=_IMAGE_EXCLUDE)
    if llm_summary:
        resp.explainability.llm_summary = llm_summary
        stages.append("llm_explanation")

    resp.processing_summary.stages_completed = stages
    _persist_response_payload(db, record, resp)

    # ── Phase 14: VLM breakdown runs after response is returned ──
    if user is not None and vlm_bd is None:
        _record_id = record.id
        _pil = pil

        def _bg_vlm():
            try:
                from db.database import SessionLocal
                breakdown = generate_vlm_breakdown(_pil, record_id=str(_record_id))
                if not breakdown:
                    return
                bg_db = SessionLocal()
                try:
                    bg_rec = bg_db.query(AnalysisRecord).filter(AnalysisRecord.id == _record_id).first()
                    if bg_rec:
                        payload = json.loads(bg_rec.result_json)
                        payload.setdefault("explainability", {})["vlm_breakdown"] = breakdown.model_dump()
                        bg_rec.result_json = json.dumps(payload)
                        bg_db.commit()
                        logger.info(f"VLM breakdown persisted for record={_record_id}")
                finally:
                    bg_db.close()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Background VLM breakdown failed: {e}")

        background_tasks.add_task(_bg_vlm)

    return resp


@router.post("/video", response_model=VideoAnalysisResponse)
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_video_endpoint(
    request: Request,
    response: Response,
    cache: bool = Query(default=True),
    language_hint: str = Query(default="auto"),
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
    cached = lookup_cached(db, media_hash=media_hash, media_type="video", user_id=user.id if user else None) if cache else None
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
    score, label, severity = compute_video_authenticity_score(
        mean_suspicious_prob=agg.mean_suspicious_prob,
        insufficient_faces=agg.insufficient_faces,
        temporal_score=agg.temporal.temporal_score if agg.temporal else None,
        audio_authenticity_score=audio_result.audio_authenticity_score if audio_result else None,
        has_audio=bool(audio_result and audio_result.has_audio),
    )

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
            ml_analysis=AudioMLScore(
                fake_probability=audio_result.ml_analysis["fake_probability"],
                label=audio_result.ml_analysis["label"],
                model_used=audio_result.ml_analysis.get("model_used", "Unknown"),
                error=audio_result.ml_analysis.get("error", False)
            ) if audio_result.ml_analysis else None
        )

    resp = VideoAnalysisResponse(
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
            calibrator_applied=agg.calibrator_applied,
        ),
    )

    # Phase 19.2 — persist video + thumbnail frame
    try:
        media_path = save_file(path, media_hash, suffix.lstrip("."))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"video media save failed: {e}")
        media_path = None
    thumbnail_url = make_video_thumbnail(path, media_hash)
    resp.thumbnail_url = thumbnail_url

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="video",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(resp.model_dump()),
        media_hash=media_hash,
        media_path=media_path,
        thumbnail_url=thumbnail_url,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    resp.record_id = record.id
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

    # Phase 12: LLM explainability card (authed users only — conserves LLM quota)
    llm = _compute_llm_summary(resp, record_id=record.id, user=user, media_kind="video")
    if llm:
        resp.llm_summary = llm

    resp.processing_summary.stages_completed = stages
    _persist_response_payload(db, record, resp)
    return resp


class TextAnalyzeBody(BaseModel):
    text: str
    cache: bool = True
    language_hint: str = "auto"


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
    lang = _resolve_language_hint(body.text, body.language_hint)
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

    # Weighted score: keep classifier authoritative. Linguistic heuristics can
    # lower confidence, but should not give a high floor when classifier is very fake.
    manip_penalty = min(len(manip) * 5, 30)
    raw_score = (1.0 - effective_fake_prob) * 100.0
    
    if lang == "en":
        heuristic_score = max(0, 100 - sens.score) * 0.60 + max(0, 100 - manip_penalty) * 0.40
        weighted = raw_score * 0.90 + heuristic_score * 0.10
    else:
        weighted = raw_score

    score = int(round(max(0.0, min(100.0, weighted))))
    label, severity = get_verdict_label(score)
    duration_ms = int((time.perf_counter() - start) * 1000)

    model_used = (
        settings.TEXT_MULTILANG_MODEL_ID if (lang != "en" and settings.TEXT_MULTILANG_MODEL_ID)
        else settings.TEXT_MODEL_ID
    )

    resp = TextAnalysisResponse(
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
            original_text=body.text,
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
            calibrator_applied=False,
        ),
    )

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="text",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(resp.model_dump()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    resp.record_id = record.id
    logger.info(f"Saved AnalysisRecord id={record.id} text score={score} verdict={label}")

    # Phase 12: LLM explainability card (authed users only — conserves LLM quota)
    llm = _compute_llm_summary(resp, record_id=record.id, user=user, media_kind="text")
    if llm:
        resp.llm_summary = llm

    resp.processing_summary.stages_completed = stages
    _persist_response_payload(db, record, resp)
    return resp


@router.post("/screenshot", response_model=ScreenshotAnalysisResponse)
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_screenshot_endpoint(
    request: Request,
    response: Response,
    cache: bool = Query(default=True),
    language_hint: str = Query(default="auto"),
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
    cached = lookup_cached(db, media_hash=media_hash, media_type="screenshot", user_id=user.id if user else None) if cache else None
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
    lang = _resolve_language_hint(full_text, language_hint) if full_text else "en"
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
    
    if lang == "en":
        heuristic_score = (
            max(0, 100 - sens.score) * 0.45
            + max(0, 100 - manip_penalty) * 0.35
            + max(0, 100 - layout_penalty) * 0.20
        )
        weighted = raw_score * 0.90 + heuristic_score * 0.10
    else:
        layout_heuristic = max(0, 100 - layout_penalty)
        weighted = raw_score * 0.90 + layout_heuristic * 0.10

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

    resp = ScreenshotAnalysisResponse(
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
            calibrator_applied=False,
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
    resp.thumbnail_url = thumbnail_url

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="screenshot",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(resp.model_dump()),
        media_hash=media_hash,
        media_path=media_path,
        thumbnail_url=thumbnail_url,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    resp.record_id = record.id
    logger.info(f"Saved AnalysisRecord id={record.id} screenshot score={score} verdict={label}")

    # Phase 12: LLM explainability card (authed users only — conserves LLM quota)
    llm = _compute_llm_summary(resp, record_id=record.id, user=user, media_kind="screenshot")
    if llm:
        resp.llm_summary = llm

    resp.processing_summary.stages_completed = stages
    _persist_response_payload(db, record, resp)
    return resp


# ───────────────────────── Phase 19.3 — async video + jobs ─────────────────────────

@router.post("/video/async", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_video_async(
    request: Request,
    response: Response,
    background: BackgroundTasks,
    cache: bool = Query(default=True),
    language_hint: str = Query(default="auto"),
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
    cached = lookup_cached(db, media_hash=media_hash, media_type="video", user_id=user.id if user else None) if cache else None
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

            score_val, label_val, sev = compute_video_authenticity_score(
                mean_suspicious_prob=agg.mean_suspicious_prob,
                insufficient_faces=agg.insufficient_faces,
                temporal_score=agg.temporal.temporal_score if agg.temporal else None,
                audio_authenticity_score=audio_result.audio_authenticity_score if audio_result else None,
                has_audio=bool(audio_result and audio_result.has_audio),
            )

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
                    ml_analysis=AudioMLScore(
                        fake_probability=audio_result.ml_analysis["fake_probability"],
                        label=audio_result.ml_analysis["label"],
                        model_used=audio_result.ml_analysis.get("model_used", "Unknown"),
                        error=audio_result.ml_analysis.get("error", False)
                    ) if audio_result.ml_analysis else None
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
                    calibrator_applied=agg.calibrator_applied,
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


@router.post("/audio", response_model=AudioAnalysisResponse)
@limiter.limit(ANON_ANALYZE, exempt_when=is_authed)
@limiter.limit(AUTH_ANALYZE, exempt_when=is_anon)
async def analyze_audio_endpoint(
    request: Request,
    response: Response,
    cache: bool = Query(default=True),
    language_hint: str = Query(default="en"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
) -> AudioAnalysisResponse:
    start = time.perf_counter()
    stages: list[str] = []

    raw, mime = await read_upload_bytes(
        file, ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/aac", "audio/ogg", "audio/webm", "video/webm", "video/mp4"], max_size_mb=25.0
    )
    stages.append("validation")

    media_hash = sha256_bytes(raw)
    cached = lookup_cached(db, media_hash=media_hash, media_type="audio", user_id=user.id if user else None) if cache else None
    if cached is not None:
        payload = cached_payload(cached)
        if payload is not None:
            return AudioAnalysisResponse.model_validate(payload)

    stages.append("feature_extraction")
    
    import tempfile
    from services.audio_service import _extract_audio_wav, _analyse_wav
    from services.audio_ml_service import analyze_audio_ml
    
    tmp_path = None
    tmp_wav = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav" if "wav" in mime else ".mp3", delete=False) as fh:
            fh.write(raw)
            tmp_path = fh.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wfh:
            tmp_wav = wfh.name
            
        _extract_audio_wav(tmp_path, tmp_wav)
        
        stages.append("voice_ml_model")
        ml_score = analyze_audio_ml(tmp_wav)
        
        stages.append("signal_heuristics")
        heuristics = _analyse_wav(tmp_wav)
        
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if tmp_wav and os.path.exists(tmp_wav):
            os.remove(tmp_wav)

    audio_expl = AudioStandaloneExplainability(
        audio_authenticity_score=heuristics.audio_authenticity_score,
        has_audio=heuristics.has_audio,
        duration_s=heuristics.duration_s,
        silence_ratio=heuristics.silence_ratio,
        spectral_variance=heuristics.spectral_variance,
        rms_consistency=heuristics.rms_consistency,
        notes=heuristics.notes,
        ml_analysis=AudioMLScore(
            fake_probability=ml_score["fake_probability"],
            label=ml_score["label"],
            model_used=ml_score.get("model_used", "Unknown"),
            error=ml_score.get("error", False)
        )
    )

    heuristics_prob = 1.0 - (heuristics.audio_authenticity_score / 100.0)
    ml_prob = ml_score["fake_probability"]
    final_prob = 0.5 * heuristics_prob + 0.5 * ml_prob

    score = int(round(max(0.0, min(100.0, (1.0 - final_prob) * 100.0))))
    label, severity = get_verdict_label(score)

    resp = AudioAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        verdict=Verdict(
            label=label,
            severity=severity,
            authenticity_score=score,
            model_confidence=final_prob,
            model_label="Deepfake-audio-detection-V2"
        ),
        explainability=audio_expl,
        processing_summary=ProcessingSummary(
            stages_completed=stages,
            total_duration_ms=int((time.perf_counter() - start) * 1000),
            model_used="MelodyMachine/Deepfake-audio-detection-V2",
            models_used=["MelodyMachine/Deepfake-audio-detection-V2", "audio-signal-heuristics"],
            calibrator_applied=False,
        )
    )

    ext = (mime.split("/")[-1] if mime else "mp3").replace("mpeg", "mp3").replace("x-wav", "wav")
    try:
        media_path = save_bytes(raw, media_hash, ext)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"audio media save failed: {e}")
        media_path = None

    record = AnalysisRecord(
        user_id=user.id if user else None,
        media_type="audio",
        verdict=label,
        authenticity_score=float(score),
        result_json=json.dumps(resp.model_dump()),
        media_hash=media_hash,
        media_path=media_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    resp.record_id = record.id

    llm = _compute_llm_summary(resp, record_id=record.id, user=user, media_kind="audio_deepfake_analysis")
    if llm:
        resp.llm_summary = llm
        stages.append("llm_summary")

    resp.processing_summary.stages_completed = stages
    _persist_response_payload(db, record, resp)
    return resp


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
