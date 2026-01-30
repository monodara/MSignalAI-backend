from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def _get_value(statement: Dict[str, Any], key: str) -> Optional[float]:
    """Safely get a float value from a financial statement dictionary."""
    value = statement.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def _get_value_from_statements(statements: List[Dict[str, Any]], index: int, key: str) -> Optional[float]:
    """Safely get a float value from a specific statement in a list."""
    if len(statements) > index:
        return _get_value(statements[index], key)
    return None

def get_trend_marker(growth_percentage: Optional[float]) -> str:
    """Returns a trend marker based on growth percentage."""
    if growth_percentage is None:
        return "---" # Use "---" for unknown/no change
    if growth_percentage > 0.005: # Small positive for improvement
        return "▲"
    if growth_percentage < -0.005: # Small negative for deterioration
        return "▼"
    return "---"

def calculate_qoq_yoy_growth(
    statements: List[Dict[str, Any]], 
    field: str, 
    period_type: str = "quarter"
) -> Dict[str, Any]: # Changed return type to Any to include trend markers
    """
    Calculates Quarter-over-Quarter (QoQ) and Year-over-Year (YoY) growth for a given field.
    Assumes statements are sorted by date descending.
    """
    qoq_growth = None
    yoy_growth = None

    if not statements:
        return {
            "qoq_growth": None, "yoy_growth": None,
            "qoq_trend": "unknown", "yoy_trend": "unknown"
        }

    # QoQ Growth (compare latest quarter with previous quarter)
    if period_type == "quarter" and len(statements) >= 2:
        latest_value = _get_value(statements[0], field)
        previous_value = _get_value(statements[1], field)
        if latest_value is not None and previous_value is not None and previous_value != 0:
            qoq_growth = (latest_value - previous_value) / previous_value

    # YoY Growth (compare latest quarter with same quarter last year)
    if len(statements) >= 4: # Need at least 4 quarters for YoY
        latest_value = _get_value(statements[0], field)
        same_quarter_last_year_value = _get_value(statements[3], field) # Assuming quarterly data, 3 quarters back is same quarter last year
        if latest_value is not None and same_quarter_last_year_value is not None and same_quarter_last_year_value != 0:
            yoy_growth = (latest_value - same_quarter_last_year_value) / same_quarter_last_year_value
    
    return {
        "qoq_growth": qoq_growth,
        "yoy_growth": yoy_growth,
        "qoq_trend": get_trend_marker(qoq_growth),
        "yoy_trend": get_trend_marker(yoy_growth)
    }

def calculate_margins(income_statements: List[Dict[str, Any]]) -> Dict[str, Any]: # Changed return type to Any
    """
    Calculates Gross Profit Margin, Operating Margin, and Net Profit Margin for the latest statement, with trends.
    Assumes statements are sorted by date descending.
    """
    margins: Dict[str, Any] = {
        "grossProfitMargin": None, "grossProfitMarginTrend": "unknown",
        "operatingProfitMargin": None, "operatingProfitMarginTrend": "unknown",
        "netProfitMargin": None, "netProfitMarginTrend": "unknown",
    }

    if not income_statements:
        return margins

    # Latest period
    latest_revenue = _get_value_from_statements(income_statements, 0, "revenue")
    latest_gross_profit = _get_value_from_statements(income_statements, 0, "grossProfit")
    latest_operating_income = _get_value_from_statements(income_statements, 0, "operatingIncome")
    latest_net_income = _get_value_from_statements(income_statements, 0, "netIncome")

    if latest_revenue is not None and latest_revenue != 0:
        if latest_gross_profit is not None:
            margins["grossProfitMargin"] = latest_gross_profit / latest_revenue
        if latest_operating_income is not None:
            margins["operatingProfitMargin"] = latest_operating_income / latest_revenue
        if latest_net_income is not None:
            margins["netProfitMargin"] = latest_net_income / latest_revenue

    # Previous period for trend calculation
    if len(income_statements) >= 2:
        previous_revenue = _get_value_from_statements(income_statements, 1, "revenue")
        previous_gross_profit = _get_value_from_statements(income_statements, 1, "grossProfit")
        previous_operating_income = _get_value_from_statements(income_statements, 1, "operatingIncome")
        previous_net_income = _get_value_from_statements(income_statements, 1, "netIncome")

        if previous_revenue is not None and previous_revenue != 0:
            if latest_gross_profit is not None and previous_gross_profit is not None:
                prev_gpm = previous_gross_profit / previous_revenue
                if margins["grossProfitMargin"] is not None and prev_gpm != 0: margins["grossProfitMarginTrend"] = get_trend_marker((margins["grossProfitMargin"] - prev_gpm) / prev_gpm)
            if latest_operating_income is not None and previous_operating_income is not None:
                prev_opm = previous_operating_income / previous_revenue
                if margins["operatingProfitMargin"] is not None and prev_opm != 0: margins["operatingProfitMarginTrend"] = get_trend_marker((margins["operatingProfitMargin"] - prev_opm) / prev_opm)
            if latest_net_income is not None and previous_net_income is not None:
                prev_npm = previous_net_income / previous_revenue
                if margins["netProfitMargin"] is not None and prev_npm != 0: margins["netProfitMarginTrend"] = get_trend_marker((margins["netProfitMargin"] - prev_npm) / prev_npm)
            
    return margins

