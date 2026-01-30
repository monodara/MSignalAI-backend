from fastapi import HTTPException
from datetime import datetime, timezone
from app.cache.redis_cache import get_cached_data, set_cached_data
from app.database.crud import insert_stock_data
from app.services.twelve_data import fetch_time_series, search_symbols
from app.config.settings import MARKET_ETFS

async def get_stock_price_service(symbol: str, interval: str = "1day"):
    cache_key = f"price:{symbol}:{interval}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data

    try:
        # Fetch historical data
        data = await fetch_time_series(symbol, interval, outputsize=200)  # outputsize 根据 MACD 等指标需求

        if not data or not data.get("values"):
            raise HTTPException(status_code=502, detail="Failed to fetch price data: No values returned from data provider.")

        # Process data
        timestamps = [v["datetime"] for v in data["values"]]
        open_prices = [float(v["open"]) for v in data["values"]]
        high_prices = [float(v["high"]) for v in data["values"]]
        low_prices = [float(v["low"]) for v in data["values"]]
        close_prices = [float(v["close"]) for v in data["values"]]
        volumes = [int(v["volume"]) for v in data["values"]]

        # Reverse to chronological order
        timestamps.reverse()
        open_prices.reverse()
        high_prices.reverse()
        low_prices.reverse()
        close_prices.reverse()
        volumes.reverse()

        # Create cached payload
        cached_payload = {
            "meta": {
                "symbol": symbol,
                "interval": interval,
                "currency": data.get("meta", {}).get("currency"),
                "exchange": data.get("meta", {}).get("exchange"),
                "source": "twelve_data",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
            "data": {
                "timestamps": timestamps,
                "open": open_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": volumes,
            }
        }
        print(f"Price Service: Successfully processed {len(timestamps)} data points for {symbol}-{interval}.")

        # Store into database
        rows = [
        {
            "datetime": ts,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        for ts, open_, high, low, close, volume in zip(
            timestamps,
            open_prices,
            high_prices,
            low_prices,
            close_prices,
            volumes,
        )
    ]
        await insert_stock_data(symbol, interval, rows)
        print(f"Price Service: Stored data for {symbol}-{interval} in DB.")

        # Store into Redis
        ttl = 86400 if interval == "1day" else 300  # Update everyday / every 5 minutes
        set_cached_data(cache_key, cached_payload, ex=ttl)
        print(f"Price Service: Cached data for {symbol}-{interval} with TTL {ttl}.")

        return cached_payload
    except HTTPException:
        # Re-raise HTTPExceptions that were already generated
        raise
    except Exception as e:
        print(f"Price Service: Unexpected error during processing for {symbol}-{interval}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing price data: {e}")

async def get_market_etfs_service():
    etf_symbols = list(MARKET_ETFS.keys())
    cache_key = "market_etfs:summary"
    cached = get_cached_data(cache_key)
    if cached:
        print("Market ETFs Service: Cache hit.")
        return cached

    print("Market ETFs Service: Cache miss. Fetching ETF data...")
    result = {}

    for symbol in etf_symbols:
        try:
            price_payload = await get_stock_price_service(symbol, interval="1day")

            data = price_payload["data"]
            meta = price_payload["meta"]

            # Get the last one 
            idx = -1

            result[symbol] = {
                "symbol": symbol,
                "name": MARKET_ETFS[symbol],
                "close": data["close"][idx],
                "open": data["open"][idx],
                "high": data["high"][idx],
                "low": data["low"][idx],
                "volume": data["volume"][idx],
                "datetime": data["timestamps"][idx],
                "currency": meta.get("currency"),
            }
            print(f"Market ETFs Service: Fetched data for ETF {symbol}.")
        except HTTPException as e:
            print(f"Market ETFs Service: Failed to fetch data for ETF {symbol}: {e.detail}")
            result[symbol] = {
                "symbol": symbol,
                "name": MARKET_ETFS[symbol],
                "error": e.detail,
            }
        except Exception as e:
            print(f"Market ETFs Service: Unexpected error for ETF {symbol}: {e}")
            result[symbol] = {
                "symbol": symbol,
                "name": MARKET_ETFS[symbol],
                "error": f"Unexpected error: {e}",
            }


    set_cached_data(cache_key, result, ex=300)
    print("Market ETFs Service: Cached market ETFs summary.")
    return result




async def search_stock_service(keyword: str):
    cache_key = f"search_stock:{keyword}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        print(f"Search Service: Cache hit for {keyword}")
        return cached_data

    print(f"Search Service: Cache miss for {keyword}. Searching symbols...")
    data = await search_symbols(keyword)
    
    set_cached_data(cache_key, data, ex=3600) # Cache for 1 hour
    print(f"Search Service: Cached search results for {keyword}.")
    return data