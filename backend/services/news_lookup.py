from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger

from config import settings
from schemas.common import ContradictingEvidence, TrustedSource, TruthOverride

# Trusted news domains — higher relevance boost
TRUSTED_DOMAINS = {
    "reuters.com": 1.0, "apnews.com": 1.0, "bbc.com": 1.0, "bbc.co.uk": 1.0,
    "theguardian.com": 0.95, "nytimes.com": 0.95, "washingtonpost.com": 0.95,
    "cnn.com": 0.9, "npr.org": 0.95, "aljazeera.com": 0.9,
    "thehindu.com": 0.9, "indianexpress.com": 0.9, "ndtv.com": 0.85,
    "hindustantimes.com": 0.85, "pti.news": 0.95,
}

# Fact-check / contradiction sources
FACTCHECK_DOMAINS = {
    "factcheck.org", "snopes.com", "politifact.com", "fullfact.org",
    "reuters.com/fact-check", "apnews.com/hub/ap-fact-check",
    "factly.in", "altnews.in", "boomlive.in", "vishvasnews.com",
}

# Domains eligible for truth-override (weight >= 0.9 per BUILD_PLAN spec)
_HIGH_TRUST_DOMAINS = {d for d, w in TRUSTED_DOMAINS.items() if w >= 0.9}

# Thresholds per BUILD_PLAN §13.2
_OVERRIDE_SIMILARITY_THRESHOLD = 0.6
_OVERRIDE_FAKE_PROB_CAP = 0.15
_OVERRIDE_FAKE_PROB_MULTIPLIER = 0.3


@dataclass
class NewsLookupResult:
    trusted_sources: List[TrustedSource]
    contradicting_evidence: List[ContradictingEvidence]
    total_articles: int
    truth_override: Optional[TruthOverride] = None
    # Fake-probability nudge when API key is set but returned 0 results.
    # Range [0, 1] — added to effective_fake_prob in the caller.
    no_source_penalty: float = 0.0


def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _is_factcheck(url: str, title: str) -> bool:
    parsed = urlparse(url or "")
    dom = parsed.netloc.lower().replace("www.", "")
    path_key = f"{dom}{parsed.path}".lower()
    if any(fc in dom or fc in path_key for fc in FACTCHECK_DOMAINS):
        return True
    tl = (title or "").lower()
    return any(kw in tl for kw in ("fact check", "fact-check", "debunked", "false claim", "misleading", "hoax"))


def _relevance(url: str) -> float:
    dom = _domain_of(url)
    for td, score in TRUSTED_DOMAINS.items():
        if td in dom:
            return score
    return 0.5


def _is_high_trust(url: str) -> bool:
    dom = _domain_of(url)
    return any(ht in dom for ht in _HIGH_TRUST_DOMAINS)


def _compute_truth_override(
    input_text: str,
    trusted_sources: List[TrustedSource],
    current_fake_prob: float,
) -> Optional[TruthOverride]:
    """Check if any high-trust source corroborates the input text at >= 0.6 cosine similarity.

    Per BUILD_PLAN §13.2:
    - Compute cosine similarity between input_text and each trusted-source headline+description
    - If ≥ 1 high-trust source (weight ≥ 0.9) has similarity ≥ 0.6 → apply fake_prob *= 0.3, cap at 0.15
    """
    if not input_text or not trusted_sources:
        return None

    # Filter to high-trust sources only
    high_trust = [s for s in trusted_sources if _is_high_trust(s.url)]
    if not high_trust:
        return None

    # Lazy-load sentence-transformer
    from models.model_loader import get_model_loader
    st_model = get_model_loader().load_sentence_transformer()
    if st_model is None:
        return None

    try:
        import numpy as np

        high_trust = [s for s in high_trust if (s.description or "").strip()]
        if not high_trust:
            return None

        # Encode input text and high-trust headline+description pairs. Headline
        # overlap alone is too weak to override the classifier.
        source_texts = [f"{s.title}. {s.description}" for s in high_trust]
        input_cmp = input_text[:512]
        input_terms = {
            t for t in input_cmp.lower().split()
            if len(t.strip(".,!?;:()[]{}\"'")) >= 5
            for t in [t.strip(".,!?;:()[]{}\"'")]
        }
        all_texts = [input_cmp] + source_texts

        embeddings = st_model.encode(all_texts, convert_to_numpy=True, normalize_embeddings=True)
        query_vec = embeddings[0]       # (D,)
        source_vecs = embeddings[1:]    # (N, D)

        # Cosine similarity — already normalized, so dot product = cosine similarity
        similarities = np.dot(source_vecs, query_vec)

        best_idx = int(np.argmax(similarities))
        best_sim = float(similarities[best_idx])
        best_source = high_trust[best_idx]

        logger.info(
            f"Truth-override: best similarity={best_sim:.3f} "
            f"source={best_source.source_name} url={best_source.url}"
        )

        best_terms = {
            t for t in f"{best_source.title} {best_source.description or ''}".lower().split()
            if len(t.strip(".,!?;:()[]{}\"'")) >= 5
            for t in [t.strip(".,!?;:()[]{}\"'")]
        }
        lexical_overlap = len(input_terms & best_terms) / max(len(input_terms), 1)

        if best_sim >= _OVERRIDE_SIMILARITY_THRESHOLD and lexical_overlap >= 0.35:
            new_fake_prob = min(
                current_fake_prob * _OVERRIDE_FAKE_PROB_MULTIPLIER,
                _OVERRIDE_FAKE_PROB_CAP,
            )
            logger.info(
                f"Truth-override APPLIED: fake_prob {current_fake_prob:.3f} → {new_fake_prob:.3f}"
            )
            return TruthOverride(
                applied=True,
                source_url=best_source.url,
                source_name=best_source.source_name,
                similarity=round(best_sim, 4),
                fake_prob_before=round(current_fake_prob, 4),
                fake_prob_after=round(new_fake_prob, 4),
            )

        return TruthOverride(
            applied=False,
            source_url=best_source.url,
            source_name=best_source.source_name,
            similarity=round(best_sim, 4),
            fake_prob_before=round(current_fake_prob, 4),
            fake_prob_after=round(current_fake_prob, 4),
        )

    except Exception as e:
        logger.warning(f"Truth-override computation failed: {e}")
        return None


