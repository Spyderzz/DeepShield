from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from loguru import logger

from config import settings
from schemas.common import ContradictingEvidence, TrustedSource

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


@dataclass
class NewsLookupResult:
    trusted_sources: List[TrustedSource]
    contradicting_evidence: List[ContradictingEvidence]
    total_articles: int


def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _is_factcheck(url: str, title: str) -> bool:
    dom = _domain_of(url)
    if any(fc in dom for fc in FACTCHECK_DOMAINS):
        return True
    tl = (title or "").lower()
    return any(kw in tl for kw in ("fact check", "fact-check", "debunked", "false claim", "misleading", "hoax"))


def _relevance(url: str) -> float:
    dom = _domain_of(url)
    for td, score in TRUSTED_DOMAINS.items():
        if td in dom:
            return score
    return 0.5


async def _fetch(q: str, country: Optional[str]) -> list[dict]:
    # Default to India ('in') if not specified, since project targets Indian news
    target_country = country or "in"
    params = {"apikey": settings.NEWS_API_KEY, "q": q, "language": "en", "size": 10, "country": "in"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(settings.NEWS_API_BASE_URL, params=params)
            r.raise_for_status()
            return (r.json() or {}).get("results") or []
    except Exception as e:
        logger.warning(f"News lookup failed: {e}")
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
) -> NewsLookupResult:
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
            published_at=art.get("pubDate"),
            relevance_score=_relevance(url),
        ))

    trusted.sort(key=lambda s: -s.relevance_score)
    return NewsLookupResult(
        trusted_sources=trusted[:limit],
        contradicting_evidence=contradictions[:limit],
        total_articles=len(articles),
    )
