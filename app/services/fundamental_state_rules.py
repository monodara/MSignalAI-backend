# backend/app/services/fundamental_state_rules.py
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

def _convert_metric_value(value_str: Optional[str]) -> Optional[float | bool]:
    """Converts a metric value string (e.g., "10.50%", "123.45", "Yes", "No") to float or bool."""
    if value_str is None or value_str == "N/A":
        return None
    
    # Handle percentage strings
    if isinstance(value_str, str) and value_str.endswith('%'):
        try:
            return float(value_str.replace('%', '')) / 100
        except ValueError:
            pass
    
    # Handle boolean strings
    if isinstance(value_str, str):
        if value_str.lower() == 'yes':
            return True
        if value_str.lower() == 'no':
            return False

    # Handle numeric strings
    try:
        # Remove commas for toLocaleString compatibility
        return float(value_str.replace(',', ''))
    except ValueError:
        return None

def _get_status_color(status: str) -> str:
    """Returns a color hex code based on the status string."""
    status_lower = status.lower()
    if status_lower in ["healthy", "strong", "positive", "cheap", "good"]:
        return "#10B981" # Green
    elif status_lower in ["weak", "volatile", "stalling", "moderate", "fair", "neutral"]:
        return "#F59E0B" # Orange
    elif status_lower in ["lossmaking", "negative", "stressed", "expensive", "bad"]:
        return "#EF4444" # Red
    return "#9CA3AF" # Gray for unknown

def assess_profitability(net_profit_margin: Optional[float], roe: Optional[float]) -> Dict[str, str]:
    """
    Assesses profitability based on net profit margin and ROE.
    Returns status and color.
    """
    status = "Unknown"
    if net_profit_margin is None and roe is None:
        status = "Unknown"
    
    # Prioritize net profit margin, then ROE
    elif net_profit_margin is not None:
        if net_profit_margin > 0.10:
            status = "Healthy"
        elif net_profit_margin > 0:
            status = "Weak"
        else:
            status = "LossMaking"
    elif roe is not None: # If no net profit margin, use ROE
        if roe > 0.15:
            status = "Healthy"
        elif roe > 0:
            status = "Weak"
        else:
            status = "LossMaking"
            
    return {"status": status, "color": _get_status_color(status)}

def assess_margin_health(margin: Optional[float]) -> Dict[str, str]:
    """Assesses the health of a margin metric."""
    status = "unknown"
    if margin is None:
        status = "unknown"
    elif margin > 0.20: # Example: >20% is good
        status = "good"
    elif margin > 0.05: # Example: 5-20% is neutral
        status = "neutral"
    else:
        status = "bad"
    return {"status": status, "color": _get_status_color(status)}

def assess_roe_health(roe: Optional[float]) -> Dict[str, str]:
    """Assesses the health of ROE."""
    status = "unknown"
    if roe is None:
        status = "unknown"
    elif roe > 0.15: # Example: >15% is good
        status = "good"
    elif roe > 0:
        status = "neutral"
    else:
        status = "bad"
    return {"status": status, "color": _get_status_color(status)}

def assess_operating_cash_flow_health(ocf: Optional[float]) -> Dict[str, str]:
    """Assesses the health of Operating Cash Flow."""
    status = "unknown"
    if ocf is None:
        status = "unknown"
    elif ocf > 0:
        status = "good"
    else:
        status = "bad"
    return {"status": status, "color": _get_status_color(status)}

def assess_free_cash_flow_health(fcf: Optional[float]) -> Dict[str, str]:
    """Assesses the health of Free Cash Flow."""
    status = "unknown"
    if fcf is None:
        status = "unknown"
    elif fcf > 0:
        status = "good"
    else:
        status = "bad"
    return {"status": status, "color": _get_status_color(status)}

def assess_debt_to_equity_health(d_e_ratio: Optional[float]) -> Dict[str, str]:
    """Assesses the health of Debt to Equity ratio."""
    status = "unknown"
    if d_e_ratio is None:
        status = "unknown"
    elif d_e_ratio < 0.5: # Example: <0.5 is good
        status = "good"
    elif d_e_ratio < 1.5: # Example: 0.5-1.5 is neutral
        status = "neutral"
    else:
        status = "bad"
    return {"status": status, "color": _get_status_color(status)}

