# backend/app/services/macd_service.py
from datetime import datetime, timezone
from fastapi import HTTPException

from app.cache.redis_cache import get_cached_data, set_cached_data
from app.services.macd import calculate_macd, process_macd_histogram_colors, detect_macd_crossovers, detect_macd_divergences
from app.services.price_service import get_stock_price_service
from typing import List, Dict, Any


async def get_macd_data_service(symbol: str, interval: str = "1day") -> Dict[str, Any]:
    """
    获取某只股票的 MACD 指标数据，优先从 Redis 缓存读取，
    不存在则从 Price Service 获取历史价格，再计算 MACD 并缓存。
    同时计算 MACD 柱状图颜色、交叉点和背离标记。
    """
    cache_key = f"tech:{symbol}:{interval}:macd_full" # Changed cache key to reflect full data
    cached_data = get_cached_data(cache_key)
    if cached_data:
        print(f"MACD Service: Cache hit for {symbol}-{interval}")
        return cached_data

    print(f"MACD Service: Cache miss for {symbol}-{interval}. Fetching price data...")
    # 1️⃣ 从 Price Service 获取历史价格
    price_data = await get_stock_price_service(symbol, interval)
    if not price_data or not price_data.get("data") or not price_data["data"].get("close"):
        print(f"MACD Service: No price data from price_service for {symbol}-{interval}")
        raise HTTPException(status_code=400, detail="No price data available for MACD calculation")

    close_prices: List[float] = price_data["data"]["close"]
    timestamps: List[str] = price_data["data"]["timestamps"]
    print(f"MACD Service: Received {len(close_prices)} close prices from price_service.")

    # 2️⃣ 计算 MACD 原始数据
    macd_raw_results = calculate_macd(close_prices, timestamps)
    
    if macd_raw_results.get("status") == "insufficient_data":
        print(f"MACD Service: Insufficient data for MACD calculation: {macd_raw_results.get('message')}")
        return {
            "symbol": symbol,
            "interval": interval,
            "macd_line": [],
            "signal_line": [],
            "histogram_data": [],
            "timestamps": [],
            "crossover_markers": [],
            "divergence_markers": [],
            "status": "insufficient_data",
            "message": macd_raw_results.get("message", "Not enough data for MACD calculation.")
        }
    elif "error" in macd_raw_results: # Fallback for unexpected errors
        print(f"MACD Service: Error in MACD calculation: {macd_raw_results['error']}")
        raise HTTPException(status_code=400, detail=macd_raw_results["error"])


    macd_line = macd_raw_results["macd_line"]
    signal_line = macd_raw_results["signal_line"]
    macd_histogram = macd_raw_results["macd_histogram"]
    macd_timestamps = macd_raw_results["timestamps"]
    print(f"MACD Service: MACD raw results have {len(macd_line)} data points.")

    # 3️⃣ 处理 MACD 柱状图颜色
    processed_histogram = process_macd_histogram_colors(macd_histogram, macd_timestamps)
    print(f"MACD Service: Processed histogram with {len(processed_histogram)} items.")

    # 4️⃣ 检测 MACD 交叉点
    crossover_markers = detect_macd_crossovers(macd_line, signal_line, macd_timestamps)
    print(f"MACD Service: Detected {len(crossover_markers)} crossover markers.")

    # 5️⃣ 检测 MACD 背离
    # Align price_close_data with macd_timestamps
    # Find the starting index of MACD data in the original price data
    macd_start_time = datetime.fromisoformat(macd_timestamps[0]) if macd_timestamps else None
    original_timestamps_dt = [datetime.fromisoformat(ts) for ts in timestamps]
    
    aligned_price_close_data = []
    aligned_original_timestamps = []
    
    if macd_start_time:
        start_idx_in_original = -1
        for idx, ts_dt in enumerate(original_timestamps_dt):
            if ts_dt >= macd_start_time:
                start_idx_in_original = idx
                break
                
        if start_idx_in_original != -1:
            aligned_price_close_data = close_prices[start_idx_in_original:]
            aligned_original_timestamps = timestamps[start_idx_in_original:]
        
        # Ensure aligned_price_close_data has the same length as macd_line for divergence calculation
        # This is crucial for index-based comparison in find_local_extremum
        if len(aligned_price_close_data) != len(macd_line):
            print(f"MACD Service: Mismatch in aligned price data length ({len(aligned_price_close_data)}) and MACD line length ({len(macd_line)}). Truncating.")
            min_len = min(len(aligned_price_close_data), len(macd_line))
            aligned_price_close_data = aligned_price_close_data[:min_len]
            aligned_original_timestamps = aligned_original_timestamps[:min_len]
            # macd_line and macd_timestamps are already truncated by calculate_macd if needed
            # No need to truncate here again unless there's a mismatch after calculate_macd
    else: # If macd_timestamps is empty, then no MACD data was calculated
        print("MACD Service: MACD timestamps are empty, skipping divergence calculation.")
        aligned_price_close_data = []
        aligned_original_timestamps = []


    divergence_markers = detect_macd_divergences(aligned_price_close_data, macd_line, aligned_original_timestamps)
    print(f"MACD Service: Detected {len(divergence_markers)} divergence markers.")

    # 6️⃣ 缓存到 Redis
    cache_payload = {
        "symbol": symbol,
        "interval": interval,
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram_data": processed_histogram, # Histogram with colors
        "timestamps": macd_timestamps,
        "crossover_markers": crossover_markers,
        "divergence_markers": divergence_markers,
        "status": "success", # Indicate successful calculation
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cached_data(cache_key, cache_payload, ex=300)  # 缓存 5 分钟
    print(f"MACD Service: Cached MACD data for {symbol}-{interval}.")

    return cache_payload
