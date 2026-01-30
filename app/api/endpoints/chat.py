# backend/app/api/endpoints/chat.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
import logging

from app.services.ai_chat_service import handle_chat_message # Will create this service
# from app.schemas.chat import ChatRequest # No longer needed

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/send_message") # Keep as POST for potential future body content
async def send_message(
    user_message: str = Query(..., description="The user's message to the AI agent."),
    session_id: str = Query("default_session", description="Unique identifier for the chat session.")
) -> Dict[str, Any]:
    """
    Receives a user message and returns an AI agent's response.
    """
    logger.info(f"Received user message for session {session_id}: {user_message}")
    
    try:
        ai_response = await handle_chat_message(user_message, session_id)
        return {"response": ai_response}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error handling chat message for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing your message.")