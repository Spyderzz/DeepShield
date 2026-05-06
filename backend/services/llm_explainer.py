"""LLM Explainability Card — Phase 12.3

Generates a plain-English summary paragraph + 3 key-signal bullets from the
full analysis payload.  Supports Gemini (default) and OpenAI providers.
Results are cached per record_id to avoid re-spending tokens.
"""

from __future__ import annotations

import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import time
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from config import settings
from schemas.common import LLMExplainabilitySummary, SignalObservation

# ── In-memory caches ──
# Keyed by record_id — one row per analysis
_cache: dict[str, LLMExplainabilitySummary] = {}
# Keyed by SHA-256 of the prompt — dedups across different analyses of the same content
_hash_cache: dict[str, LLMExplainabilitySummary] = {}

# ── Circuit breaker: shared by llm_explainer + vlm_breakdown via the helpers below ──
_COOLDOWN_SECONDS = 300  # 5 min after a 429/quota error
_cooldown_until: float = 0.0


def is_rate_limited() -> bool:
    """Return True if we're in a post-429 cooldown window. Skip all LLM calls."""
    return time.time() < _cooldown_until


def mark_rate_limited(seconds: int = _COOLDOWN_SECONDS) -> None:
    """Open the circuit for `seconds`. Safe to call from any LLM caller."""
    global _cooldown_until
    _cooldown_until = time.time() + seconds
    logger.warning(f"LLM rate-limited — pausing all LLM calls for {seconds}s")


def _is_quota_error(exc: Exception) -> bool:
    """Heuristic: detect 429 / quota / ResourceExhausted across Gemini + OpenAI SDKs."""
    msg = f"{type(exc).__name__} {exc!s}".lower()
    return any(m in msg for m in ("429", "resourceexhausted", "quota", "rate limit", "toomanyrequests"))


_PROMPT_TEMPLATE = """\
DeepShield forensics explainer. Media={media_kind}. Plain English, public audience.

OUTPUT — strict JSON, no fences:
{{"paragraph":"<4-5 sentences: verdict + strongest evidence + practical advice, 80-120 words>","signals":[{{"name":"<name>","observation":"<specific, cite numbers>","verdict":"suspicious|authentic|inconclusive"}}],"bullets":["<finding+number>","<finding+number>","<finding+number>","<user action>"]}}

SIGNALS (images only — [] for video/audio/text/screenshot). Use ONLY payload data, never invent:
1 Face-Neck Boundary — texture/colour break where face meets neck? Use ARTIFACTS facial_boundary conf.
2 Lighting Consistency — light direction match face vs background? Use ARTIFACTS lighting conf.
3 Skin Texture — natural pores/imperfections vs unnaturally smooth? Use VLM skin score + FUSION forensics.
4 Face Geometry — proportions/jaw blending natural? Use VLM sym+anat scores.
5 Background/Compression — compression blocks, ghosting, sharpness mismatch? Use ARTIFACTS compression. If FLAGS has video_frame, note it.
6 AI Generation Markers — synthetic image detector result. Use FUSION general prob. If low and video_frame=true, note detector unreliable for video.
verdict: suspicious=manipulation signal, authentic=genuine signal, inconclusive=insufficient data.

RULES: no jargon (say "face-swap model" not "EfficientNet", "AI-image detector" not "GAN"). Numbers from payload only. Bullets 15-25 words each.

DATA:
{payload_json}
"""

_EXPLAINABILITY_LIMITS = {
    "artifact_indicators": 6,
    "manipulation_indicators": 6,
    "suspicious_phrases": 6,
    "layout_anomalies": 5,
    "trusted_sources": 5,
    "contradicting_evidence": 5,
    "ocr_boxes": 8,
    "frames": 6,
    "suspicious_timestamps": 8,
}

_KEEP_TOP_LEVEL = {
    "analysis_id",
    "record_id",
    "media_type",
    "timestamp",
    "verdict",
    "trusted_sources",
    "contradicting_evidence",
    "processing_summary",
}

