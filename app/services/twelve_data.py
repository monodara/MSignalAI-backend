import requests
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.config.settings import TWELVE_DATA_API_KEY, TWELVE_DATA_API_URL

logger = logging.getLogger(__name__)

def _check_api_key():
    if not TWELVE_DATA_API_KEY or TWELVE_DATA_API_KEY == "your_api_key_here":
        logger.error("API key for Twelve Data is not configured.")
        raise HTTPException(status_code=500, detail="API key for Twelve Data is not configured.")

async def _make_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    _check_api_key()
    params["apikey"] = TWELVE_DATA_API_KEY
    try:
        response = requests.get(f"{TWELVE_DATA_API_URL}/{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "error":
            error_message = data.get("message", "Unknown error from data provider.")
            logger.error(f"Twelve Data API error: {error_message}")
            raise HTTPException(status_code=400, detail=f"API error from data provider: {error_message}")
        return data
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from data provider: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error from data provider: {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to data provider: {e}")
        raise HTTPException(status_code=503, detail=f"Error connecting to data provider: {e}")
    except ValueError as e: # Catches JSONDecodeError
        logger.error(f"Failed to decode JSON response from data provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to decode JSON response from data provider.")

async def fetch_time_series(symbol: str, interval: str = "1day", outputsize: Optional[int] = None) -> Dict[str, Any]:
    params = {"symbol": symbol, "interval": interval}
    if outputsize:
        params["outputsize"] = outputsize
    logger.info(f"Fetching time series for {symbol} with interval {interval}.")
    return await _make_request("time_series", params)

async def search_symbols(keyword: str) -> Dict[str, Any]:
    logger.info(f"Searching for symbols with keyword: {keyword}")
    return await _make_request("symbol_search", {"symbol": keyword})