import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
from fastapi import HTTPException

from app.cache.redis_cache import get_cached_data, set_cached_data, clear_cache
from app.services.fmp_service import fetch_income_statements, fetch_balance_sheets, fetch_cash_flows
from app.database.crud import (
    insert_income_statement, get_income_statements_from_db,
    insert_balance_sheet, get_balance_sheets_from_db,
    insert_cash_flow_statement, get_cash_flow_statements_from_db
)
from app.services.fundamental_calculations import (
    calculate_qoq_yoy_growth, calculate_margins,
    calculate_fcf_continuity, calculate_debt_to_equity,
    calculate_roe, calculate_operating_cash_flow_value, calculate_current_ratio,
    calculate_valuation_metrics, calculate_free_cash_flow_value
)
from app.services.fundamental_state_rules import (
    get_fundamental_state, _get_status_color,
    assess_margin_health, assess_roe_health, assess_operating_cash_flow_health,
    assess_free_cash_flow_health, assess_debt_to_equity_health,
    assess_current_ratio_health, assess_valuation_health
)

logger = logging.getLogger(__name__)

def _create_metric_item(
    name: str,
    value: Optional[float],
    trend: Optional[str] = None,
    status: Optional[str] = None,
    color: Optional[str] = None, # Added color parameter
    is_percentage: bool = False,
    decimal_places: int = 2
) -> Dict[str, Any]:
    """Helper to create a MetricItem dictionary."""
    display_value = "N/A"
    if value is not None:
        if is_percentage:
            display_value = f"{(value * 100):.{decimal_places}f}%"
        else:
            display_value = f"{value:,.{decimal_places}f}"

    item = {
        "name": name,
        "value": display_value,
        "trend": trend if trend else "unknown", # Use "unknown" for consistency
        "status": status if status else "unknown",
        "color": color if color else _get_status_color(status if status else "unknown")
    }
    return item