_KEEP_EXPLAINABILITY = {
    "original_text",
    "extracted_text",
    "transcript",
    "fake_probability",
    "top_label",
    "all_scores",
    "keywords",
    "sensationalism",
    "manipulation_indicators",
    "suspicious_phrases",
    "layout_anomalies",
    "artifact_indicators",
    "exif",
    "no_face_analysis",
    "vlm_breakdown",
    "truth_override",
    "num_frames_sampled",
    "num_face_frames",
    "num_suspicious_frames",
    "mean_suspicious_prob",
    "max_suspicious_prob",
    "suspicious_ratio",
    "insufficient_faces",
    "suspicious_timestamps",
    "frames",
    "temporal_score",
    "optical_flow_variance",
    "flicker_score",
    "blink_rate_anomaly",
    "audio",
    "audio_authenticity_score",
    "has_audio",
    "duration_s",
    "silence_ratio",
    "spectral_variance",
    "rms_consistency",
    "notes",
    "ml_analysis",
    "ocr_boxes",
}

_DROP_SUFFIXES = ("_base64",)
_DROP_KEYS = {
    "heatmap_base64", "ela_base64", "boxes_base64",
    "heatmap_url", "ela_url", "boxes_url",
    "thumbnail_url", "media_path", "media_url",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def _g(obj: Any, key: str, default: Any = None) -> Any:
    """Get from dict or object attribute."""
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def _truncate_text(value: Any, limit: int = 600) -> Any:
    if not isinstance(value, str):
        return value
    text = " ".join(value.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _compact_value(key: str, value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _compact_value(k, v) for k, v in value.items()
                if k not in _DROP_KEYS and not str(k).endswith(_DROP_SUFFIXES)}
    if isinstance(value, list):
        limit = _EXPLAINABILITY_LIMITS.get(key, 10)
        return [_compact_value(key, item) for item in value[:limit]]
    return _truncate_text(value)


# ── image compact payload ─────────────────────────────────────────────────────

def _build_image_compact(payload: dict[str, Any]) -> str:
    """Dense line-based payload for image analysis — ~70% fewer tokens than JSON.

    Format the LLM can read with zero ambiguity:
      KEY:value1 value2 ...   (one concept per line, no nesting)
    """
    lines: list[str] = []

    # Verdict
    v = payload.get("verdict", {})
    label = _g(v, "label", "?")
    score = _g(v, "authenticity_score", "?")
    conf  = _g(v, "model_confidence", 0.0)
    lines.append(f"VERDICT:{label}|score={score}|conf={conf:.2f}")

    # Evidence fusion components (Phase A — new signals)
    ps  = payload.get("processing_summary", {})
    ef  = _g(ps, "evidence_fusion", {}) or {}
    comps = _g(ef, "components", {}) or {}
    if comps:
        parts = " ".join(
            f"{k}={float(val):.2f}" for k, val in comps.items()
            if isinstance(val, (int, float))
        )
        lines.append(f"FUSION:{parts}")

    # Flags: video_frame, gating, disagreement, pre-gating drift
    gating    = _g(ps, "gating_applied")
    disagree  = _g(ps, "disagreement_reason")
    is_vid    = _g(ef, "is_video_frame", False)
    pre_gate  = _g(ef, "pre_gating")
    flag_parts: list[str] = []
    if is_vid:       flag_parts.append("video_frame=yes")
    if gating:       flag_parts.append(f"gated={gating}")
    if disagree:     flag_parts.append(f"disagree={disagree[:60]}")
    if pre_gate is not None and comps:
        final = _g(v, "model_confidence", 0.5)
        if abs(float(pre_gate) - float(final)) > 0.05:
            flag_parts.append(f"pre_gate={float(pre_gate):.2f}")
    if flag_parts:
        lines.append(f"FLAGS:{' '.join(flag_parts)}")

    expl = payload.get("explainability", {}) or {}

    # Artifact indicators — type(severity_initial, confidence%)
    arts = _g(expl, "artifact_indicators", []) or []
    if arts:
        art_strs = []
        for a in arts[:6]:
            t = _g(a, "type", "?")
            s = (_g(a, "severity", "?") or "?")[0].upper()
            c = _g(a, "confidence", 0.0)
            art_strs.append(f"{t}({s},{c:.0%})")
        lines.append(f"ARTIFACTS:{' '.join(art_strs)}")
    else:
        lines.append("ARTIFACTS:none")

    # EXIF — abbreviated
    exif = _g(expl, "exif")
    if exif:
        adj    = _g(exif, "trust_adjustment", 0)
        make   = _g(exif, "make")
        model  = _g(exif, "model")
        sw     = _g(exif, "software")
        reason = _g(exif, "trust_reason", "")
        exif_parts = [f"adj={adj}"]
        if make:   exif_parts.append(f"cam={make} {model or ''}".strip())
        if sw:     exif_parts.append(f"sw={sw[:30]}")
        if reason: exif_parts.append(f"note={reason[:60]}")
        lines.append(f"EXIF:{' '.join(exif_parts)}")
    else:
        lines.append("EXIF:none")

    # VLM breakdown — 6 scores in one line
    vlm = _g(expl, "vlm_breakdown")
    if vlm:
        def _s(k: str) -> int:
            d = _g(vlm, k, {}) or {}
            return int(_g(d, "score", 75))
        lines.append(
            f"VLM:sym={_s('facial_symmetry')} skin={_s('skin_texture')} "
            f"light={_s('lighting_consistency')} bg={_s('background_coherence')} "
            f"anat={_s('anatomy_hands_eyes')} ctx={_s('context_objects')}"
        )

    # Face presence (no_face_analysis is set only when NO face found)
    face_present = _g(expl, "no_face_analysis") is None
    lines.append(f"FACE:{'yes' if face_present else 'no'}")

    # Models + method
    models  = _g(ps, "models_used", []) or []
    method  = _g(ef, "method", "")
    face_m  = _g(ef, "face_stack_method", "")
    if models:
        short = [str(m).split("/")[-1][:25] for m in models[:4]]
        lines.append(f"MODELS:{','.join(short)}")
    if method:
        lines.append(f"METHOD:{face_m or method}")

    return "\n".join(lines)


# ── non-image compact payload (lightweight JSON) ──────────────────────────────

_KEEP_NON_IMAGE = {
    "media_type", "verdict", "trusted_sources", "contradicting_evidence",
}
_KEEP_NON_IMAGE_EXPL = {
    "original_text", "extracted_text", "transcript", "fake_probability",
    "top_label", "keywords", "sensationalism", "manipulation_indicators",
    "suspicious_phrases", "layout_anomalies",
    "num_frames_sampled", "num_face_frames", "num_suspicious_frames",
    "mean_suspicious_prob", "suspicious_ratio", "insufficient_faces",
    "temporal_score", "audio_authenticity_score", "has_audio",
    "silence_ratio", "spectral_variance", "rms_consistency", "ml_analysis",
    "ocr_boxes",
}


def _build_non_image_compact(payload: dict[str, Any]) -> str:
    out: dict[str, Any] = {k: _compact_value(k, payload[k])
                           for k in _KEEP_NON_IMAGE if k in payload}
    expl = payload.get("explainability", {})
    if isinstance(expl, dict):
        out["e"] = {k: _compact_value(k, v) for k, v in expl.items()
                    if k in _KEEP_NON_IMAGE_EXPL and k not in _DROP_KEYS}
    return json.dumps(out, separators=(",", ":"), default=str)


def _build_llm_payload(payload: dict[str, Any]) -> str:
    """Return the token-efficient payload string for the LLM prompt."""
    media_type = payload.get("media_type", "")
    if media_type == "image":
        return _build_image_compact(payload)
    return _build_non_image_compact(payload)


class _LLMProvider(ABC):
    name: str = "base"
    model: str = ""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send prompt to LLM and return raw text response."""

    @property
    def tag(self) -> str:
        return f"{self.name}/{self.model}"


class _GeminiProvider(_LLMProvider):
    """Gemini via the new `google-genai` SDK (replaces deprecated `google-generativeai`)."""
    name = "gemini"

    def __init__(self) -> None:
        from google import genai
        from google.genai import types

        self._client = genai.Client(api_key=settings.LLM_API_KEY)
        self.model = settings.LLM_MODEL
        self._config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=600,
            response_mime_type="application/json",
        )

    def generate(self, prompt: str) -> str:
        resp = self._client.models.generate_content(model=self.model, contents=prompt, config=self._config)
        return resp.text or ""


class _OpenAIProvider(_LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.LLM_API_KEY)
        self.model = settings.LLM_MODEL

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


class _GroqProvider(_LLMProvider):
    """Groq — free-tier Llama 3.3 70B. Used as failover when the primary hits 429."""
    name = "groq"

    def __init__(self) -> None:
        from groq import Groq
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


class _ProviderChain:
    """Primary provider with optional Groq fallback. Each provider gets its own
    timeout so the fallback gets a full shot even if the primary is slow.
    The `last_used` attribute tracks which provider produced the response.
    """

    _PRIMARY_TIMEOUT = 7    # gemini-2.0-flash responds in ~2-4s
    _FALLBACK_TIMEOUT = 8   # seconds for Groq

    def __init__(self, primary: _LLMProvider, fallback: _LLMProvider | None) -> None:
        self._primary = primary
        self._fallback = fallback
        self.last_used: _LLMProvider = primary

    def _call_with_timeout(self, provider: _LLMProvider, prompt: str, timeout: int) -> str:
        """Run a single provider with a timeout. Raises on failure or timeout."""
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(provider.generate, prompt)
            return future.result(timeout=timeout)

    def generate(self, prompt: str) -> str:
        # Try primary provider with its own timeout
        try:
            text = self._call_with_timeout(self._primary, prompt, self._PRIMARY_TIMEOUT)
            self.last_used = self._primary
            return text
        except FuturesTimeoutError:
            logger.warning(f"{self._primary.tag} timed out after {self._PRIMARY_TIMEOUT}s")
            primary_error = f"{self._primary.tag} timed out"
        except Exception as e:
            logger.warning(f"{self._primary.tag} failed: {type(e).__name__}: {e}")
            primary_error = f"{self._primary.tag} {type(e).__name__}"

        # Try fallback provider (Groq) with its own timeout
        if self._fallback is None:
            raise RuntimeError(primary_error)

        logger.info(f"Failing over to {self._fallback.tag}")
        try:
            text = self._call_with_timeout(self._fallback, prompt, self._FALLBACK_TIMEOUT)
            self.last_used = self._fallback
            logger.info(f"Fallback {self._fallback.tag} succeeded")
            return text
        except FuturesTimeoutError:
            logger.warning(f"{self._fallback.tag} also timed out after {self._FALLBACK_TIMEOUT}s")
            raise RuntimeError(f"Both {self._primary.tag} and {self._fallback.tag} timed out")
        except Exception as e2:
            logger.error(f"{self._fallback.tag} also failed: {type(e2).__name__}: {e2}")
            raise


_provider_lock = threading.Lock()
_provider_instance: _ProviderChain | None = None
_provider_model_tag: str = ""  # tracks the model that _provider_instance was built for


def _get_provider() -> _ProviderChain:
    """Lazy-init the configured provider chain (thread-safe singleton).
    Re-initializes when the configured model changes (e.g. hot-reload during dev).
    """
    global _provider_instance, _provider_model_tag
    current_tag = f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}"
    if _provider_instance is not None and _provider_model_tag == current_tag:
        return _provider_instance
    with _provider_lock:
        if _provider_instance is None or _provider_model_tag != current_tag:
            provider_name = settings.LLM_PROVIDER.lower()
            primary: _LLMProvider = _OpenAIProvider() if provider_name == "openai" else _GeminiProvider()
            fallback: _LLMProvider | None = None
            if settings.GROQ_API_KEY and primary.name != "groq":
                try:
                    fallback = _GroqProvider()
                    logger.info(f"LLM chain initialized: {primary.tag} → {fallback.tag}")
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Groq fallback unavailable: {e}")
            _provider_instance = _ProviderChain(primary, fallback)
            _provider_model_tag = current_tag
    return _provider_instance


def _parse_llm_response(raw: str) -> tuple[str, list[SignalObservation], list[str]]:
    """Parse the LLM's JSON response into (paragraph, signals, bullets).
    Handles cases where the LLM wraps output in markdown fences.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    parsed = json.loads(text)
    paragraph = parsed.get("paragraph", "")

    raw_signals = parsed.get("signals", [])
    signals: list[SignalObservation] = []
    if isinstance(raw_signals, list):
        for s in raw_signals[:8]:
            if isinstance(s, dict) and s.get("name") and s.get("observation"):
                verdict = s.get("verdict", "inconclusive").lower()
                if verdict not in ("authentic", "suspicious", "inconclusive"):
                    verdict = "inconclusive"
                signals.append(SignalObservation(
                    name=str(s["name"]),
                    observation=str(s["observation"]),
                    verdict=verdict,
                ))

    bullets = parsed.get("bullets", [])
    if not isinstance(bullets, list):
        bullets = [str(bullets)]
    return paragraph, signals, bullets[:5]


def generate_llm_summary(
    payload: dict[str, Any],
    record_id: str | None = None,
    media_kind: str = "media",
) -> LLMExplainabilitySummary:
    """Generate an LLM-powered plain-English explanation for an analysis result.

    Args:
        payload: The full analysis response dict (verdict, scores, indicators, etc.).
        record_id: Optional cache key. If provided and cached, returns cached result.

    Returns:
        LLMExplainabilitySummary with paragraph, bullets, and model info.
    """
    # Check record-id cache
    if record_id and record_id in _cache:
        logger.debug(f"LLM summary cache hit for record_id={record_id}")
        cached = _cache[record_id]
        cached.cached = True
        return cached

    # Circuit breaker — skip the API entirely during cooldown
    if is_rate_limited():
        logger.debug("LLM in cooldown — returning fallback summary")
        return _fallback_summary(payload, reason="rate_limited")

    # Guard: no API key configured
    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not set — using deterministic fallback summary")
        return _fallback_summary(payload, reason="no_api_key")

    # _build_llm_payload already returns a compact string (line-based for images,
    # stripped JSON for other media). No further json.dumps needed.
    prompt_body = _build_llm_payload(payload)
    prompt = _PROMPT_TEMPLATE.format(media_kind=media_kind, payload_json=prompt_body)

    content_hash = hashlib.sha256(
        f"{settings.LLM_PROVIDER}|{settings.LLM_MODEL}|{prompt_body}".encode("utf-8")
    ).hexdigest()
    if content_hash in _hash_cache:
        logger.debug(f"LLM summary content-hash cache hit sha={content_hash[:12]}")
        summary = _hash_cache[content_hash].model_copy(update={"cached": True})
        if record_id:
            _cache[record_id] = summary
        return summary

    try:
        chain = _get_provider()
        raw_response = chain.generate(prompt)
        paragraph, signals, bullets = _parse_llm_response(raw_response)

        summary = LLMExplainabilitySummary(
            paragraph=paragraph,
            signals=signals,
            bullets=bullets,
            model_used=chain.last_used.tag,
        )

        # Cache by both record_id and content hash
        _hash_cache[content_hash] = summary
        if record_id:
            _cache[record_id] = summary

        logger.info(f"LLM summary generated via {chain.last_used.tag}")
        return summary

    except json.JSONDecodeError as e:
        logger.error(f"LLM returned unparseable JSON: {e}")
        chain = _get_provider()
        return LLMExplainabilitySummary(
            paragraph="Analysis complete. See the detailed indicators below for specifics.",
            signals=[],
            bullets=["LLM explanation could not be parsed"],
            model_used=chain.last_used.tag,
        )
    except Exception as e:
        err_msg = str(e).lower()
        if "timed out" in err_msg:
            logger.warning(f"LLM providers timed out: {e}")
            return _fallback_summary(payload, reason="timeout")
        if _is_quota_error(e):
            mark_rate_limited()
            logger.warning(f"LLM quota hit ({type(e).__name__}) — circuit open for {_COOLDOWN_SECONDS}s")
            return _fallback_summary(payload, reason="rate_limited")
        logger.error(f"LLM explainer failed: {e}")
        return _fallback_summary(payload, reason="error")


_SIGNAL_ARTIFACT_MAP = {
    "facial_boundary": ("Face-Neck Boundary", "suspicious"),
    "lighting":        ("Lighting Consistency", "suspicious"),
    "skin_texture":    ("Skin Texture", "suspicious"),
    "face_geometry":   ("Face Geometry", "suspicious"),
    "compression":     ("Background / Compression", "suspicious"),
    "gan_artifact":    ("AI Generation Markers", "suspicious"),
}


def _fallback_signals(payload: dict[str, Any]) -> list[SignalObservation]:
    """Build a signal list from artifact_indicators when the LLM is unavailable."""
    if payload.get("media_type") not in ("image", None):
        return []
    artifacts = (
        payload.get("explainability", {}).get("artifact_indicators", [])
        if isinstance(payload.get("explainability"), dict) else []
    )
    seen: set[str] = set()
    signals: list[SignalObservation] = []
    for art in artifacts:
        art_type = art.get("type", "") if isinstance(art, dict) else getattr(art, "type", "")
        art_desc = art.get("description", "") if isinstance(art, dict) else getattr(art, "description", "")
        art_conf = art.get("confidence", 0.0) if isinstance(art, dict) else getattr(art, "confidence", 0.0)
        if art_type in _SIGNAL_ARTIFACT_MAP and art_type not in seen:
            name, verdict = _SIGNAL_ARTIFACT_MAP[art_type]
            signals.append(SignalObservation(
                name=name,
                observation=f"{art_desc} (confidence {art_conf:.0%})",
                verdict=verdict,
            ))
            seen.add(art_type)
    return signals


def _fallback_summary(payload: dict[str, Any], *, reason: str) -> LLMExplainabilitySummary:
    """Deterministic summary used when the LLM is unavailable (no key / rate-limited)."""
    verdict_data = payload.get("verdict", {})
    label = verdict_data.get("label", "Unknown")
    score = verdict_data.get("authenticity_score", 50)
    tail = {
        "rate_limited": "LLM paused — automatic summary shown during quota cooldown.",
        "no_api_key": "Note: Configure an LLM API key for deeper contextual analysis.",
        "timeout": "Both Gemini and Groq timed out — showing automatic summary instead.",
        "error": "LLM providers encountered an error — showing automatic summary.",
    }.get(reason, "LLM explanation unavailable.")
    is_likely_real = score >= 65
    confidence_word = "high" if abs(score - 50) > 30 else "moderate"
    action = (
        "This content appears safe to read and share, though independent verification is always recommended."
        if is_likely_real
        else "Exercise caution before sharing this content — it shows signs that may indicate manipulation or fabrication."
    )
    return LLMExplainabilitySummary(
        paragraph=(
            f"DeepShield's forensic pipeline analyzed this {payload.get('media_type', 'media')} and returned a verdict of '{label}' "
            f"with an authenticity score of {score}/100 and {confidence_word} model confidence. "
            f"The score is derived from deepfake detection models, artifact scanning, metadata integrity checks, and (for text) trusted-source cross-referencing. "
            f"{action}"
        ),
        signals=_fallback_signals(payload),
        bullets=[
            f"Authenticity score: {score}/100 — {'above' if score >= 50 else 'below'} the suspicion threshold of 50",
            f"Verdict: {label}",
            f"Pipeline completed: deepfake detection, artifact analysis, metadata checks",
            tail,
        ],
        model_used=f"static-fallback:{reason}",
    )