async def _fetch(q: str, country: Optional[str]) -> list[dict]:
    params = {"apikey": settings.NEWS_API_KEY, "q": q, "language": "en", "size": 10, "country": country or "in"}
    logger.info(f"News lookup query: {q!r} country={country or 'in'}")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as c:
            r = await c.get(settings.NEWS_API_BASE_URL, params=params)
            r.raise_for_status()
            results = (r.json() or {}).get("results") or []
            logger.info(f"News lookup returned {len(results)} articles for query: {q!r}")
            return results
    except Exception as e:
        logger.warning(f"News lookup failed (query={q!r}): {e}")
        return []


async def search_news(
    keywords: List[str],
    limit: int = 6,
    country: Optional[str] = None,
) -> List[TrustedSource]:
    """Back-compat simple form — returns trusted sources only."""
    result = await search_news_full(keywords, limit=limit, country=country)
    return result.trusted_sources


async def search_news_full(
    keywords: List[str],
    limit: int = 6,
    country: Optional[str] = None,
    original_text: Optional[str] = None,
    current_fake_prob: float = 0.5,
) -> NewsLookupResult:
    """Full news lookup with truth-override support.

    Args:
        keywords: NER-extracted or frequency-extracted keywords to search.
        limit: Max sources to return.
        country: Country code for newsdata.io.
        original_text: Input text to compare against headlines for truth-override.
        current_fake_prob: Current fake probability — may be adjusted by truth-override.
    """
    if not settings.NEWS_API_KEY or not keywords:
        return NewsLookupResult([], [], 0)

    q = " ".join(keywords[:4])
    articles = await _fetch(q, country)

    seen: set[str] = set()
    trusted: List[TrustedSource] = []
    contradictions: List[ContradictingEvidence] = []

    for art in articles:
        url = art.get("link") or ""
        if not url or url in seen:
            continue
        seen.add(url)

        title = art.get("title") or ""
        dom = _domain_of(url)
        src_name = art.get("source_id") or dom or "news"

        if _is_factcheck(url, title):
            contradictions.append(ContradictingEvidence(
                source_name=src_name, title=title, url=url, type="fact_check",
            ))
            continue

        trusted.append(TrustedSource(
            source_name=src_name,
            title=title,
            url=url,
            description=art.get("description") or art.get("content"),
            published_at=art.get("pubDate"),
            relevance_score=_relevance(url),
        ))

    trusted.sort(key=lambda s: -s.relevance_score)
    trusted = trusted[:limit]

    # ── Phase 13.2: Truth-override ──
    truth_override = None
    if original_text and trusted:
        truth_override = _compute_truth_override(original_text, trusted, current_fake_prob)

    # ── No-source penalty: API key is configured but yielded 0 results.
    # Unverifiable claims should raise fake probability slightly.
    no_source_penalty = 0.0
    if settings.NEWS_API_KEY and not trusted and not contradictions:
        no_source_penalty = 0.08
        logger.info(
            f"No trusted sources found for query — applying no_source_penalty={no_source_penalty}"
        )

    return NewsLookupResult(
        trusted_sources=trusted,
        contradicting_evidence=contradictions[:limit],
        total_articles=len(articles),
        truth_override=truth_override,
        no_source_penalty=no_source_penalty,
    )
