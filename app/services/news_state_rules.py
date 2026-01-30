# backend/app/services/news_state_rules.py
from typing import Dict, Any, List, Optional
import logging

from app.schemas.stock_state import NewsState

logger = logging.getLogger(__name__)

def get_news_state(news_data: List[Dict[str, Any]]) -> NewsState:
    """
    Processes raw news data to derive a NewsState object.
    """
    overall_sentiment_scores = {"positive": 0, "neutral": 0, "negative": 0, "unknown": 0}
    impact_levels = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
    significant_headlines: List[str] = []

    if not news_data:
        return NewsState(
            overall_sentiment="neutral",
            significant_headlines=[],
            overall_impact="unknown"
        )

    for event in news_data:
        sentiment = event.get("sentiment", "unknown").lower()
        if sentiment in overall_sentiment_scores:
            overall_sentiment_scores[sentiment] += 1
        
        impact_level = event.get("impact", {}).get("level", "unknown").lower()
        if impact_level in impact_levels:
            impact_levels[impact_level] += 1

        # Consider headlines with high impact or strong sentiment as significant
        if impact_level == "high" or event.get("confidence", 0) > 0.7:
            significant_headlines.append(event.get("headline", "No Headline"))

    # Determine overall sentiment
    overall_sentiment = max(overall_sentiment_scores, key=overall_sentiment_scores.get)
    if overall_sentiment_scores[overall_sentiment] == 0: # If all are zero
        overall_sentiment = "neutral"

    # Determine overall impact
    overall_impact = max(impact_levels, key=impact_levels.get)
    if impact_levels[overall_impact] == 0: # If all are zero
        overall_impact = "unknown"

    return NewsState(
        overall_sentiment=overall_sentiment,
        significant_headlines=list(set(significant_headlines)), # Remove duplicates
        overall_impact=overall_impact
    )
