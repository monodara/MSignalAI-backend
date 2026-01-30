# backend/app/services/bollinger_service.py
from datetime import datetime, timezone
from fastapi import HTTPException

from app.cache.redis_cache import get_cached_data, set_cached_data
from app.services.bollinger_bands import calculate_bollinger_bands, detect_bollinger_band_squeeze, detect_walking_the_bands, detect_false_breakouts, detect_middle_band_support_resistance, analyze_bandwidth, detect_extreme_deviation
from app.services.price_service import get_stock_price_service
from typing import Dict, Any


async def get_bollinger_data_service(symbol: str, interval: str = "1day", period: int = 20, num_std: int = 2) -> Dict[str, Any]:
    """
    获取某只股票的布林带数据，优先从 Redis 缓存读取，
    不存在则从 Price Service 获取历史价格，再计算布林带并缓存。
    """
    cache_key = f"tech:{symbol}:{interval}:bollinger:{period}:{num_std}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        print(f"Bollinger Bands Service: Cache hit for {symbol}-{interval}-{period}-{num_std}")
        return cached_data

    print(f"Bollinger Bands Service: Cache miss for {symbol}-{interval}-{period}-{num_std}. Fetching price data...")
    # 1️⃣ 从 Price Service 获取历史价格
    price_data = await get_stock_price_service(symbol, interval)
    if not price_data or not price_data.get("data") or not price_data["data"].get("close"):
        print(f"Bollinger Bands Service: No price data from price_service for {symbol}-{interval}")
        raise HTTPException(status_code=400, detail="No price data available for Bollinger Bands calculation")

    close_prices = price_data["data"]["close"]
    timestamps = price_data["data"]["timestamps"]
    print(f"Bollinger Bands Service: Received {len(close_prices)} close prices from price_service.")

    # 3️⃣ 计算 Bollinger Bands
    bollinger_raw_results = calculate_bollinger_bands(close_prices, period, num_std)
    
    if bollinger_raw_results.get("status") == "insufficient_data":
        print(f"Bollinger Bands Service: Insufficient data for Bollinger Bands calculation: {bollinger_raw_results.get('message')}")
        return {
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "num_std": num_std,
            "bollinger": {
                "middle": [], "upper": [], "lower": [], "timestamps": []
            },
            "status": "insufficient_data",
            "message": bollinger_raw_results.get("message", "Not enough data for Bollinger Bands calculation.")
        }
    elif "error" in bollinger_raw_results: # Fallback for unexpected errors
        print(f"Bollinger Bands Service: Error in Bollinger Bands calculation: {bollinger_raw_results['error']}")
        raise HTTPException(status_code=400, detail=bollinger_raw_results["error"])

    # 4️⃣ 关联时间戳
    # Find the first non-None value in middle band to align timestamps
    first_valid_bb_idx = -1
    for idx, val in enumerate(bollinger_raw_results["middle"]):
        if val is not None:
            first_valid_bb_idx = idx
            break
    
    if first_valid_bb_idx == -1:
        print("Bollinger Bands Service: No valid Bollinger Bands values found after calculation.")
        return { # Return insufficient data status if no valid BB values found
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "num_std": num_std,
            "bollinger": {
                "middle": [], "upper": [], "lower": [], "timestamps": []
            },
            "status": "insufficient_data",
            "message": "Bollinger Bands calculation resulted in no valid data."
        }

    bollinger_timestamps = timestamps[first_valid_bb_idx:]
    
    # Ensure all lists have the same length
    min_len = min(len(bollinger_raw_results["middle"][first_valid_bb_idx:]), len(bollinger_timestamps))
    
    bollinger_results = {
        "middle": bollinger_raw_results["middle"][first_valid_bb_idx:first_valid_bb_idx + min_len],
        "upper": bollinger_raw_results["upper"][first_valid_bb_idx:first_valid_bb_idx + min_len],
        "lower": bollinger_raw_results["lower"][first_valid_bb_idx:first_valid_bb_idx + min_len],
        "timestamps": bollinger_timestamps[:min_len]
    }

    # 6️⃣ Detect Bollinger Band Squeeze
    squeeze_markers = detect_bollinger_band_squeeze(
        upper_band=bollinger_results["upper"],
        lower_band=bollinger_results["lower"],
        middle_band=bollinger_results["middle"],
        timestamps=bollinger_results["timestamps"]
    )
    print(f"Bollinger Bands Service: Detected {len(squeeze_markers)} squeeze markers.")

    # 7️⃣ Detect Walking the Bands
    walking_the_bands_markers = detect_walking_the_bands(
        close_prices=close_prices[first_valid_bb_idx:first_valid_bb_idx + min_len],
        upper_band=bollinger_results["upper"],
        lower_band=bollinger_results["lower"],
        timestamps=bollinger_results["timestamps"]
    )
    print(f"Bollinger Bands Service: Detected {len(walking_the_bands_markers)} walking the bands markers.")

    # 8️⃣ Detect False Breakouts
    false_breakout_markers = detect_false_breakouts(
        close_prices=close_prices[first_valid_bb_idx:first_valid_bb_idx + min_len],
        upper_band=bollinger_results["upper"],
        lower_band=bollinger_results["lower"],
        timestamps=bollinger_results["timestamps"]
    )
    print(f"Bollinger Bands Service: Detected {len(false_breakout_markers)} false breakout markers.")

    # 9️⃣ Detect Middle Band Support/Resistance
    middle_band_support_resistance_markers = detect_middle_band_support_resistance(
        close_prices=close_prices[first_valid_bb_idx:first_valid_bb_idx + min_len],
        middle_band=bollinger_results["middle"],
        timestamps=bollinger_results["timestamps"]
    )
    print(f"Bollinger Bands Service: Detected {len(middle_band_support_resistance_markers)} middle band support/resistance markers.")

    # 10️⃣ Analyze Bandwidth
    bandwidth_data = analyze_bandwidth(
        upper_band=bollinger_results["upper"],
        lower_band=bollinger_results["lower"],
        middle_band=bollinger_results["middle"],
        timestamps=bollinger_results["timestamps"]
    )
    print(f"Bollinger Bands Service: Analyzed bandwidth for {len(bandwidth_data['timestamps'])} data points.")

    # 11️⃣ Detect Extreme Deviation
    extreme_deviation_markers = detect_extreme_deviation(
        close_prices=close_prices[first_valid_bb_idx:first_valid_bb_idx + min_len],
        upper_band=bollinger_results["upper"],
        lower_band=bollinger_results["lower"],
        timestamps=bollinger_results["timestamps"]
    )
    print(f"Bollinger Bands Service: Detected {len(extreme_deviation_markers)} extreme deviation markers.")

    # 12️⃣ 缓存到 Redis
    cache_payload = {
        "symbol": symbol,
        "interval": interval,
        "period": period,
        "num_std": num_std,
        "bollinger": bollinger_results,
        "squeeze_markers": squeeze_markers,
        "walking_the_bands_markers": walking_the_bands_markers,
        "false_breakout_markers": false_breakout_markers,
        "middle_band_support_resistance_markers": middle_band_support_resistance_markers,
        "bandwidth_data": bandwidth_data,
        "extreme_deviation_markers": extreme_deviation_markers,
        "status": "success", # Indicate successful calculation
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cached_data(cache_key, cache_payload, ex=300)  # 缓存 5 分钟
    print(f"Bollinger Bands Service: Cached Bollinger Bands data for {symbol}-{interval}-{period}-{num_std}.")

    return cache_payload