async def get_fundamental_data_service(symbol: str, period: str = "quarter", limit: int = 4) -> Dict[str, Any]:
    """
    Fetches, calculates, and assesses fundamental data for a given stock symbol, with caching.
    """
    cache_key = f"fundamental:{symbol}:{period}:{limit}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        logger.info(f"Fundamental Service: Cache hit for {symbol} ({period}, {limit}).")
        return cached_data

    logger.info(f"Fundamental Service: Cache miss for {symbol} ({period}, {limit}).")
    
    income_statements_db = []
    balance_sheets_db = []
    cash_flow_statements_db = []

    try:
        # Try to retrieve from DB first
        income_statements_db = await get_income_statements_from_db(symbol, limit, period)
        balance_sheets_db = await get_balance_sheets_from_db(symbol, limit, period)
        cash_flow_statements_db = await get_cash_flow_statements_from_db(symbol, limit, period)

        if not income_statements_db or not balance_sheets_db or not cash_flow_statements_db:
            logger.info(f"Fundamental Service: Data not complete in DB for {symbol}. Fetching from FMP API...")
            # 1. Fetch raw financial statements from FMP in parallel
            income_statements, balance_sheets, cash_flow_statements = await asyncio.gather(
                fetch_income_statements(symbol, limit, period),
                fetch_balance_sheets(symbol, limit, period),
                fetch_cash_flows(symbol, limit, period)
            )

            # 2. Store fetched data into SQLite
            for statement in income_statements:
                await insert_income_statement(symbol, statement)
            for statement in balance_sheets:
                await insert_balance_sheet(symbol, statement)
            for statement in cash_flow_statements:
                await insert_cash_flow_statement(symbol, statement)
            
            # Re-retrieve from DB to ensure consistent data structure and order after insertion
            income_statements_db = await get_income_statements_from_db(symbol, limit, period)
            balance_sheets_db = await get_balance_sheets_from_db(symbol, limit, period)
            cash_flow_statements_db = await get_cash_flow_statements_from_db(symbol, limit, period)
        else:
            logger.info(f"Fundamental Service: Data found in DB for {symbol}. Using cached DB data.")

        if not income_statements_db and not balance_sheets_db and not cash_flow_statements_db:
            raise HTTPException(status_code=404, detail=f"No fundamental data found for {symbol}.")

        # 3. Perform fundamental calculations and create MetricItems
        calculated_metrics = {}
        
        # Revenue Growth
        revenue_growth_data = calculate_qoq_yoy_growth(income_statements_db, "revenue", period)
        calculated_metrics["revenueGrowthQoQ"] = _create_metric_item(
            name="Revenue QoQ Growth",
            value=revenue_growth_data.get("qoq_growth"),
            trend=revenue_growth_data.get("qoq_trend"),
            is_percentage=True
        )
        calculated_metrics["revenueGrowthYoY"] = _create_metric_item(
            name="Revenue YoY Growth",
            value=revenue_growth_data.get("yoy_growth"),
            trend=revenue_growth_data.get("yoy_trend"),
            is_percentage=True
        )

        # EPS Growth
        eps_growth_data = calculate_qoq_yoy_growth(income_statements_db, "eps", period)
        calculated_metrics["epsGrowthQoQ"] = _create_metric_item(
            name="EPS QoQ Growth",
            value=eps_growth_data.get("qoq_growth"),
            trend=eps_growth_data.get("qoq_trend"),
            is_percentage=True
        )
        calculated_metrics["epsGrowthYoY"] = _create_metric_item(
            name="EPS YoY Growth",
            value=eps_growth_data.get("yoy_growth"),
            trend=eps_growth_data.get("yoy_trend"),
            is_percentage=True
        )

        # Margins
        margins_data = calculate_margins(income_statements_db)
        gross_profit_margin_health = assess_margin_health(margins_data.get("grossProfitMargin"))
        operating_profit_margin_health = assess_margin_health(margins_data.get("operatingProfitMargin"))
        net_profit_margin_health = assess_margin_health(margins_data.get("netProfitMargin"))

        calculated_metrics["grossProfitMargin"] = _create_metric_item(
            name="Gross Profit Margin",
            value=margins_data.get("grossProfitMargin"),
            is_percentage=True,
            trend=margins_data.get("grossProfitMarginTrend"),
            status=gross_profit_margin_health["status"],
            color=gross_profit_margin_health["color"]
        )
        calculated_metrics["operatingProfitMargin"] = _create_metric_item(
            name="Operating Profit Margin",
            value=margins_data.get("operatingProfitMargin"),
            is_percentage=True,
            trend=margins_data.get("operatingProfitMarginTrend"),
            status=operating_profit_margin_health["status"],
            color=operating_profit_margin_health["color"]
        )
        calculated_metrics["netProfitMargin"] = _create_metric_item(
            name="Net Profit Margin",
            value=margins_data.get("netProfitMargin"),
            is_percentage=True,
            trend=margins_data.get("netProfitMarginTrend"),
            status=net_profit_margin_health["status"],
            color=net_profit_margin_health["color"]
        )

        # ROE
        roe_data = calculate_roe(income_statements_db, balance_sheets_db)
        roe_health = assess_roe_health(roe_data.get("roe"))
        calculated_metrics["roe"] = _create_metric_item(
            name="Return on Equity (ROE)",
            value=roe_data.get("roe"),
            is_percentage=True,
            trend=roe_data.get("roe_trend"),
            status=roe_health["status"],
            color=roe_health["color"]
        )

        # Operating Cash Flow
        operating_cash_flow_data = calculate_operating_cash_flow_value(cash_flow_statements_db)
        operating_cash_flow_health = assess_operating_cash_flow_health(operating_cash_flow_data.get("operatingCashFlow"))
        calculated_metrics["operatingCashFlow"] = _create_metric_item(
            name="Operating Cash Flow",
            value=operating_cash_flow_data.get("operatingCashFlow"),
            decimal_places=0,
            trend=operating_cash_flow_data.get("operatingCashFlowTrend"),
            status=operating_cash_flow_health["status"],
            color=operating_cash_flow_health["color"]
        )

        # Free Cash Flow
        free_cash_flow_data = calculate_free_cash_flow_value(cash_flow_statements_db)
        free_cash_flow_health = assess_free_cash_flow_health(free_cash_flow_data.get("freeCashFlow"))
        calculated_metrics["freeCashFlow"] = _create_metric_item(
            name="Free Cash Flow",
            value=free_cash_flow_data.get("freeCashFlow"),
            decimal_places=0,
            trend=free_cash_flow_data.get("freeCashFlowTrend"),
            status=free_cash_flow_health["status"],
            color=free_cash_flow_health["color"]
        )

        # FCF Continuity
        fcf_continuity_data = calculate_fcf_continuity(cash_flow_statements_db)
        # For fcfConsistentPositive, we directly use the boolean and map to status/color
        calculated_metrics["fcfConsistentPositive"] = _create_metric_item(
            name="FCF Consistent Positive",
            value=1 if fcf_continuity_data.get("isConsistentPositive") else 0, # Represent boolean as 1/0 for MetricItem
            status="good" if fcf_continuity_data.get("isConsistentPositive") else "bad",
            color=_get_status_color("good" if fcf_continuity_data.get("isConsistentPositive") else "bad"),
            decimal_places=0
        )
        # For fcfTrend, the trend is already a string, we just need to map it to status/color
        fcf_trend_status = "good" if fcf_continuity_data.get("trend") == "increasing" else ("bad" if fcf_continuity_data.get("trend") == "decreasing" else "neutral")
        calculated_metrics["fcfTrend"] = _create_metric_item(
            name="FCF Trend",
            value=None, # No direct numeric value for trend
            trend=fcf_continuity_data.get("trend"),
            status=fcf_trend_status,
            color=_get_status_color(fcf_trend_status)
        )
        # Determine status for Latest FCF
        latest_fcf_value = fcf_continuity_data.get("latestFcf")
        latest_fcf_status = "good" if latest_fcf_value is not None and latest_fcf_value > 0 else ("bad" if latest_fcf_value is not None and latest_fcf_value < 0 else "unknown")
        logger.debug(f"Latest FCF Value: {latest_fcf_value}, Status: {latest_fcf_status}")

        calculated_metrics["latestFcf"] = _create_metric_item(
            name="Latest FCF",
            value=latest_fcf_value,
            decimal_places=0,
            trend=free_cash_flow_data.get("freeCashFlowTrend"),
            status=latest_fcf_status,
            color=_get_status_color(latest_fcf_status)
        )

        # Debt to Equity
        debt_to_equity_data = calculate_debt_to_equity(balance_sheets_db)
        debt_to_equity_health = assess_debt_to_equity_health(debt_to_equity_data.get("debtToEquity"))
        calculated_metrics["debtToEquity"] = _create_metric_item(
            name="Debt to Equity",
            value=debt_to_equity_data.get("debtToEquity"),
            trend=debt_to_equity_data.get("debtToEquityTrend"),
            status=debt_to_equity_health["status"],
            color=debt_to_equity_health["color"]
        )

        # Current Ratio
        current_ratio_data = calculate_current_ratio(balance_sheets_db)
        current_ratio_health = assess_current_ratio_health(current_ratio_data.get("currentRatio"))
        calculated_metrics["currentRatio"] = _create_metric_item(
            name="Current Ratio",
            value=current_ratio_data.get("currentRatio"),
            trend=current_ratio_data.get("currentRatioTrend"),
            status=current_ratio_health["status"],
            color=current_ratio_health["color"]
        )

        # Valuation Metrics
        valuation_metrics_data = calculate_valuation_metrics()
        valuation_health = assess_valuation_health(
            valuation_metrics_data.get("peRatio"),
            valuation_metrics_data.get("forwardPeRatio"),
            valuation_metrics_data.get("psRatio")
        )
        calculated_metrics["peRatio"] = _create_metric_item(
            name="PE Ratio",
            value=valuation_metrics_data.get("peRatio"),
            trend=valuation_metrics_data.get("peRatioTrend"),
            status=valuation_health["status"],
            color=valuation_health["color"]
        )
        calculated_metrics["forwardPeRatio"] = _create_metric_item(
            name="Forward PE Ratio",
            value=valuation_metrics_data.get("forwardPeRatio"),
            trend=valuation_metrics_data.get("forwardPeRatioTrend"),
            status=valuation_health["status"],
            color=valuation_health["color"]
        )
        calculated_metrics["psRatio"] = _create_metric_item(
            name="PS Ratio",
            value=valuation_metrics_data.get("psRatio"),
            trend=valuation_metrics_data.get("psRatioTrend"),
            status=valuation_health["status"],
            color=valuation_health["color"]
        )

        # 4. Get overall fundamental state
        fundamental_state = get_fundamental_state(
            income_statements=income_statements_db,
            balance_sheets=balance_sheets_db,
            cash_flow_statements=cash_flow_statements_db,
            calculated_metrics=calculated_metrics
        )

        logger.debug(f"Income statements for historical data: {income_statements_db}")
        logger.debug(f"Cash flow statements for historical data: {cash_flow_statements_db}")

        # Extract historical data for sparklines (oldest to newest)
        historical_revenue = []
        historical_eps = []
        historical_free_cash_flow = []

        # Income statements are sorted descending, so reverse for chronological order
        for statement in reversed(income_statements_db):
            date = statement.get("date")
            revenue = statement.get("revenue")
            eps = statement.get("eps")
            if date and revenue is not None:
                historical_revenue.append({"date": date, "value": revenue})
            if date and eps is not None:
                historical_eps.append({"date": date, "value": eps})

        # Cash flow statements are sorted descending, so reverse for chronological order
        for statement in reversed(cash_flow_statements_db):
            date = statement.get("date")
            fcf = statement.get("freeCashFlow")
            if date and fcf is not None:
                historical_free_cash_flow.append({"date": date, "value": fcf})

        logger.debug(f"Historical Revenue: {historical_revenue}")
        logger.debug(f"Historical EPS: {historical_eps}")
        logger.debug(f"Historical Free Cash Flow: {historical_free_cash_flow}")

        # 5. Prepare payload and cache
        cache_payload = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "incomeStatements": income_statements_db,
            "balanceSheets": balance_sheets_db,
            "cashFlowStatements": cash_flow_statements_db,
            "calculatedMetrics": calculated_metrics,
            "fundamentalState": fundamental_state,
            "historicalRevenue": historical_revenue,
            "historicalEPS": historical_eps,
            "historicalFreeCashFlow": historical_free_cash_flow,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        set_cached_data(cache_key, cache_payload, ex=3600) # Cache for 1 hour

        logger.info(f"Fundamental Service: Processed and cached fundamental data for {symbol}.")
        return cache_payload

    except HTTPException as e:
        logger.error(f"Fundamental Service: HTTP Exception for {symbol}: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Fundamental Service: An unexpected error occurred for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing fundamental data: {e}")