def calculate_roe(income_statements: List[Dict[str, Any]], balance_sheets: List[Dict[str, Any]]) -> Dict[str, Any]: # Changed return type
    """
    Calculates Return on Equity (ROE) for the latest period, with trend.
    Assumes statements are sorted by date descending.
    """
    roe_value = None
    roe_trend = "unknown"

    if not income_statements or not balance_sheets:
        return {"roe": None, "roe_trend": "unknown"}

    # Latest period
    latest_net_income = _get_value_from_statements(income_statements, 0, "netIncome")
    latest_total_equity = _get_value_from_statements(balance_sheets, 0, "totalEquity")

    if latest_net_income is not None and latest_total_equity is not None and latest_total_equity != 0:
        roe_value = latest_net_income / latest_total_equity

    # Previous period for trend calculation
    if len(income_statements) >= 2 and len(balance_sheets) >= 2:
        previous_net_income = _get_value_from_statements(income_statements, 1, "netIncome")
        previous_total_equity = _get_value_from_statements(balance_sheets, 1, "totalEquity")

        if previous_net_income is not None and previous_total_equity is not None and previous_total_equity != 0:
            previous_roe = previous_net_income / previous_total_equity
            if roe_value is not None and previous_roe is not None and previous_roe != 0: roe_trend = get_trend_marker((roe_value - previous_roe) / previous_roe)
            
    return {"roe": roe_value, "roe_trend": roe_trend}

def calculate_operating_cash_flow_value(cash_flow_statements: List[Dict[str, Any]]) -> Dict[str, Any]: # Changed return type
    """
    Retrieves the latest Net Cash Provided By Operating Activities, with trend.
    Assumes statements are sorted by date descending.
    """
    ocf_value = None
    ocf_trend = "unknown"

    if not cash_flow_statements:
        return {"operatingCashFlow": None, "operatingCashFlowTrend": "unknown"}

    # Latest period
    ocf_value = _get_value_from_statements(cash_flow_statements, 0, "netCashProvidedByOperatingActivities")

    # Previous period for trend calculation
    if len(cash_flow_statements) >= 2:
        previous_ocf_value = _get_value_from_statements(cash_flow_statements, 1, "netCashProvidedByOperatingActivities")
        if ocf_value is not None and previous_ocf_value is not None and previous_ocf_value != 0:
            ocf_trend = get_trend_marker((ocf_value - previous_ocf_value) / previous_ocf_value)
            
    return {"operatingCashFlow": ocf_value, "operatingCashFlowTrend": ocf_trend}

def calculate_free_cash_flow_value(cash_flow_statements: List[Dict[str, Any]]) -> Dict[str, Any]: # Changed return type
    """
    Retrieves the latest Free Cash Flow value, with trend.
    Assumes statements are sorted by date descending.
    """
    fcf_value = None
    fcf_trend = "unknown"

    if not cash_flow_statements:
        return {"freeCashFlow": None, "freeCashFlowTrend": "unknown"}

    # Latest period
    fcf_value = _get_value_from_statements(cash_flow_statements, 0, "freeCashFlow")

    # Previous period for trend calculation
    if len(cash_flow_statements) >= 2:
        previous_fcf_value = _get_value_from_statements(cash_flow_statements, 1, "freeCashFlow")
        if fcf_value is not None and previous_fcf_value is not None and previous_fcf_value != 0:
            fcf_trend = get_trend_marker((fcf_value - previous_fcf_value) / previous_fcf_value)
            
    return {"freeCashFlow": fcf_value, "freeCashFlowTrend": fcf_trend}

