# backend/app/services/gemini_formatter.py
import json
import logging
from typing import List, Dict, Any
import uuid
from google import genai
from pydantic import BaseModel

from app.config.settings import GEMINI_API_KEY

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

EVENT_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            # 基础分类
            "type": {
                "type": "STRING", 
                "enum": ["earnings", "company_event", "macro", "sector", "regulatory", "sentiment", "unknown"]
            },
            "headline": {"type": "STRING"},
            "summary": {"type": "STRING"},
            
            # 情感与信心
            "sentiment": {"type": "STRING", "enum": ["positive", "neutral", "negative", "unknown"]},
            "confidence": {"type": "NUMBER"}, # 0.0 到 1.0 之间
            
            # 影响评估
            "impact": {
                "type": "OBJECT",
                "properties": {
                    "level": {"type": "STRING", "enum": ["low", "medium", "high", "unknown"]},
                    "reason": {"type": "STRING"}
                },
                "required": ["level", "reason"]
            },
            "time_horizon": {"type": "STRING", "enum": ["immediate", "short", "mid", "long", "unknown"]},
            "directional_bias": {"type": "STRING", "enum": ["bullish", "bearish", "mixed", "unknown"]},
            
            # 价格风险 (金融建模核心)
            "price_relevance": {
                "type": "OBJECT",
                "properties": {
                    "gap_risk": {"type": "BOOLEAN"},
                    "volatility_risk": {"type": "STRING", "enum": ["low", "medium", "high", "unknown"]},
                    "trend_risk": {"type": "STRING", "enum": ["continuation", "reversal", "unclear", "unknown"]}
                },
                "required": ["gap_risk", "volatility_risk", "trend_risk"]
            },
            
            # 标签
            "tags": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        # 只要求 AI 必须生成它能从文字中推断出的东西
        "required": [
            "type", "headline", "summary", "sentiment", "confidence", 
            "impact", "time_horizon", "directional_bias", "price_relevance"
        ]
    }
}

async def format_news_with_gemini(raw_news_article_content: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
    """
    Formats a single raw news article (as a string) into a structured Event schema using Gemini LLM.
    """
    if not client:
        logger.error("Gemini API key is not configured.")
        return []

    if not raw_news_article_content:
        return []

    articles_input = "\n---\n".join([
        f"Article Index: {i}\nTitle: {a['title']}\nContent: {a['content']}"
        for i, a in enumerate(raw_news_article_content)
    ])
    user_content: List[Any] = [
        f"Stock Symbol: {symbol}",
        "Please analyze the following news articles individually and return an array of event objects:",
        articles_input
    ]

    try:
        logger.info(f"Invoking Gemini for symbol {symbol} with a single article.")
        
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_content,
            config={
                "system_instruction": "You are a financial analyst. Analyze each provided article and extract stock-related events into a JSON array.",
                "response_mime_type": "application/json",
                "response_schema": EVENT_SCHEMA,
            }
        )
        
        raw_output = response.parsed if response.parsed is not None else json.loads(response.text or "[]")
        
        # 类型窄化与数据补全
        events = raw_output if isinstance(raw_output, list) else [raw_output]
        
        # 此时在 Python 层注入 ID 和 Source 信息，比让 AI 生成更可靠
        final_output = []
        for i, item in enumerate(events):
          if isinstance(item, BaseModel):
              event_dict = item.model_dump()
          
          elif isinstance(item, dict):
              event_dict = item.copy()
              
          else:
              logger.warning(f"Unexpected item type: {type(item)}")
              continue

          # 注入元数据 (来自原始的 raw_news_article_content 列表)
          if i < len(raw_news_article_content):
              event_dict["id"] = str(uuid.uuid4())
              event_dict["timestamp"] = raw_news_article_content[i].get("published_at")
              event_dict["raw_sources"] = [{
                  "source": raw_news_article_content[i].get("source"),
                  "url": raw_news_article_content[i].get("url"),
                  "published_at": raw_news_article_content[i].get("published_at")
              }]
    
          final_output.append(event_dict)
        
        return final_output

    except json.JSONDecodeError as je:
        logger.error(f"Gemini returned invalid JSON for article: {je}")
        return []
    except Exception as e:
        logger.error(f"Gemini formatting error for article: {str(e)}")
        return []