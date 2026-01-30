# backend/app/schemas/stock_state.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Re-using FundamentalStateItem from fundamental_state_rules
class FundamentalStateItem(BaseModel):
    status: str
    color: str

class FundamentalState(BaseModel):
    profitability: FundamentalStateItem
    growth: FundamentalStateItem
    cashflow: FundamentalStateItem
    balanceSheet: FundamentalStateItem
    valuationContext: FundamentalStateItem

class TechnicalState(BaseModel):
    overall_trend: str = "unknown"
    momentum_assessment: str = "unknown"
    volatility_assessment: str = "unknown"
    macd_status: str = "unknown" # e.g., "bullish_crossover", "bearish_crossover", "above_zero", "below_zero"
    rsi_status: str = "unknown" # e.g., "overbought", "oversold", "neutral"
    bollinger_status: str = "unknown" # e.g., "squeezing", "expanding", "walking_upper", "walking_lower"
    divergences: List[str] = Field(default_factory=list) # e.g., ["bullish_macd_divergence", "bearish_rsi_divergence"]

class NewsState(BaseModel):
    overall_sentiment: str = "neutral" # e.g., "positive", "neutral", "negative"
    significant_headlines: List[str] = Field(default_factory=list)
    overall_impact: str = "unknown" # e.g., "high", "medium", "low"

class StockState(BaseModel):
    symbol: str
    timeframe: str = "1day" # Default to 1day
    technical_state: TechnicalState = Field(default_factory=TechnicalState)
    fundamental_state: FundamentalState
    news_state: NewsState = Field(default_factory=NewsState)
