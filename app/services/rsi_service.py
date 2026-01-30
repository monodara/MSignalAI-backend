# backend/app/services/rsi_service.py
from datetime import datetime, timezone
from fastapi import HTTPException

from app.cache.redis_cache import get_cached_data, set_cached_data
from app.services.rsi import calculate_rsi, detect_rsi_divergences
from app.services.price_service import get_stock_price_service
from typing import Dict, Any


async def get_rsi_data_service(symbol: str, interval: str = "1day", period: int = 14) -> Dict[str, Any]:
    """
    获取某只股票的 RSI 指标数据和背离信号。
    """
    cache_key = f"tech:{symbol}:{interval}:rsi_with_divergence:{period}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        print(f"RSI Service: Cache hit for {symbol}-{interval}-{period}")
        return cached_data

    print(f"RSI Service: Cache miss for {symbol}-{interval}-{period}. Fetching price data...")
    price_data = await get_stock_price_service(symbol, interval)
    if not price_data or not price_data.get("data") or not price_data["data"].get("close"):
        raise HTTPException(status_code=400, detail="No price data available for RSI calculation")

    close_prices = price_data["data"]["close"]
    timestamps = price_data["data"]["timestamps"]
    
    rsi_results = calculate_rsi(close_prices, period)
    
    if rsi_results.get("status") == "insufficient_data":
        return {
            "symbol": symbol, "interval": interval, "period": period,
            "rsi": [], "timestamps": [], "divergences": {"bullish": [], "bearish": []},
            "status": "insufficient_data", "message": rsi_results.get("message")
        }

    # Align data for divergence calculation
    rsi_values = rsi_results["rsi"]
    first_valid_idx = next((i for i, v in enumerate(rsi_values) if v is not None), -1)
    
    if first_valid_idx == -1:
        return {
            "symbol": symbol, "interval": interval, "period": period,
            "rsi": [], "timestamps": [], "divergences": {"bullish": [], "bearish": []},
            "status": "insufficient_data", "message": "RSI calculation resulted in no valid data."
        }

    aligned_rsi = rsi_values[first_valid_idx:]
    aligned_prices = close_prices[first_valid_idx:]
    aligned_timestamps = timestamps[first_valid_idx:]
    
    min_len = min(len(aligned_rsi), len(aligned_prices), len(aligned_timestamps))
    final_rsi = aligned_rsi[:min_len]
    final_prices = aligned_prices[:min_len]
    final_timestamps = aligned_timestamps[:min_len]

    # Detect divergences
    divergences = detect_rsi_divergences(
        price_data=final_prices,
        rsi_data=final_rsi,
        timestamps=final_timestamps
    )

    # Prepare payload
    payload = {
        "symbol": symbol,
        "interval": interval,
        "period": period,
        "rsi": final_rsi,
        "timestamps": final_timestamps,
        "divergences": divergences,
        "status": "success",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    
    set_cached_data(cache_key, payload, ex=300)
    print(f"RSI Service: Cached RSI and divergence data for {symbol}-{interval}-{period}.")

    return payload
