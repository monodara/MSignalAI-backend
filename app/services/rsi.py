# backend/app/services/rsi.py
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from scipy.signal import find_peaks
from app.services.utils import validate_data_length, clean_series_data

logger = logging.getLogger(__name__)

def calculate_rsi(close_prices: List[float], period: int = 14) -> Dict[str, Any]:
    if not validate_data_length(close_prices, period + 1, "RSI"):
        return {
            "rsi": [], "status": "insufficient_data",
            "message": f"Not enough data to calculate RSI. Need at least {period + 1} data points."
        }

    df = pd.DataFrame({'close': close_prices})
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    rsi_values = clean_series_data(rsi)
    
    if not any(v is not None for v in rsi_values):
        logger.warning("RSI: Calculation resulted in no valid data.")
        return {"rsi": [], "status": "insufficient_data", "message": "RSI calculation resulted in no valid data."}
    
    logger.info(f"RSI: Successfully calculated with {len([v for v in rsi_values if v is not None])} valid data points.")
    return {"rsi": rsi_values, "status": "success"}


def detect_rsi_divergences(
    price_data: List[float], 
    rsi_data: List[Optional[float]], 
    timestamps: List[str],
    lookback: int = 60, 
    peak_prominence: float = 1.0, 
    trough_prominence: float = 1.0
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detects bullish and bearish RSI divergences.
    - Bullish: Lower low in price, higher low in RSI.
    - Bearish: Higher high in price, lower high in RSI.
    """
    if len(price_data) != len(rsi_data) or len(price_data) != len(timestamps):
        logger.warning("Divergence Detection: Input arrays must have the same length.")
        return {"bullish": [], "bearish": []}

    price_series = pd.Series(price_data)
    rsi_series = pd.Series(rsi_data)

    # Find peaks (for bearish divergence)
    price_peaks, _ = find_peaks(price_series, prominence=peak_prominence)
    rsi_peaks, _ = find_peaks(rsi_series, prominence=peak_prominence)

    # Find troughs (for bullish divergence) by inverting the series
    price_troughs, _ = find_peaks(-price_series, prominence=trough_prominence)
    rsi_troughs, _ = find_peaks(-rsi_series, prominence=trough_prominence)

    divergences = {"bullish": [], "bearish": []}

    # --- Bearish Divergence Detection ---
    rsi_peak_indices = set(rsi_peaks)
    recent_price_peaks = [p for p in price_peaks if p >= len(price_series) - lookback]
    
    if len(recent_price_peaks) >= 2:
        for i in range(len(recent_price_peaks) - 1):
            for j in range(i + 1, len(recent_price_peaks)):
                p1_idx, p2_idx = recent_price_peaks[i], recent_price_peaks[j]

                if price_series[p2_idx] > price_series[p1_idx]:
                    rsi_p1_idx = min(rsi_peak_indices, key=lambda x: abs(x - p1_idx), default=None)
                    rsi_p2_idx = min(rsi_peak_indices, key=lambda x: abs(x - p2_idx), default=None)

                    if rsi_p1_idx is not None and rsi_p2_idx is not None and rsi_p1_idx != rsi_p2_idx:
                        if rsi_series[rsi_p2_idx] < rsi_series[rsi_p1_idx]:
                            divergences["bearish"].append({
                                "price_start": {"time": timestamps[p1_idx], "value": price_series[p1_idx]},
                                "price_end": {"time": timestamps[p2_idx], "value": price_series[p2_idx]},
                                "rsi_start": {"time": timestamps[rsi_p1_idx], "value": rsi_series[rsi_p1_idx]},
                                "rsi_end": {"time": timestamps[rsi_p2_idx], "value": rsi_series[rsi_p2_idx]},
                            })

    # --- Bullish Divergence Detection ---
    rsi_trough_indices = set(rsi_troughs)
    recent_price_troughs = [t for t in price_troughs if t >= len(price_series) - lookback]

    if len(recent_price_troughs) >= 2:
        for i in range(len(recent_price_troughs) - 1):
            for j in range(i + 1, len(recent_price_troughs)):
                t1_idx, t2_idx = recent_price_troughs[i], recent_price_troughs[j]

                if price_series[t2_idx] < price_series[t1_idx]:
                    rsi_t1_idx = min(rsi_trough_indices, key=lambda x: abs(x - t1_idx), default=None)
                    rsi_t2_idx = min(rsi_trough_indices, key=lambda x: abs(x - t2_idx), default=None)

                    if rsi_t1_idx is not None and rsi_t2_idx is not None and rsi_t1_idx != rsi_t2_idx:
                        if rsi_series[rsi_t2_idx] > rsi_series[rsi_t1_idx]:
                            divergences["bullish"].append({
                                "price_start": {"time": timestamps[t1_idx], "value": price_series[t1_idx]},
                                "price_end": {"time": timestamps[t2_idx], "value": price_series[t2_idx]},
                                "rsi_start": {"time": timestamps[rsi_t1_idx], "value": rsi_series[rsi_t1_idx]},
                                "rsi_end": {"time": timestamps[rsi_t2_idx], "value": rsi_series[rsi_t2_idx]},
                            })
    
    logger.info(f"Divergences: Detected {len(divergences['bullish'])} bullish and {len(divergences['bearish'])} bearish RSI divergences.")
    return divergences
