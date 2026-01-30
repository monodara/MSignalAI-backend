# backend/app/services/macd.py
import pandas as pd
from typing import List, Dict, Any, Optional, Sequence
import logging
from app.services.utils import validate_data_length, clean_series_data

logger = logging.getLogger(__name__)

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()

def calculate_macd(close_prices: List[float], timestamps: List[str]) -> Dict[str, Any]:
    min_data_points = 34 
    if not validate_data_length(close_prices, min_data_points, "MACD"):
        return {
            "macd_line": [], "signal_line": [], "macd_histogram": [], "timestamps": [],
            "status": "insufficient_data",
            "message": f"Not enough data to calculate MACD. Need at least {min_data_points} data points."
        }

    df = pd.DataFrame({'close': close_prices}, index=pd.to_datetime(timestamps))
    ema_12 = calculate_ema(df['close'], 12)
    ema_26 = calculate_ema(df['close'], 26)
    macd_line = ema_12 - ema_26
    signal_line = calculate_ema(macd_line, 9)
    macd_histogram = macd_line - signal_line

    first_valid_index = signal_line.first_valid_index()
    if first_valid_index is None:
        logger.warning("MACD: Could not find first valid index for signal_line.")
        return {
            "macd_line": [], "signal_line": [], "macd_histogram": [], "timestamps": [],
            "status": "insufficient_data",
            "message": "Could not calculate MACD, possibly due to insufficient valid data."
        }

    macd_results = {
        "macd_line": clean_series_data(macd_line[first_valid_index:]),
        "signal_line": clean_series_data(signal_line[first_valid_index:]),
        "macd_histogram": clean_series_data(macd_histogram[first_valid_index:]),
        "timestamps": [ts.isoformat() for ts in macd_line[first_valid_index:].index],
        "status": "success"
    }
    logger.info(f"MACD: Successfully calculated with {len(macd_results['macd_line'])} data points.")
    return macd_results

def process_macd_histogram_colors(macd_histogram: List[Optional[float]], timestamps: List[str]) -> List[Dict[str, Any]]:
    if not macd_histogram or not timestamps:
        logger.warning("Histogram Colors: Empty MACD histogram or timestamps received.")
        return []
    
    histogram_data_with_colors = []
    for i, (value, time) in enumerate(zip(macd_histogram, timestamps)):
        color = '#CCCCCC'  # Default for missing data
        if value is not None:
            prev_value: float = 0.0
            if i > 0:
                val_at_prev_i = macd_histogram[i - 1]
                if val_at_prev_i is not None:
                    prev_value = val_at_prev_i

            if value > 0:
                color = '#66BB6A' if value < prev_value else '#26a69a'
            else:
                color = '#EF9A9A' if value > prev_value else '#ef5350'
        histogram_data_with_colors.append({"time": time, "value": value, "color": color})
    logger.info(f"Histogram Colors: Processed {len(histogram_data_with_colors)} items.")
    return histogram_data_with_colors

def detect_macd_crossovers(macd_line: List[Optional[float]], signal_line: List[Optional[float]], timestamps: List[str]) -> List[Dict[str, Any]]:
    if not macd_line or not signal_line or not timestamps:
        logger.warning("Crossovers: Empty MACD line, signal line or timestamps received.")
        return []

    crossover_markers = []
    for i in range(1, len(macd_line)):
        prev_macd, current_macd = macd_line[i - 1], macd_line[i]
        prev_signal, current_signal = signal_line[i - 1], signal_line[i]

        if prev_macd is None or current_macd is None or prev_signal is None or current_signal is None:
            continue

        if prev_macd < prev_signal and current_macd > current_signal:
            crossover_markers.append({
                "time": timestamps[i], "position": "aboveBar", "color": "#00FF00", "shape": "arrowUp", "text": "Bullish Crossover",
            })
        elif prev_macd > prev_signal and current_macd < current_signal:
            crossover_markers.append({
                "time": timestamps[i], "position": "belowBar", "color": "#FF0000", "shape": "arrowDown", "text": "Bearish Crossover",
            })
    logger.info(f"Crossovers: Detected {len(crossover_markers)} markers.")
    return crossover_markers

def find_local_extremum(data: Sequence[Optional[float]], index: int, lookback_window: int, extremum_type: str) -> Optional[Dict[str, Any]]:
    if not data or index < lookback_window or index >= len(data) - lookback_window:
        return None

    current_value = data[index]
    if current_value is None:
        return None

    is_extremum = True
    for j in range(index - lookback_window, index + lookback_window + 1):
        if j == index:
            continue
        
        compare_value = data[j]
        if compare_value is None:
            is_extremum = False
            break

        if extremum_type == 'low' and compare_value < current_value:
            is_extremum = False
            break
        if extremum_type == 'high' and compare_value > current_value:
            is_extremum = False
            break
    
    return {"value": current_value, "index": index} if is_extremum else None

def detect_macd_divergences(price_close_data: Sequence[Optional[float]], macd_line: Sequence[Optional[float]], timestamps: List[str]) -> List[Dict[str, Any]]:
    if not price_close_data or not macd_line or not timestamps:
        logger.warning("Divergences: Empty price close data, MACD line or timestamps received.")
        return []

    divergence_markers = []
    lookback_window = 5

    price_extremums = []
    for i in range(len(price_close_data)):
        for extremum_type in ['low', 'high']:
            extremum = find_local_extremum(price_close_data, i, lookback_window, extremum_type)
            if extremum:
                price_extremums.append({"type": extremum_type, "time": timestamps[i], "value": extremum["value"], "index": i})

    price_lows = sorted([e for e in price_extremums if e["type"] == "low"], key=lambda x: x["index"])
    price_highs = sorted([e for e in price_extremums if e["type"] == "high"], key=lambda x: x["index"])

    for i in range(1, len(price_lows)):
        prev_low, current_low = price_lows[i-1], price_lows[i]
        if current_low["value"] < prev_low["value"]:
            current_macd = macd_line[current_low["index"]] if current_low["index"] < len(macd_line) else None
            prev_macd = macd_line[prev_low["index"]] if prev_low["index"] < len(macd_line) else None
            if current_macd is not None and prev_macd is not None and current_macd > prev_macd:
                divergence_markers.append({
                    "time": current_low["time"], "position": "belowBar", "color": "#008000", "shape": "arrowUp", "text": "Bullish Divergence",
                })

    for i in range(1, len(price_highs)):
        prev_high, current_high = price_highs[i-1], price_highs[i]
        if current_high["value"] > prev_high["value"]:
            current_macd = macd_line[current_high["index"]] if current_high["index"] < len(macd_line) else None
            prev_macd = macd_line[prev_high["index"]] if prev_high["index"] < len(macd_line) else None
            if current_macd is not None and prev_macd is not None and current_macd < prev_macd:
                divergence_markers.append({
                    "time": current_high["time"], "position": "aboveBar", "color": "#800000", "shape": "arrowDown", "text": "Bearish Divergence",
                })

    logger.info(f"Divergences: Detected {len(divergence_markers)} markers.")
    return divergence_markers
