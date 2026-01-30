# backend/app/services/ai_chat_service.py
import logging
import json # Re-add import json
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from google import genai
from pydantic import BaseModel, Field

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool # Decorator for creating tools
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage # Added for clarity in prompt

from app.config.settings import GEMINI_API_KEY
from app.services.gemini_formatter import client # Re-use the Gemini client
from app.services.stock_state_service import get_stock_state_for_analysis
from app.services.ai_agent_service import analyze_stock_with_gemini
from app.services.price_service import search_stock_service # <--- NEW IMPORT

logger = logging.getLogger(__name__)

# Initialize Gemini client (re-using the one from gemini_formatter)
# This client is used for direct genai calls, but LangChain will use ChatGoogleGenerativeAI
# gemini_client = client # No longer directly used for chat orchestration

# --- Define LangChain Tools ---

@tool
async def get_stock_state_tool(symbol: str, timeframe: str = "1day") -> Dict[str, Any]:
    """
    Fetches the comprehensive stock state (technical, fundamental, news) for a given symbol and timeframe.
    Use this tool to gather all necessary information about a stock before performing an AI analysis or answering detailed questions about its current state.
    """
    logger.info(f"LangChain Tool: Calling get_stock_state_for_analysis for {symbol} ({timeframe})")
    try:
        stock_state = await get_stock_state_for_analysis(symbol, timeframe)
        return stock_state.model_dump() # Convert Pydantic model to dict
    except Exception as e:
        logger.error(f"Error in get_stock_state_tool for {symbol}: {e}")
        return {"error": str(e)}

@tool
async def perform_ai_analysis_tool(symbol: str, timeframe: str = "1day") -> Optional[Dict[str, Any]]:
    """
    Performs a comprehensive AI analysis of a stock based on its symbol and timeframe.
    This tool leverages the AI agent to provide an overall bias, technical summary,
    fundamental summary, and risk factors. Use this when the user explicitly asks for an "analysis" or "opinion" on a stock.
    """
    logger.info(f"LangChain Tool: Calling analyze_stock_with_gemini for {symbol} ({timeframe})")
    try:
        analysis = await analyze_stock_with_gemini(symbol, timeframe)
        return analysis
    except Exception as e:
        logger.error(f"Error in perform_ai_analysis_tool for {symbol}: {e}")
        return {"error": str(e)}

@tool # <--- NEW TOOL
async def search_stock_symbol_tool(company_or_symbol: str) -> Optional[str]: # Changed return type
    """
    Searches for stock symbols based on a keyword (company name or partial symbol).
    Use this tool when the user mentions a company name and you need to find its stock symbol.
    Returns the most relevant stock symbol found, or None if no clear symbol is identified.
    """
    logger.info(f"LangChain Tool: Searching for stock symbol with keyword: {company_or_symbol}")
    try:
        results = await search_stock_service(company_or_symbol) # <--- ADDED AWAIT
        if results and results.get("data"):
            # Assuming the first result is the most relevant
            first_result = results["data"][0]
            symbol = first_result.get("symbol")
            if symbol:
                logger.info(f"Found symbol {symbol} for keyword {company_or_symbol}")
                return symbol
        logger.info(f"No clear symbol found for keyword {company_or_symbol}")
        return None # No clear symbol found
    except Exception as e:
        logger.error(f"Error in search_stock_symbol_tool for keyword {company_or_symbol}: {e}")
        return None # Return None on error

# List of all tools available to the agent
tools = [get_stock_state_tool, perform_ai_analysis_tool, search_stock_symbol_tool] # <--- UPDATED TOOLS LIST

# --- LangChain Model and Agent Setup ---

# Initialize the ChatGoogleGenerativeAI model
# Ensure GEMINI_API_KEY is set in your environment
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=GEMINI_API_KEY) # Changed model to gemini-3-flash-preview

# Define the prompt template for the agent
prompt = f'''
         "You are a helpful AI assistant specializing in stock market analysis. "
            "You can fetch stock data, search for stock symbols, and perform AI analysis. " # <--- UPDATED PROMPT
            "Always try to use the available tools to answer questions about specific stocks. "
            "If a user asks for an analysis, use the 'perform_ai_analysis_tool'. "
            "If a user asks for detailed information about a stock's state (technical, fundamental, news), use 'get_stock_state_tool'. "
            "If the user mentions a company name and you need to find its stock symbol, use the 'search_stock_symbol_tool'. "
            "Do not give financial advice. State that you are an AI analyst and cannot provide buy/sell recommendations."
    '''

# Create the agent
agent = create_agent(llm, tools, system_prompt=prompt, checkpointer=InMemorySaver()) # Removed extra comma


async def handle_chat_message(user_message: str, session_id: str = "default_session") -> str: # Modified signature
    """
    Handles a user's chat message using a LangChain agent with Gemini,
    including function calling and conversation memory.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key is not configured.")

    try:
        # Invoke the agent with the current input and memory
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=user_message)]}, # Only pass the current user message
            {"configurable": {"thread_id": session_id}}, # Use session_id for memory
        )
        
        ai_response_message = response["messages"][-1]
        
        # Ensure the final response content is a string
        if isinstance(ai_response_message, AIMessage):
            if isinstance(ai_response_message.content, str):
                ai_response_text = ai_response_message.content
            elif isinstance(ai_response_message.content, dict) or isinstance(ai_response_message.content, list):
                # If the content is a structured object (e.g., tool output), convert it to a readable string
                ai_response_text = json.dumps(ai_response_message.content, indent=2)
            else:
                ai_response_text = str(ai_response_message.content)
        else:
            # If the last message is not an AIMessage (e.g., FunctionMessage), convert it to string
            ai_response_text = str(ai_response_message)

        return ai_response_text

    except Exception as e:
        logger.error(f"Error in LangChain agent chat session: {e}")
        return "I'm sorry, I encountered an error trying to respond."
