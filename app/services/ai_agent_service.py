# backend/app/services/ai_agent_service.py
import logging
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.config.settings import GEMINI_API_KEY
from app.services.gemini_formatter import client
from app.services.stock_state_service import get_stock_state_for_analysis
from app.cache.redis_cache import get_cached_data, set_cached_data # Import caching utilities

logger = logging.getLogger(__name__)

async def analyze_stock_with_gemini(symbol: str, timeframe: str = "1day") -> Optional[Dict[str, Any]]:
    """
    Analyzes the stock state using the Gemini AI model and returns a structured analysis.
    The stock state is now calculated on the backend.
    """
    if not client:
        logger.error("Gemini client is not configured, cannot analyze stock.")
        return None

    cache_key = f"ai_analysis:{symbol}:{timeframe}"
    cached_analysis = get_cached_data(cache_key)
    if cached_analysis:
        logger.info(f"AI Agent Service: Cache hit for {symbol}-{timeframe}.")
        return cached_analysis

    logger.info(f"AI Agent Service: Cache miss for {symbol}-{timeframe}. Generating new analysis.")

    # Get the complete stock state from the new service
    stock_state = await get_stock_state_for_analysis(symbol, timeframe)

    # Define the expected response schema for the AI agent's analysis
    AGENT_ANALYSIS_SCHEMA = {
        "type": "OBJECT",
        "properties": {
            "overall_bias": {
                "type": "STRING",
                "enum": ["Bullish", "Bearish", "Neutral", "Bullish (Cautious)", "Bearish (Cautious)"]
            },
            "technical_summary": {"type": "STRING"},
            "fundamental_summary": {"type": "STRING"},
            "risk_factors": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["overall_bias", "technical_summary", "fundamental_summary", "risk_factors"]
    }

    # Construct a detailed prompt for the Gemini model
    user_content: List[Any] = [
        "You are an expert financial analyst AI. Your task is to analyze the provided stock's state across technical, fundamental, and news aspects, and generate a concise, structured analysis.",
        f"Here is the stock's current state:\n{stock_state.model_dump_json(indent=2)}",
        "Based on this information, provide an analysis in the following JSON format:"
    ]

    try:
        logger.info(f"Invoking Gemini for stock analysis: {stock_state.symbol}")
        logger.debug(f"Prompt sent to Gemini: {user_content}")
        
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash", 
            contents=user_content,
            config={
                "response_mime_type": "application/json",
                "response_schema": AGENT_ANALYSIS_SCHEMA,
            }
        )
        
        analysis = response.parsed
        
        if analysis:
            if isinstance(analysis, BaseModel):
                analysis_dict = analysis.model_dump()
            elif isinstance(analysis, dict):
                analysis_dict = analysis
            else:
                logger.warning(f"Gemini returned unexpected analysis type for {stock_state.symbol}: {type(analysis)}")
                return None
            
            set_cached_data(cache_key, analysis_dict, ex=3600) # Cache for 1 hour
            logger.info(f"AI Agent Service: Cached analysis for {symbol}-{timeframe}.")
            return analysis_dict
        else:
            logger.warning(f"Gemini returned no parsed analysis for {stock_state.symbol}. Raw text: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error analyzing stock with Gemini for {stock_state.symbol}: {e}")
        return None
