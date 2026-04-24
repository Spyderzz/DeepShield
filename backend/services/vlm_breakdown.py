"""VLM Detailed Breakdown — Phase 14.1

Calls a vision-capable LLM (Gemini or OpenAI) to score 6 perceptual
components of an image for deepfake forensics. Cached per record_id.
"""
from __future__ import annotations

import json
from io import BytesIO
from typing import Any

from loguru import logger
from PIL import Image

from config import settings
from schemas.common import VLMBreakdown, VLMComponentScore
from services.llm_explainer import is_rate_limited, mark_rate_limited, _is_quota_error

_cache: dict[str, VLMBreakdown] = {}

_PROMPT = """\
You are DeepShield's deepfake forensics engine. Analyze this image and score \
each component for visual authenticity.

Output ONLY valid JSON (no markdown fences, no extra text):
{
  "facial_symmetry": {"score": <0-100>, "notes": "<brief observation under 15 words>"},
  "skin_texture": {"score": <0-100>, "notes": "<brief observation under 15 words>"},
  "lighting_consistency": {"score": <0-100>, "notes": "<brief observation under 15 words>"},
  "background_coherence": {"score": <0-100>, "notes": "<brief observation under 15 words>"},
  "anatomy_hands_eyes": {"score": <0-100>, "notes": "<brief observation under 15 words>"},
  "context_objects": {"score": <0-100>, "notes": "<brief observation under 15 words>"}
}

Scoring rules:
- 100 = perfectly natural/authentic for that component
- 0 = clear manipulation artifact for that component
- Score each independently based only on visual evidence in this image
- If a component is not visible (e.g. no hands present), score 75 and note "not visible in image"
"""


def _parse_response(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = [ln for ln in text.split("\n") if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _to_component(d: Any) -> VLMComponentScore:
    if isinstance(d, dict):
        return VLMComponentScore(
            score=max(0, min(100, int(d.get("score", 75)))),
            notes=str(d.get("notes", ""))[:200],
        )
    return VLMComponentScore()


def _build_breakdown(data: dict[str, Any]) -> VLMBreakdown:
    return VLMBreakdown(
        facial_symmetry=_to_component(data.get("facial_symmetry")),
        skin_texture=_to_component(data.get("skin_texture")),
        lighting_consistency=_to_component(data.get("lighting_consistency")),
        background_coherence=_to_component(data.get("background_coherence")),
        anatomy_hands_eyes=_to_component(data.get("anatomy_hands_eyes")),
        context_objects=_to_component(data.get("context_objects")),
    )


def generate_vlm_breakdown(
    image: Image.Image,
    record_id: str | None = None,
) -> VLMBreakdown | None:
    """Score 6 perceptual components via vision LLM. Returns None when unconfigured."""
    if record_id and record_id in _cache:
        cached = _cache[record_id]
        cached.cached = True
        return cached

    if not settings.LLM_API_KEY:
        logger.debug("LLM_API_KEY not set — skipping VLM breakdown")
        return None

    # Shared circuit breaker with llm_explainer — skip during cooldown
    if is_rate_limited():
        logger.debug("VLM in cooldown — skipping")
        return None

    provider = settings.LLM_PROVIDER.lower()
    model_id = settings.LLM_MODEL

    try:
        if provider == "openai":
            breakdown = _call_openai(image, model_id)
        else:
            breakdown = _call_gemini(image, model_id)

        breakdown.model_used = f"{provider}/{model_id}"
        if record_id:
            _cache[record_id] = breakdown

        logger.info(f"VLM breakdown generated via {provider}/{model_id}")
        return breakdown

    except json.JSONDecodeError as e:
        logger.error(f"VLM breakdown: unparseable JSON from LLM: {e}")
        return None
    except Exception as e:
        if _is_quota_error(e):
            mark_rate_limited()
            logger.warning(f"VLM quota hit ({type(e).__name__}) — circuit open")
            return None
        logger.error(f"VLM breakdown failed: {e}")
        return None


def _call_gemini(image: Image.Image, model_id: str) -> VLMBreakdown:
    from google import genai
    client = genai.Client(api_key=settings.LLM_API_KEY)
    response = client.models.generate_content(model=model_id, contents=[_PROMPT, image])
    return _build_breakdown(_parse_response(response.text or ""))


def _call_openai(image: Image.Image, model_id: str) -> VLMBreakdown:
    import base64
    from openai import OpenAI  # type: ignore

    buf = BytesIO()
    img = image.convert("RGB")
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    client = OpenAI(api_key=settings.LLM_API_KEY)
    response = client.chat.completions.create(
        model=model_id,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": _PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
        temperature=0.2,
        max_tokens=400,
    )
    return _build_breakdown(_parse_response(response.choices[0].message.content))
