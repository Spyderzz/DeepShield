"""LLM Explainability Card — Phase 12.3

Generates a plain-English summary paragraph + 3 key-signal bullets from the
full analysis payload.  Supports Gemini (default) and OpenAI providers.
Results are cached per record_id to avoid re-spending tokens.
"""

from __future__ import annotations

import hashlib
import json
import threading
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
You are DeepShield's explainability engine. Given the JSON analysis payload below,
write a concise, accessible summary for a non-technical user.

**Output format (strict JSON only — no markdown fences):**
{{
  "paragraph": "<2-3 sentence plain-English summary of the verdict and key signals>",
  "bullets": [
    "<key signal 1>",
    "<key signal 2>",
    "<key signal 3>"
  ]
}}

Rules:
- Be factual. State what the analysis found, not what you speculate.
- Reference specific indicators (e.g. "GAN artifact score", "EXIF metadata", "sensationalism level").
- If the verdict is "Likely Authentic", reassure the user and explain why.
- If the verdict is "Likely Manipulated" or "Suspicious", highlight the strongest evidence.
- Keep the paragraph under 60 words. Each bullet under 20 words.

**Analysis payload:**
{payload_json}
"""


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
        self._client = genai.Client(api_key=settings.LLM_API_KEY)
        self.model = settings.LLM_MODEL

    def generate(self, prompt: str) -> str:
        resp = self._client.models.generate_content(model=self.model, contents=prompt)
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
            max_tokens=300,
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
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


class _ProviderChain:
    """Primary provider with optional Groq fallback. On a quota error from the
    primary, transparently retries on Groq. The `last_used` attribute tracks
    which provider actually produced the response so `model_used` reflects truth.
    """

    def __init__(self, primary: _LLMProvider, fallback: _LLMProvider | None) -> None:
        self._primary = primary
        self._fallback = fallback
        self.last_used: _LLMProvider = primary

    def generate(self, prompt: str) -> str:
        try:
            text = self._primary.generate(prompt)
            self.last_used = self._primary
            return text
        except Exception as e:
            if self._fallback is None:
                raise
            logger.info(f"{self._primary.tag} failed ({type(e).__name__}) — failing over to {self._fallback.tag}")
            text = self._fallback.generate(prompt)
            self.last_used = self._fallback
            return text


_provider_lock = threading.Lock()
_provider_instance: _ProviderChain | None = None  # reset to None forces re-init with new fallback logic


def _get_provider() -> _ProviderChain:
    """Lazy-init the configured provider chain (thread-safe singleton)."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance
    with _provider_lock:
        if _provider_instance is None:
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
    return paragraph, bullets[:3]


def generate_llm_summary(
    payload: dict[str, Any],
    record_id: str | None = None,
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

    # Strip heavy base64 fields to reduce token usage
    slim_payload = {k: v for k, v in payload.items()
                    if k not in ("explainability",)}
    # Include explainability but strip base64 images
    if "explainability" in payload and isinstance(payload["explainability"], dict):
        expl = {k: v for k, v in payload["explainability"].items()
                if not k.endswith("_base64")}
        slim_payload["explainability"] = expl

    prompt_body = json.dumps(slim_payload, indent=2, default=str, sort_keys=True)
    prompt = _PROMPT_TEMPLATE.format(payload_json=prompt_body)

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
        if _is_quota_error(e):
            mark_rate_limited()
            logger.warning(f"LLM quota hit ({type(e).__name__}) — circuit open for {_COOLDOWN_SECONDS}s")
            return _fallback_summary(payload, reason="rate_limited")
        logger.error(f"LLM explainer failed: {e}")
        return LLMExplainabilitySummary(
            paragraph="Analysis complete. See the detailed indicators below for specifics.",
            bullets=["LLM explanation temporarily unavailable"],
            model_used="error",
        )


def _fallback_summary(payload: dict[str, Any], *, reason: str) -> LLMExplainabilitySummary:
    """Deterministic summary used when the LLM is unavailable (no key / rate-limited)."""
    verdict_data = payload.get("verdict", {})
    label = verdict_data.get("label", "Unknown")
    score = verdict_data.get("authenticity_score", 50)
    tail = {
        "rate_limited": "LLM paused — automatic summary shown during quota cooldown.",
        "no_api_key": "Note: Configure an LLM API key for deeper contextual analysis.",
    }.get(reason, "LLM explanation unavailable.")
    return LLMExplainabilitySummary(
        paragraph=(
            f"The DeepShield AI engine analyzed this media and determined it is '{label}' "
            f"with an authenticity score of {score}/100, derived from deepfake detection, "
            f"artifact scanning, and metadata analysis."
        ),
        bullets=[
            f"Overall Authenticity Score: {score}/100",
            f"Primary Verdict: {label}",
            tail,
        ],
        model_used=f"static-fallback:{reason}",
    )