def assess_current_ratio_health(current_ratio: Optional[float]) -> Dict[str, str]:
    """Assesses the health of Current Ratio."""
    status = "unknown"
    if current_ratio is None:
        status = "unknown"
    elif current_ratio > 2.0: # Example: >2.0 is good
        status = "good"
    elif current_ratio > 1.0: # Example: 1.0-2.0 is neutral
        status = "neutral"
    else:
        status = "bad"
    return {"status": status, "color": _get_status_color(status)}

def assess_valuation_health(pe_ratio: Optional[float], forward_pe_ratio: Optional[float], ps_ratio: Optional[float]) -> Dict[str, str]:
    """Assesses the health of valuation metrics."""
    status = "unknown"
    if pe_ratio is None and forward_pe_ratio is None and ps_ratio is None:
        status = "unknown"
    # Simplified logic for now, can be expanded
    elif (pe_ratio is not None and pe_ratio < 15) or \
         (forward_pe_ratio is not None and forward_pe_ratio < 12) or \
         (ps_ratio is not None and ps_ratio < 1):
        status = "good" # Potentially undervalued
    elif (pe_ratio is not None and pe_ratio > 30) or \
         (forward_pe_ratio is not None and forward_pe_ratio > 25) or \
         (ps_ratio is not None and ps_ratio > 5):
        status = "bad" # Potentially overvalued
    else:
        status = "neutral" # Fairly valued
    return {"status": status, "color": _get_status_color(status)}

def assess_growth(yoy_revenue_growth: Optional[float], yoy_eps_growth: Optional[float]) -> Dict[str, str]:
    """
    Assesses growth based on YoY revenue growth and EPS YoY growth.
    Returns status and color.
    """
    status = "Unknown"
    if yoy_revenue_growth is None and yoy_eps_growth is None:
        status = "Unknown"

    # Prioritize EPS growth, then revenue growth
    elif yoy_eps_growth is not None:
        if yoy_eps_growth > 0.15:
            status = "Strong"
        elif yoy_eps_growth > 0.05:
            status = "Moderate"
        elif yoy_eps_growth > 0:
            status = "Stalling"
        else:
            status = "Negative"
    elif yoy_revenue_growth is not None: # If no EPS growth, use revenue growth
        if yoy_revenue_growth > 0.15:
            status = "Strong"
        elif yoy_revenue_growth > 0.05:
            status = "Moderate"
        elif yoy_revenue_growth > 0:
            status = "Stalling"
        else:
            status = "Negative"
            
    return {"status": status, "color": _get_status_color(status)}

def assess_cashflow(is_consistent_positive_fcf: Optional[bool], fcf_trend: Optional[str], latest_fcf: Optional[float], operating_cash_flow: Optional[float]) -> Dict[str, str]:
    """
    Assesses cash flow based on Free Cash Flow continuity and latest Operating Cash Flow.
    Returns status and color.
    """
    status = "Unknown"
    if is_consistent_positive_fcf:
        status = "Positive"
    elif fcf_trend == "volatile":
        status = "Volatile"
    elif latest_fcf is not None and latest_fcf < 0:
        status = "Negative"
    elif operating_cash_flow is not None and operating_cash_flow < 0:
        status = "Negative"
    else:
        status = "Unknown"
        
    return {"status": status, "color": _get_status_color(status)}

def assess_balance_sheet(d_e_ratio: Optional[float], current_ratio: Optional[float]) -> Dict[str, str]:
    """
    Assesses balance sheet strength based on Debt-to-Equity ratio and Current Ratio.
    Returns status and color.
    """
    status = "Unknown"
    if d_e_ratio is None and current_ratio is None:
        status = "Unknown"

    # Prioritize Debt-to-Equity, then Current Ratio
    elif d_e_ratio is not None:
        if d_e_ratio < 0.5:
            status = "Strong"
        elif d_e_ratio < 1.5:
            status = "Moderate"
        else:
            status = "Stressed"
    elif current_ratio is not None: # If no D/E, use Current Ratio
        if current_ratio > 2.0:
            status = "Strong"
        elif current_ratio > 1.0:
            status = "Moderate"
        else:
            status = "Stressed"
            
    return {"status": status, "color": _get_status_color(status)}

