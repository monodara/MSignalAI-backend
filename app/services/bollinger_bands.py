# backend/app/services/bollinger_bands.py
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from app.services.utils import validate_data_length, clean_series_data

logger = logging.getLogger(__name__)

def calculate_bollinger_bands(close_prices: List[float], period: int = 20, num_std: int = 2) -> Dict[str, Any]:
    if not validate_data_length(close_prices, period, "Bollinger Bands"):
        return {
            "middle": [], "upper": [], "lower": [], "status": "insufficient_data",
            "message": f"Not enough data for Bollinger Bands. Need {period} data points."
        }

    series = pd.Series(close_prices)
    middle = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std

    bb_results = {
        "middle": clean_series_data(middle),
        "upper": clean_series_data(upper),
        "lower": clean_series_data(lower),
        "status": "success"
    }
    logger.info(f"Bollinger Bands: Calculated with {len([v for v in bb_results['middle'] if v is not None])} valid points.")
    return bb_results

def detect_bollinger_band_squeeze(
    upper_band: List[Optional[float]], 
    lower_band: List[Optional[float]], 
    middle_band: List[Optional[float]], 
    timestamps: List[str], 
    squeeze_period: int = 120, 
    squeeze_threshold: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Detects Bollinger Band squeezes.
    A squeeze is identified when the bandwidth is at a historical low.
    """
    if not all(len(lst) == len(timestamps) for lst in [upper_band, lower_band, middle_band]):
        logger.warning("Squeeze Detection: Input arrays must have the same length.")
        return []

    # Convert to pandas Series for easier calculation
    upper_series = pd.Series(upper_band)
    lower_series = pd.Series(lower_band)
    middle_series = pd.Series(middle_band)

    # Calculate bandwidth
    bandwidth = (upper_series - lower_series) / middle_series

    # Calculate historical low of the bandwidth
    historical_low = bandwidth.rolling(window=squeeze_period).min()

    # Identify squeeze points
    is_squeezing = bandwidth <= historical_low * (1 + squeeze_threshold)

    squeeze_markers = []
    for i, squeezing in enumerate(is_squeezing):
        if squeezing:
            squeeze_markers.append({
                "time": timestamps[i],
                "position": "belowBar",
                "color": "#FFD700",  # Gold color for squeeze
                "shape": "circle",
                "text": "Squeeze",
            })
            
    logger.info(f"Squeeze Detection: Detected {len(squeeze_markers)} squeeze points.")
    return squeeze_markers

def detect_walking_the_bands(
    close_prices: List[float], 
    upper_band: List[Optional[float]], 
    lower_band: List[Optional[float]], 
    timestamps: List[str], 
    min_consecutive: int = 3
) -> List[Dict[str, Any]]:
    """
    Detects when the price is "walking the bands", indicating a strong trend.
    """
    if not all(len(lst) == len(timestamps) for lst in [close_prices, upper_band, lower_band]):
        logger.warning("Walking The Bands Detection: Input arrays must have the same length.")
        return []

    walking_markers = []
    consecutive_above = 0
    consecutive_below = 0

    for i in range(len(timestamps)):
        price = close_prices[i]
        upper = upper_band[i]
        lower = lower_band[i]

        if upper is None or lower is None:
            consecutive_above = 0
            consecutive_below = 0
            continue

        # Check for walking the upper band
        if price > upper:
            consecutive_above += 1
            consecutive_below = 0
            if consecutive_above >= min_consecutive:
                walking_markers.append({
                    "time": timestamps[i],
                    "position": "aboveBar",
                    "color": "#00BFFF",  # Deep Sky Blue for strong uptrend
                    "shape": "arrowUp",
                    "text": f"Strong Uptrend ({consecutive_above} periods)",
                })
        # Check for walking the lower band
        elif price < lower:
            consecutive_below += 1
            consecutive_above = 0
            if consecutive_below >= min_consecutive:
                walking_markers.append({
                    "time": timestamps[i],
                    "position": "belowBar",
                    "color": "#FF4500",  # OrangeRed for strong downtrend
                    "shape": "arrowDown",
                    "text": f"Strong Downtrend ({consecutive_below} periods)",
                })
        else:
            consecutive_above = 0
            consecutive_below = 0
            
    logger.info(f"Walking The Bands Detection: Detected {len(walking_markers)} markers.")
    return walking_markers

def detect_false_breakouts(
    close_prices: List[float], 
    upper_band: List[Optional[float]], 
    lower_band: List[Optional[float]], 
    timestamps: List[str], 
    confirmation_period: int = 2
) -> List[Dict[str, Any]]:
    """
    Detects false breakouts from the Bollinger Bands.
    """
    if not all(len(lst) == len(timestamps) for lst in [close_prices, upper_band, lower_band]):
        logger.warning("False Breakout Detection: Input arrays must have the same length.")
        return []

    breakout_markers = []
    for i in range(1, len(timestamps) - confirmation_period):
        price = close_prices[i]
        prev_price = close_prices[i-1]
        upper = upper_band[i]
        lower = lower_band[i]
        prev_upper = upper_band[i-1]
        prev_lower = lower_band[i-1]

        if upper is None or lower is None or prev_upper is None or prev_lower is None:
            continue

        # False breakout above the upper band
        if prev_price < prev_upper and price > upper:
            reverted = False
            for j in range(1, confirmation_period + 1):
                future_upper = upper_band[i+j]
                if future_upper is None:
                    reverted = False # Cannot confirm reversion if future band is None
                    break
                if close_prices[i+j] < future_upper:
                    reverted = True
                    break
            if reverted:
                breakout_markers.append({
                    "time": timestamps[i],
                    "position": "aboveBar",
                    "color": "#8A2BE2",  # BlueViolet for false breakout
                    "shape": "square",
                    "text": "False Breakout (Upper)",
                })

        # False breakout below the lower band
        if prev_price > prev_lower and price < lower:
            reverted = False
            for j in range(1, confirmation_period + 1):
                future_lower = lower_band[i+j]
                if future_lower is None:
                    reverted = False # Cannot confirm reversion if future band is None
                    break
                if close_prices[i+j] > future_lower:
                    reverted = True
                    break
            if reverted:
                breakout_markers.append({
                    "time": timestamps[i],
                    "position": "belowBar",
                    "color": "#8A2BE2",  # BlueViolet for false breakout
                    "shape": "square",
                    "text": "False Breakout (Lower)",
                })

    logger.info(f"False Breakout Detection: Detected {len(breakout_markers)} markers.")
    return breakout_markers

def detect_middle_band_support_resistance(
    close_prices: List[float], 
    middle_band: List[Optional[float]], 
    timestamps: List[str]
) -> List[Dict[str, Any]]:
    """
    Detects when the middle band acts as support or resistance.
    """
    if not all(len(lst) == len(timestamps) for lst in [close_prices, middle_band]):
        logger.warning("Middle Band Support/Resistance Detection: Input arrays must have the same length.")
        return []

    support_resistance_markers = []
    for i in range(1, len(timestamps) - 1):
        price = close_prices[i]
        prev_price = close_prices[i-1]
        next_price = close_prices[i+1]
        middle = middle_band[i]
        prev_middle = middle_band[i-1]

        if middle is None or prev_middle is None:
            continue

        # Middle band as support
        if prev_price > prev_middle and price <= middle and next_price > price:
            support_resistance_markers.append({
                "time": timestamps[i],
                "position": "belowBar",
                "color": "#32CD32",  # LimeGreen for support
                "shape": "circle",
                "text": "Middle Band Support",
            })

        # Middle band as resistance
        if prev_price < prev_middle and price >= middle and next_price < price:
            support_resistance_markers.append({
                "time": timestamps[i],
                "position": "aboveBar",
                "color": "#FF6347",  # Tomato for resistance
                "shape": "circle",
                "text": "Middle Band Resistance",
            })

    logger.info(f"Middle Band Support/Resistance Detection: Detected {len(support_resistance_markers)} markers.")
    return support_resistance_markers

def analyze_bandwidth(
    upper_band: List[Optional[float]], 
    lower_band: List[Optional[float]], 
    middle_band: List[Optional[float]],
    timestamps: List[str]
) -> Dict[str, Any]:
    """
    Analyzes the Bollinger Bandwidth to identify periods of high and low volatility.
    """
    if not all(len(lst) == len(timestamps) for lst in [upper_band, lower_band, middle_band]):
        logger.warning("Bandwidth Analysis: Input arrays must have the same length.")
        return {"bandwidth": [], "timestamps": []}

    upper_series = pd.Series(upper_band)
    lower_series = pd.Series(lower_band)
    middle_series = pd.Series(middle_band)

    bandwidth = (upper_series - lower_series) / middle_series
    
    bandwidth_results = {
        "bandwidth": clean_series_data(bandwidth),
        "timestamps": timestamps
    }
    
    logger.info(f"Bandwidth Analysis: Calculated bandwidth for {len(timestamps)} data points.")
    return bandwidth_results

def detect_extreme_deviation(
    close_prices: List[float], 
    upper_band: List[Optional[float]], 
    lower_band: List[Optional[float]], 
    timestamps: List[str],
    deviation_multiplier: float = 1.5
) -> List[Dict[str, Any]]:
    """
    Detects extreme deviation from the Bollinger Bands.
    """
    if not all(len(lst) == len(timestamps) for lst in [close_prices, upper_band, lower_band]):
        logger.warning("Extreme Deviation Detection: Input arrays must have the same length.")
        return []

    deviation_markers = []
    for i in range(len(timestamps)):
        price = close_prices[i]
        upper = upper_band[i]
        lower = lower_band[i]

        if upper is None or lower is None:
            continue

        # Assert that upper and lower are not None for type checker
        assert upper is not None
        assert lower is not None

        band_height = upper - lower
        
        # Extreme deviation above the upper band
        if price > upper + (band_height * deviation_multiplier):
            deviation_markers.append({
                "time": timestamps[i],
                "position": "aboveBar",
                "color": "#FF00FF",  # Magenta for extreme deviation
                "shape": "triangleUp",
                "text": "Extreme Deviation (Upper)",
            })

        # Extreme deviation below the lower band
        if price < lower - (band_height * deviation_multiplier):
            deviation_markers.append({
                "time": timestamps[i],
                "position": "belowBar",
                "color": "#FF00FF",  # Magenta for extreme deviation
                "shape": "triangleDown",
                "text": "Extreme Deviation (Lower)",
            })

    logger.info(f"Extreme Deviation Detection: Detected {len(deviation_markers)} markers.")
    return deviation_markers
