# backend/app/schemas/chat.py
from pydantic import BaseModel
from typing import List, Dict

class ChatMessage(BaseModel):
    sender: str
    text: str

class ChatRequest(BaseModel):
    user_message: str
    chat_history: List[ChatMessage] = []