def calculate_current_ratio(balance_sheets: List[Dict[str, Any]]) -> Dict[str, Any]: # Changed return type
    """
    Calculates the Current Ratio for the latest balance sheet, with trend.
    Assumes statements are sorted by date descending.
    """
    current_ratio_value = None
    current_ratio_trend = "unknown"

    if not balance_sheets:
        return {"currentRatio": None, "currentRatioTrend": "unknown"}

    # Latest period
    latest_total_current_assets = _get_value_from_statements(balance_sheets, 0, "totalCurrentAssets")
    latest_total_current_liabilities = _get_value_from_statements(balance_sheets, 0, "totalCurrentLiabilities")

    if latest_total_current_assets is not None and latest_total_current_liabilities is not None and latest_total_current_liabilities != 0:
        current_ratio_value = latest_total_current_assets / latest_total_current_liabilities

    # Previous period for trend calculation
    if len(balance_sheets) >= 2:
        previous_total_current_assets = _get_value_from_statements(balance_sheets, 1, "totalCurrentAssets")
        previous_total_current_liabilities = _get_value_from_statements(balance_sheets, 1, "totalCurrentLiabilities")

        if previous_total_current_assets is not None and previous_total_current_liabilities is not None and previous_total_current_liabilities != 0:
            previous_current_ratio = previous_total_current_assets / previous_total_current_liabilities
            if current_ratio_value is not None and previous_current_ratio is not None and previous_current_ratio != 0: current_ratio_trend = get_trend_marker((current_ratio_value - previous_current_ratio) / previous_current_ratio)
            
    return {"currentRatio": current_ratio_value, "currentRatioTrend": current_ratio_trend}

def calculate_valuation_metrics() -> Dict[str, Any]: # Changed return type
    """
    Placeholder for valuation metrics (PE, Forward PE, PS), with trends.
    Requires market price data and shares outstanding, which are not directly available here.
    Returning dummy data for demonstration.
    """
    # Dummy data for demonstration purposes
    dummy_pe = 20.0
    dummy_forward_pe = 18.0
    dummy_ps = 2.5

    return {
        "peRatio": dummy_pe, "peRatioTrend": "unknown",
        "forwardPeRatio": dummy_forward_pe, "forwardPeRatioTrend": "unknown",
        "psRatio": dummy_ps, "psRatioTrend": "unknown",
    }

def calculate_fcf_continuity(cash_flow_statements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes Free Cash Flow (FCF) consistency over the last few periods.
    Assumes statements are sorted by date descending.
    """
    fcf_continuity = {
        "isConsistentPositive": False,
        "trend": "unknown", # "increasing", "decreasing", "stable", "volatile"
        "latestFcf": None
    }

    if not cash_flow_statements:
        return fcf_continuity

    fcf_values: List[float] = [f for f in [_get_value(s, "freeCashFlow") for s in cash_flow_statements] if f is not None]
    
    if not fcf_values:
        return fcf_continuity

    fcf_continuity["latestFcf"] = fcf_values[0]

    if all(f > 0 for f in fcf_values):
        fcf_continuity["isConsistentPositive"] = True
    
    if len(fcf_values) >= 3:
        # Check trend
        if fcf_values[0] > fcf_values[1] > fcf_values[2]:
            fcf_continuity["trend"] = "increasing"
        elif fcf_values[0] < fcf_values[1] < fcf_values[2]:
            fcf_continuity["trend"] = "decreasing"
        else:
            fcf_continuity["trend"] = "volatile" # Or "stable" if values are very close

    return fcf_continuity

def calculate_debt_to_equity(balance_sheets: List[Dict[str, Any]]) -> Dict[str, Any]: # Changed return type
    """
    Calculates the Debt-to-Equity ratio for the latest balance sheet, with trend.
    Assumes statements are sorted by date descending.
    """
    debt_to_equity_value = None
    debt_to_equity_trend = "unknown"

    if not balance_sheets:
        return {"debtToEquity": None, "debtToEquityTrend": "unknown"}

    # Latest period
    latest_total_debt = _get_value_from_statements(balance_sheets, 0, "totalDebt")
    latest_total_equity = _get_value_from_statements(balance_sheets, 0, "totalEquity")

    if latest_total_debt is not None and latest_total_equity is not None and latest_total_equity != 0:
        debt_to_equity_value = latest_total_debt / latest_total_equity

    # Previous period for trend calculation
    if len(balance_sheets) >= 2:
        previous_total_debt = _get_value_from_statements(balance_sheets, 1, "totalDebt")
        previous_total_equity = _get_value_from_statements(balance_sheets, 1, "totalEquity")

        if previous_total_debt is not None and previous_total_equity is not None and previous_total_equity != 0:
            previous_debt_to_equity = previous_total_debt / previous_total_equity
            if debt_to_equity_value is not None and previous_debt_to_equity is not None and previous_debt_to_equity != 0: debt_to_equity_trend = get_trend_marker((debt_to_equity_value - previous_debt_to_equity) / previous_debt_to_equity)
            
    return {"debtToEquity": debt_to_equity_value, "debtToEquityTrend": debt_to_equity_trend}