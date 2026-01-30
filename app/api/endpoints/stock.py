from fastapi import APIRouter
from app.services.price_service import get_stock_price_service
from app.services.macd_service import get_macd_data_service
from app.services.rsi_service import get_rsi_data_service
from app.services.bollinger_service import get_bollinger_data_service
from app.services.news_service import get_stock_news_service
from app.services.fundamental_service import get_fundamental_data_service

router = APIRouter()

@router.get("/stock/{symbol}/price")
async def get_stock_data(symbol: str, interval: str = "1day"):
    return await get_stock_price_service(symbol, interval)


@router.get("/stock/{symbol}/macd")
async def get_macd_data(symbol: str, interval: str = "1day"):
    return await get_macd_data_service(symbol, interval)

@router.get("/stock/{symbol}/rsi")
async def get_rsi_data(symbol: str, interval: str = "1day", period: int = 14):
    return await get_rsi_data_service(symbol, interval, period)

@router.get("/stock/{symbol}/bollinger")
async def get_bollinger_data(symbol: str, interval: str = "1day", period: int = 20, num_std: int = 2):
    return await get_bollinger_data_service(symbol, interval, period, num_std)

@router.get("/stock/{symbol}/news")
async def get_stock_news(symbol: str, time_range_days: int = 7):
    return await get_stock_news_service(symbol, time_range_days)

@router.get("/stock/{symbol}/fundamental")
async def get_fundamental_data(symbol: str, period: str = "quarter", limit: int = 4):
    return await get_fundamental_data_service(symbol, period, limit)