def assess_valuation_context(pe_ratio: Optional[float], forward_pe_ratio: Optional[float], ps_ratio: Optional[float]) -> Dict[str, str]:
    """
    Assesses valuation context based on PE, Forward PE, and PS ratios.
    This is a simplified assessment and would ideally compare to industry averages.
    Returns status and color.
    """
    status = "Unknown"
    if pe_ratio is None and forward_pe_ratio is None and ps_ratio is None:
        status = "Unknown"

    # Simple heuristic: if PE/Forward PE are very high, it's expensive.
    # If very low, it's cheap. Otherwise, fair.
    # These thresholds are arbitrary and should be refined with industry data.
    elif (pe_ratio is not None and pe_ratio > 30) or \
       (forward_pe_ratio is not None and forward_pe_ratio > 25) or \
       (ps_ratio is not None and ps_ratio > 5):
        status = "Expensive"
    elif (pe_ratio is not None and pe_ratio < 10) or \
         (forward_pe_ratio is not None and forward_pe_ratio < 8) or \
         (ps_ratio is not None and ps_ratio < 1):
        status = "Cheap"
    else:
        status = "Fair"
        
    return {"status": status, "color": _get_status_color(status)}

def get_fundamental_state(
    income_statements: List[Dict[str, Any]],
    balance_sheets: List[Dict[str, Any]],
    cash_flow_statements: List[Dict[str, Any]],
    calculated_metrics: Dict[str, Any]
) -> Dict[str, Dict[str, str]]: # Changed return type to include status and color
    """
    Calculates the overall fundamental state based on various metrics.
    """
    state = {
        "profitability": {"status": "Unknown", "color": _get_status_color("Unknown")},
        "growth": {"status": "Unknown", "color": _get_status_color("Unknown")},
        "cashflow": {"status": "Unknown", "color": _get_status_color("Unknown")},
        "balanceSheet": {"status": "Unknown", "color": _get_status_color("Unknown")},
        "valuationContext": {"status": "Unknown", "color": _get_status_color("Unknown")},
    }

    # Profitability
    net_profit_margin = _convert_metric_value(calculated_metrics.get("netProfitMargin", {}).get("value"))
    roe = _convert_metric_value(calculated_metrics.get("roe", {}).get("value"))
    profitability_assessment = assess_profitability(net_profit_margin, roe)
    state["profitability"] = profitability_assessment

    # Growth
    yoy_revenue_growth = _convert_metric_value(calculated_metrics.get("revenueGrowthYoY", {}).get("value"))
    yoy_eps_growth = _convert_metric_value(calculated_metrics.get("epsGrowthYoY", {}).get("value"))
    growth_assessment = assess_growth(yoy_revenue_growth, yoy_eps_growth)
    state["growth"] = growth_assessment

    # Cashflow
    is_consistent_positive_fcf = _convert_metric_value(calculated_metrics.get("fcfConsistentPositive", {}).get("value"))
    fcf_trend = calculated_metrics.get("fcfTrend", {}).get("value") # This is already a string
    latest_fcf = _convert_metric_value(calculated_metrics.get("latestFcf", {}).get("value"))
    operating_cash_flow = _convert_metric_value(calculated_metrics.get("operatingCashFlow", {}).get("value"))
    cashflow_assessment = assess_cashflow(is_consistent_positive_fcf, fcf_trend, latest_fcf, operating_cash_flow)
    state["cashflow"] = cashflow_assessment

    # Balance Sheet
    d_e_ratio = _convert_metric_value(calculated_metrics.get("debtToEquity", {}).get("value"))
    current_ratio = _convert_metric_value(calculated_metrics.get("currentRatio", {}).get("value"))
    balance_sheet_assessment = assess_balance_sheet(d_e_ratio, current_ratio)
    state["balanceSheet"] = balance_sheet_assessment

    # Valuation Context
    pe_ratio = _convert_metric_value(calculated_metrics.get("peRatio", {}).get("value"))
    forward_pe_ratio = _convert_metric_value(calculated_metrics.get("forwardPeRatio", {}).get("value"))
    ps_ratio = _convert_metric_value(calculated_metrics.get("psRatio", {}).get("value"))
    valuation_assessment = assess_valuation_context(pe_ratio, forward_pe_ratio, ps_ratio)
    state["valuationContext"] = valuation_assessment

    return state
