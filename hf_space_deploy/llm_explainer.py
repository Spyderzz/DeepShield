"""LLM Explainability Card — Phase 12.3

Generates a plain-English summary paragraph + 3 key-signal bullets from the
full analysis payload.  Supports Gemini (default) and OpenAI providers.
Results are cached per record_id to avoid re-spending tokens.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any

from loguru import logger

from config import settings
from schemas.common import LLMExplainabilitySummary

# ── In-memory cache keyed by record_id ──
_cache: dict[str, LLMExplainabilitySummary] = {}


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
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send prompt to LLM and return raw text response."""


class _GeminiProvider(_LLMProvider):
    def __init__(self) -> None:
        import google.generativeai as genai
        genai.configure(api_key=settings.LLM_API_KEY)
        self._model = genai.GenerativeModel(settings.LLM_MODEL)

    def generate(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return response.text


class _OpenAIProvider(_LLMProvider):
    def __init__(self) -> None:
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.LLM_API_KEY)

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        return response.choices[0].message.content


@lru_cache(maxsize=1)
def _get_provider() -> _LLMProvider:
    """Lazy-init the configured LLM provider (singleton)."""
    provider_name = settings.LLM_PROVIDER.lower()
    if provider_name == "openai":
        return _OpenAIProvider()
    return _GeminiProvider()


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
    # Check cache
    if record_id and record_id in _cache:
        logger.debug(f"LLM summary cache hit for record_id={record_id}")
        cached = _cache[record_id]
        cached.cached = True
        return cached

    # Guard: no API key configured
    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not set — using deterministic fallback summary")
        
        verdict_data = payload.get("verdict", {})
        label = verdict_data.get("label", "Unknown")
        score = verdict_data.get("authenticity_score", 50)
        
        return LLMExplainabilitySummary(
            paragraph=f"The DeepShield AI engine has analyzed this media and determined it is '{label}' with an authenticity score of {score}/100. We arrived at this conclusion by passing the file through our deepfake detection algorithms, artifact scanners, and metadata analyzers.",
            bullets=[
                f"Overall Authenticity Score: {score}/100",
                f"Primary Verdict: {label}",
                "Note: Configure an LLM API key for deeper contextual analysis."
            ],
            model_used="static-fallback",
        )

    # Strip heavy base64 fields to reduce token usage
    slim_payload = {k: v for k, v in payload.items()
                    if k not in ("explainability",)}
    # Include explainability but strip base64 images
    if "explainability" in payload and isinstance(payload["explainability"], dict):
        expl = {k: v for k, v in payload["explainability"].items()
                if not k.endswith("_base64")}
        slim_payload["explainability"] = expl

    prompt = _PROMPT_TEMPLATE.format(payload_json=json.dumps(slim_payload, indent=2, default=str))

    try:
        provider = _get_provider()
        raw_response = provider.generate(prompt)
        paragraph, bullets = _parse_llm_response(raw_response)

        summary = LLMExplainabilitySummary(
            paragraph=paragraph,
            bullets=bullets,
            model_used=f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}",
        )

        # Cache result
        if record_id:
            _cache[record_id] = summary

        logger.info(f"LLM summary generated via {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")
        return summary

    except json.JSONDecodeError as e:
        logger.error(f"LLM returned unparseable JSON: {e}")
        return LLMExplainabilitySummary(
            paragraph="Analysis complete. See the detailed indicators below for specifics.",
            bullets=["LLM explanation could not be parsed"],
            model_used=f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}",
        )
    except Exception as e:
        logger.error(f"LLM explainer failed: {e}")
        return LLMExplainabilitySummary(
            paragraph="Analysis complete. See the detailed indicators below for specifics.",
            bullets=["LLM explanation temporarily unavailable"],
            model_used="error",
        )
