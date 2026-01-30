# backend/app/services/fmp_service.py
import requests
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from app.config.settings import FMP_API_KEY, FMP_API_URL

logger = logging.getLogger(__name__)

async def _make_fmp_request(endpoint: str, symbol: str, limit: int = 4, period: str = "quarter") -> List[Dict[str, Any]]:
    """
    Helper function to make requests to the Financial Modeling Prep API.
    """
    if not FMP_API_KEY:
        logger.error("FMP API key is not configured.")
        raise HTTPException(status_code=500, detail="FMP API key is not configured.")

    url = f"{FMP_API_URL}/{endpoint}/"
    params = {
        "symbol": symbol,
        "limit": limit,
        "period": period,
        "apikey": FMP_API_KEY
    }

    try:
        logger.info(f"Fetching {endpoint} for {symbol} from FMP API.")
        response = requests.get(url, params=params)
        print(f"url: {url}")
        print(f"params: {params}")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        print(f"response data: {data}")

        if not data:
            logger.warning(f"No data found for {endpoint} for {symbol}.")
            return []
        
        return data

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from FMP API for {endpoint} {symbol}: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error from FMP API: {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to FMP API for {endpoint} {symbol}: {e}")
        raise HTTPException(status_code=503, detail=f"Error connecting to FMP API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching {endpoint} from FMP: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

async def fetch_income_statements(symbol: str, limit: int = 4, period: str = "quarter") -> List[Dict[str, Any]]:
    return await _make_fmp_request("income-statement", symbol, limit, period)

async def fetch_balance_sheets(symbol: str, limit: int = 4, period: str = "quarter") -> List[Dict[str, Any]]:
    return await _make_fmp_request("balance-sheet-statement", symbol, limit, period)

async def fetch_cash_flows(symbol: str, limit: int = 4, period: str = "quarter") -> List[Dict[str, Any]]:
    return await _make_fmp_request("cash-flow-statement", symbol, limit, period)

async def fetch_stock_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the current stock quote for a given symbol.
    """
    # The quote endpoint typically doesn't use limit or period parameters in the same way
    # as financial statements, so we'll call _make_fmp_request with adjusted parameters.
    # FMP's /quote endpoint returns a list, even for a single symbol.
    quotes = await _make_fmp_request("quote", symbol, limit=1, period="annual") # limit and period are often ignored for quote
    if quotes:
        return quotes[0] # Return the first (and likely only) quote
    return None
