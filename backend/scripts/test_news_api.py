"""Test script for the NewsData API integration."""
import asyncio
import sys
import os

# Add backend directory to sys.path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from services.news_lookup import search_news_full

async def test_news():
    print(f"Testing News API Integration with key: {settings.NEWS_API_KEY[:6]}... (masked)")
    
    if not settings.NEWS_API_KEY:
        print("ERROR: NEWS_API_KEY is empty in .env")
        return
        
    keywords = ["modi", "election", "bjp", "congress"]
    print(f"Searching for keywords: {keywords}")
    
    try:
        result = await search_news_full(keywords, limit=5)
        
        print("\n=== RAW RESULT ===")
        print(f"Total articles found: {result.total_articles}")
        
        print("\n=== TRUSTED SOURCES ===")
        for i, source in enumerate(result.trusted_sources, 1):
            date_str = str(source.published_at)[:10] if source.published_at else "Unknown date"
            print(f"{i}. [{source.relevance_score}] {source.source_name}: {source.title[:60]}... ({date_str})")
            
        print("\n=== CONTRADICTING EVIDENCE / FACT CHECKS ===")
        if not result.contradicting_evidence:
            print("No fact-check articles found for these keywords.")
        for i, ev in enumerate(result.contradicting_evidence, 1):
            print(f"{i}. {ev.source_name}: {ev.title[:60]}...")
            
    except Exception as e:
        print(f"\nERROR running test: {e}")

if __name__ == "__main__":
    asyncio.run(test_news())
