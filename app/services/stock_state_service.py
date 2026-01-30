# backend/app/services/stock_state_service.py
import logging
import asyncio
from typing import Dict, Any, List
from fastapi import HTTPException

from app.schemas.stock_state import StockState, TechnicalState, FundamentalState, NewsState, FundamentalStateItem
from app.services.price_service import get_stock_price_service
from app.services.macd_service import get_macd_data_service
from app.services.rsi_service import get_rsi_data_service
from app.services.bollinger_service import get_bollinger_data_service
from app.services.news_service import get_stock_news_service
from app.services.fundamental_service import get_fundamental_data_service
from app.services.fundamental_state_rules import get_fundamental_state as get_calculated_fundamental_state # Alias to avoid name collision
from app.services.technical_state_rules import get_technical_state # Import new technical state rules
from app.services.news_state_rules import get_news_state # Import new news state rules

logger = logging.getLogger(__name__)

async def get_stock_state_for_analysis(symbol: str, timeframe: str = "1day") -> StockState:
    """
    Aggregates all necessary data (technical, fundamental, news) to construct a StockState object.
    """
    # 1. Fetch Fundamental Data
    fundamental_data_raw = await get_fundamental_data_service(symbol, period="quarter", limit=4)
    
    # Extract fundamental state from the raw fundamental data
    fundamental_state_dict = fundamental_data_raw.get("fundamentalState", {})
    fundamental_state = FundamentalState(
        profitability=FundamentalStateItem(**fundamental_state_dict.get("profitability", {"status": "Unknown", "color": "#9CA3AF"})),
        growth=FundamentalStateItem(**fundamental_state_dict.get("growth", {"status": "Unknown", "color": "#9CA3AF"})),
        cashflow=FundamentalStateItem(**fundamental_state_dict.get("cashflow", {"status": "Unknown", "color": "#9CA3AF"})),
        balanceSheet=FundamentalStateItem(**fundamental_state_dict.get("balanceSheet", {"status": "Unknown", "color": "#9CA3AF"})),
        valuationContext=FundamentalStateItem(**fundamental_state_dict.get("valuationContext", {"status": "Unknown", "color": "#9CA3AF"}))
    )

    # 2. Fetch Technical Data (MACD, RSI, Bollinger Bands)
    macd_data, rsi_data, bollinger_data = await asyncio.gather(
        get_macd_data_service(symbol, timeframe),
        get_rsi_data_service(symbol, timeframe),
        get_bollinger_data_service(symbol, timeframe)
    )

    # 3. Fetch News Data
    news_data = await get_stock_news_service(symbol, time_range_days=7)

    # 4. Construct TechnicalState
    technical_state = get_technical_state(macd_data, rsi_data, bollinger_data)

    # 5. Construct NewsState
    news_state = get_news_state(news_data)

    # 6. Assemble the final StockState
    stock_state = StockState(
        symbol=symbol,
        timeframe=timeframe,
        technical_state=technical_state,
        fundamental_state=fundamental_state,
        news_state=news_state
    )

    return stock_state