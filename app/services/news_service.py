# backend/app/services/news_service.py
from typing import List, Dict, Any
import logging
from fastapi import HTTPException

from app.cache.redis_cache import get_cached_data, set_cached_data
from app.services.tavily_news import fetch_news_from_tavily
from app.services.gemini_formatter import format_news_with_gemini

logger = logging.getLogger(__name__)

async def get_stock_news_service(symbol: str, time_range_days: int = 1) -> List[Dict[str, Any]]:
    """
    Fetches and formats news for a given stock symbol, with caching.
    """
    cache_key = f"news:{symbol}:{time_range_days}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        logger.info(f"News Service: Cache hit for {symbol} (last {time_range_days} days).")
        return cached_data.get("events", [])

    logger.info(f"News Service: Cache miss for {symbol} (last {time_range_days} days). Fetching raw news...")
    try:
        # 1. Fetch raw news from Tavily
        raw_news = await fetch_news_from_tavily(query=symbol, time_range_days=time_range_days)
        
        if not raw_news:
            logger.info(f"News Service: No raw news found for {symbol}.")
            return []

        # 2. Format news using Gemini LLM (one by one)
        formatted_news = await format_news_with_gemini(raw_news, symbol)

        # 3. Cache the formatted news
        set_cached_data(cache_key, {"events": formatted_news}, ex=3600) # Cache for 1 hour
        logger.info(f"News Service: Cached {len(formatted_news)} formatted news events for {symbol}.")

        return formatted_news

    except HTTPException as e:
        logger.error(f"News Service: HTTP Exception for {symbol}: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"News Service: An unexpected error occurred for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing news: {e}")
