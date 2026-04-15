from __future__ import annotations

from typing import List

import httpx
from loguru import logger

from config import settings
from schemas.common import TrustedSource

TRUSTED_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "theguardian.com",
    "nytimes.com", "washingtonpost.com", "cnn.com", "npr.org", "aljazeera.com",
    "thehindu.com", "indianexpress.com", "ndtv.com", "hindustantimes.com",
    "pti.news", "factcheck.org", "snopes.com", "politifact.com",
}


def _domain_of(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


async def search_news(keywords: List[str], limit: int = 6) -> List[TrustedSource]:
    if not settings.NEWS_API_KEY or not keywords:
        return []
    q = " ".join(keywords[:4])
    params = {"apikey": settings.NEWS_API_KEY, "q": q, "language": "en", "size": 10}
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(settings.NEWS_API_BASE_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning(f"News lookup failed: {e}")
        return []

    out: List[TrustedSource] = []
    for art in (data.get("results") or [])[:limit * 2]:
        url = art.get("link") or ""
        dom = _domain_of(url)
        trusted = dom in TRUSTED_DOMAINS
        rel = 1.0 if trusted else 0.6
        out.append(TrustedSource(
            source_name=art.get("source_id") or dom or "news",
            title=art.get("title") or "",
            url=url,
            published_at=art.get("pubDate"),
            relevance_score=rel,
        ))
    out.sort(key=lambda s: -s.relevance_score)
    return out[:limit]
