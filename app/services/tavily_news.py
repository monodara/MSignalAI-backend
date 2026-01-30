# backend/app/services/tavily_news.py
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import HTTPException
import httpx


from app.config.settings import TAVILY_API_KEY, TAVILY_API_URL

logger = logging.getLogger(__name__)

async def fetch_news_from_tavily(query: str, num_results: int = 10, time_range_days: int = 1) -> List[Dict[str, Any]]:
    """
    Fetches news articles using the Tavily API.
    """
    if not TAVILY_API_KEY:
        logger.error("Tavily API key is not configured.")
        raise HTTPException(status_code=500, detail="Tavily API key is not configured.")

    end_date = datetime.now()
    start_date_str = (end_date - timedelta(days=time_range_days)).strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "include_images": False,
        "num_results": num_results,
        "include_raw_content": False,
        "max_results": num_results,
        "q_in_url": f"after:{start_date_str} before:{end_date_str}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(TAVILY_API_URL, json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            
            return [{
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
                "published_at": r.get("published_date"),
                "source": r.get("domain"),
            } for r in data.get("results", [])]

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Tavily API: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error from Tavily API: {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Tavily API: {e}")
        raise HTTPException(status_code=503, detail=f"Error connecting to Tavily API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching news from Tavily: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

async def _get_company_name(symbol: str) -> str:
    url = f"https://api.twelvedata.com/stocks?symbol={symbol}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        
        if data.get("status") == "ok" and data.get("data"):
            return data["data"][0]["name"]
        return symbol  