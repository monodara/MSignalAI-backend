from fastapi import APIRouter
from app.api.endpoints import stock, market, agent, chat # Import chat router

api_router = APIRouter()
api_router.include_router(stock.router, tags=["stock"])
api_router.include_router(market.router, tags=["market"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"]) # Include chat router