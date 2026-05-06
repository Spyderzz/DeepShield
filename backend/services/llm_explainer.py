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
from schemas.common import LLMExplainabilitySummary

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
You are DeepShield's AI explainability engine. Your job is to explain a media forensics analysis result in clear, plain English that a non-technical person (a news reader, student, or concerned citizen) can immediately understand and act on.

This analysis is for a **{media_kind}**.

**Output format (strict JSON only — no markdown fences):**
{{
  "paragraph": "<4-5 sentence plain-English summary: (1) state the verdict clearly, (2) explain what evidence led to that verdict, (3) mention the strongest 1-2 signals, (4) tell the user what this means for them practically — e.g. should they share this, is it reliable, should they be cautious>",
  "bullets": [
    "<signal 1: specific finding with a number or detail from the payload>",
    "<signal 2: specific finding with a number or detail from the payload>",
    "<signal 3: specific finding with a number or detail from the payload>",
    "<signal 4: what the user should do or be aware of>"
  ]
}}

**General Rules:**
- Write for a general public audience. Avoid jargon like "GAN", "cosine similarity", "EfficientNet". Use plain equivalents instead (e.g. "AI-generated image detector", "news source matching").
- Be strictly factual — only describe what the payload shows. Do NOT invent details or describe content you have not seen.
- Be specific: mention actual numbers (scores, counts, probabilities) from the payload.
- Give practical guidance: if likely real, say it is safe to share with normal caution. If suspicious/fake, warn the user clearly.
- Paragraph: 4-5 sentences, ~80-120 words. Each bullet: 15-25 words, specific.

**Media-Specific Rules (based on media_kind="{media_kind}"):**
- "image": Lead with whether the AI detector found manipulation. Explain artifact indicators and EXIF metadata findings. Mention if a face was detected and how that affects analysis. Give practical advice.
- "video": Focus on how many frames were suspicious, temporal consistency score, and audio analysis. Explain what unnatural movement or audio anomalies suggest.
- "audio": Explain voice synthesis probability, spectral findings, and what a high/low fake probability means for the listener.
- "text": Report the fake-news classifier result, sensationalism score, manipulation patterns found, and whether the claim was corroborated by trusted news sources. Tell the user if this news looks unreliable.
- "screenshot": First explain what the OCR extracted and whether the text content itself appears credible. Then explain visual layout anomalies. Be explicit if the claim in the screenshot could not be verified by any trusted news source.

**Analysis payload:**
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
    "heatmap_base64",
    "ela_base64",
    "boxes_base64",
    "heatmap_url",
    "ela_url",
    "boxes_url",
    "thumbnail_url",
    "media_path",
    "media_url",
}


def _truncate_text(value: Any, limit: int = 1200) -> Any:
    if not isinstance(value, str):
        return value
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _compact_value(key: str, value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _compact_value(k, v)
            for k, v in value.items()
            if k not in _DROP_KEYS and not str(k).endswith(_DROP_SUFFIXES)
        }
    if isinstance(value, list):
        limit = _EXPLAINABILITY_LIMITS.get(key, 10)
        return [_compact_value(key, item) for item in value[:limit]]
    return _truncate_text(value)


def _build_llm_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the compact evidence packet sent to the LLM.

    The full API response can include image overlays, many OCR boxes, per-frame
    video records, and other large fields. The summary only needs the verdict,
    strongest evidence, source matches, and pipeline context.
    """
    compact: dict[str, Any] = {}
    for key in _KEEP_TOP_LEVEL:
        if key in payload and key not in _DROP_KEYS:
            compact[key] = _compact_value(key, payload[key])

    explainability = payload.get("explainability")
    if isinstance(explainability, dict):
        compact["explainability"] = {
            key: _compact_value(key, value)
            for key, value in explainability.items()
            if key in _KEEP_EXPLAINABILITY
            and key not in _DROP_KEYS
            and not str(key).endswith(_DROP_SUFFIXES)
        }

    return compact


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


def _parse_llm_response(raw: str) -> tuple[str, list[str]]:
    """Parse the LLM's JSON response into (paragraph, bullets).
    Handles cases where the LLM wraps output in markdown fences.
    """
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    parsed = json.loads(text)
    paragraph = parsed.get("paragraph", "")
    bullets = parsed.get("bullets", [])
    if not isinstance(bullets, list):
        bullets = [str(bullets)]
    return paragraph, bullets[:5]


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

    slim_payload = _build_llm_payload(payload)

    prompt_body = json.dumps(slim_payload, separators=(",", ":"), default=str, sort_keys=True)
    prompt = _PROMPT_TEMPLATE.format(media_kind=media_kind, payload_json=prompt_body)

    # Content-hash cache — dedups "same analysis re-run" across users / record_ids
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
        # Chain handles per-provider timeouts + Groq fallback internally
        raw_response = chain.generate(prompt)
        paragraph, bullets = _parse_llm_response(raw_response)

        summary = LLMExplainabilitySummary(
            paragraph=paragraph,
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
        bullets=[
            f"Authenticity score: {score}/100 — {'above' if score >= 50 else 'below'} the suspicion threshold of 50",
            f"Verdict: {label}",
            f"Pipeline completed: deepfake detection, artifact analysis, metadata checks",
            tail,
        ],
        model_used=f"static-fallback:{reason}",
    )
