# backend/app/api/endpoints/agent.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import logging

from app.services.ai_agent_service import analyze_stock_with_gemini

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/analyze") # Changed to GET, or could be POST with query params
async def analyze_stock(
    symbol: str = Query(..., description="Stock symbol to analyze"),
    timeframe: str = Query("1day", description="Timeframe for technical analysis (e.g., '1day', '1hour')")
):
    """
    Endpoint to receive stock symbol and timeframe, and return AI agent's analysis.
    The stock state is now calculated on the backend.
    """
    logger.info(f"Received request for AI analysis for symbol: {symbol}, timeframe: {timeframe}")
    
    analysis_result = await analyze_stock_with_gemini(symbol, timeframe)
    
    if analysis_result is None:
        raise HTTPException(status_code=500, detail="Failed to get analysis from AI agent.")
    
    return analysis_result