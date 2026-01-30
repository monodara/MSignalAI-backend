# backend/app/services/technical_state_rules.py
from typing import Dict, Any, List, Optional
import logging

from app.schemas.stock_state import TechnicalState

logger = logging.getLogger(__name__)

def assess_macd_state(macd_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assesses the MACD state based on MACD line, signal line, and histogram.
    """
    macd_status = "unknown"
    divergences: List[str] = []

    if macd_data.get("status") != "success" or not macd_data.get("macd_line"):
        return {"macd_status": "insufficient_data", "divergences": []}

    macd_line = macd_data["macd_line"]
    signal_line = macd_data["signal_line"]
    histogram = macd_data["histogram_data"]
    crossovers = macd_data.get("crossover_markers", [])
    macd_divergences = macd_data.get("divergence_markers", [])

    # Latest MACD and Signal values
    latest_macd = macd_line[-1] if macd_line else None
    latest_signal = signal_line[-1] if signal_line else None
    latest_histogram = histogram[-1] if histogram else None

    if latest_macd is not None and latest_signal is not None:
        if latest_macd > latest_signal:
            macd_status = "bullish"
        elif latest_macd < latest_signal:
            macd_status = "bearish"
        else:
            macd_status = "neutral" # MACD and Signal are equal

    # Check for recent crossovers
    if crossovers:
        latest_crossover = crossovers[-1]
        # More robust logic needed to check if crossover is truly recent
        if "Bullish Crossover" in latest_crossover.get("text", ""):
            macd_status = "bullish_crossover"
        elif "Bearish Crossover" in latest_crossover.get("text", ""):
            macd_status = "bearish_crossover"

    # Check for MACD position relative to zero
    if latest_macd is not None:
        if latest_macd > 0:
            macd_status += "_above_zero" if macd_status != "unknown" else "above_zero"
        elif latest_macd < 0:
            macd_status += "_below_zero" if macd_status != "unknown" else "below_zero"

    # Add divergences
    for div in macd_divergences:
        if "Bullish Divergence" in div.get("text", ""):
            divergences.append("bullish_macd_divergence")
        elif "Bearish Divergence" in div.get("text", ""):
            divergences.append("bearish_macd_divergence")

    return {"macd_status": macd_status, "divergences": divergences}

def assess_rsi_state(rsi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assesses the RSI state based on RSI values and divergences.
    """
    rsi_status = "unknown"
    divergences: List[str] = []

    if rsi_data.get("status") != "success" or not rsi_data.get("rsi"):
        return {"rsi_status": "insufficient_data", "divergences": []}

    rsi_values = rsi_data["rsi"]
    rsi_divergences = rsi_data.get("divergences", {})

    latest_rsi = rsi_values[-1] if rsi_values else None

    if latest_rsi is not None:
        if latest_rsi > 70:
            rsi_status = "overbought"
        elif latest_rsi < 30:
            rsi_status = "oversold"
        else:
            rsi_status = "neutral"

    for div in rsi_divergences.get("bullish", []):
        divergences.append("bullish_rsi_divergence")
    for div in rsi_divergences.get("bearish", []):
        divergences.append("bearish_rsi_divergence")

    return {"rsi_status": rsi_status, "divergences": divergences}

def assess_bollinger_state(bollinger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assesses the Bollinger Bands state based on various markers and bandwidth.
    """
    bollinger_status = "unknown"
    volatility_assessment = "unknown"
    overall_trend = "unknown" # Can be derived from walking the bands

    if bollinger_data.get("status") != "success" or not bollinger_data.get("bollinger"):
        return {"bollinger_status": "insufficient_data", "volatility_assessment": "unknown", "overall_trend": "unknown"}

    squeeze_markers = bollinger_data.get("squeeze_markers", [])
    walking_the_bands_markers = bollinger_data.get("walking_the_bands_markers", [])
    bandwidth_data = bollinger_data.get("bandwidth_data", {})

    # Squeeze detection
    if squeeze_markers:
        # Check if the latest marker is a squeeze
        latest_squeeze = squeeze_markers[-1]
        # More robust check needed for recency
        bollinger_status = "squeezing"
        volatility_assessment = "low"

    # Walking the bands detection
    if walking_the_bands_markers:
        latest_walking = walking_the_bands_markers[-1]
        if "Uptrend" in latest_walking.get("text", ""):
            bollinger_status = "walking_upper_band"
            overall_trend = "strong_uptrend"
        elif "Downtrend" in latest_walking.get("text", ""):
            bollinger_status = "walking_lower_band"
            overall_trend = "strong_downtrend"
        volatility_assessment = "expanding" # Implies expanding volatility

    # Bandwidth assessment
    bandwidth_values = bandwidth_data.get("bandwidth", [])
    if bandwidth_values:
        latest_bandwidth = bandwidth_values[-1]
        # Compare to historical average or thresholds
        # For simplicity, let's just say if it's high or low
        if latest_bandwidth is not None:
            # These thresholds are arbitrary and need tuning
            if latest_bandwidth > 0.10: # Example: >10% of price is high volatility
                volatility_assessment = "high"
            elif latest_bandwidth < 0.02: # Example: <2% of price is low volatility
                volatility_assessment = "low"
            else:
                volatility_assessment = "moderate"
    
    # If no specific status from markers, default based on volatility
    if bollinger_status == "unknown" and volatility_assessment != "unknown":
        if volatility_assessment == "low":
            bollinger_status = "contracting"
        elif volatility_assessment == "high":
            bollinger_status = "expanding"

    return {
        "bollinger_status": bollinger_status,
        "volatility_assessment": volatility_assessment,
        "overall_trend": overall_trend
    }

def get_technical_state(
    macd_data: Dict[str, Any],
    rsi_data: Dict[str, Any],
    bollinger_data: Dict[str, Any]
) -> TechnicalState:
    """
    Combines assessments from MACD, RSI, and Bollinger Bands into a comprehensive TechnicalState.
    """
    macd_assessment = assess_macd_state(macd_data)
    rsi_assessment = assess_rsi_state(rsi_data)
    bollinger_assessment = assess_bollinger_state(bollinger_data)

    technical_state = TechnicalState(
        macd_status=macd_assessment["macd_status"],
        rsi_status=rsi_assessment["rsi_status"],
        bollinger_status=bollinger_assessment["bollinger_status"],
        volatility_assessment=bollinger_assessment["volatility_assessment"]
    )

    # Aggregate divergences
    technical_state.divergences.extend(macd_assessment["divergences"])
    technical_state.divergences.extend(rsi_assessment["divergences"])

    # Determine overall trend and momentum
    # This is a simplified aggregation and can be made more sophisticated
    if "strong_uptrend" in bollinger_assessment["overall_trend"] or "bullish_crossover" in macd_assessment["macd_status"]:
        technical_state.overall_trend = "uptrend"
        technical_state.momentum_assessment = "strong_bullish"
    elif "strong_downtrend" in bollinger_assessment["overall_trend"] or "bearish_crossover" in macd_assessment["macd_status"]:
        technical_state.overall_trend = "downtrend"
        technical_state.momentum_assessment = "strong_bearish"
    elif technical_state.macd_status == "bullish" or technical_state.rsi_status == "neutral":
        technical_state.overall_trend = "sideways"
        technical_state.momentum_assessment = "neutral"
    
    return technical_state
