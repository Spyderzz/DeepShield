"""Phase 5 smoke: unit-test news_lookup classification + endpoint wiring."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.news_lookup import (
    _domain_of, _is_factcheck, _relevance, search_news_full,
)


def test_domain():
    assert _domain_of("https://www.reuters.com/article/x") == "reuters.com"
    assert _domain_of("https://snopes.com/fact-check/abc") == "snopes.com"
    print("[OK] _domain_of")


def test_factcheck_detection():
    assert _is_factcheck("https://snopes.com/x", "Claim about moon")
    assert _is_factcheck("https://factly.in/x", "")
    assert _is_factcheck("https://example.com/x", "FACT CHECK: viral video debunked")
    assert not _is_factcheck("https://bbc.com/news/world-123", "Election results")
    print("[OK] _is_factcheck")


def test_relevance():
    assert _relevance("https://reuters.com/x") == 1.0
    assert _relevance("https://ndtv.com/x") == 0.85
    assert _relevance("https://random-blog.xyz/x") == 0.5
    print("[OK] _relevance weights")


async def test_empty_key_returns_empty():
    res = await search_news_full(["modi", "election"])
    assert res.trusted_sources == []
    assert res.contradicting_evidence == []
    assert res.total_articles == 0
    print(f"[OK] empty-key path -> {res}")


async def test_endpoint_wiring():
    import httpx
    body = {"text": "BREAKING!!! You won't BELIEVE this SHOCKING miracle cure doctors don't want you to know!!! Click now!"}
    async with httpx.AsyncClient(timeout=180.0) as c:
        r = await c.post("http://127.0.0.1:8000/api/v1/analyze/text", json=body)
    r.raise_for_status()
    j = r.json()
    assert j["media_type"] == "text"
    assert "trusted_sources" in j
    assert "contradicting_evidence" in j
    assert "news_lookup" in j["processing_summary"]["stages_completed"]
    print(f"[OK] /analyze/text -> verdict={j['verdict']['label']} "
          f"score={j['verdict']['authenticity_score']} "
          f"trusted={len(j['trusted_sources'])} contradictions={len(j['contradicting_evidence'])}")


async def main():
    test_domain()
    test_factcheck_detection()
    test_relevance()
    await test_empty_key_returns_empty()
    await test_endpoint_wiring()
    print("\n=== Phase 5 smoke PASS ===")


if __name__ == "__main__":
    asyncio.run(main())
