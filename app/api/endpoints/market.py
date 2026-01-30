from fastapi import APIRouter
from app.services.price_service import search_stock_service, get_market_etfs_service

router = APIRouter()

@router.get("/search_stock")
async def search_stock(keyword: str):
    return await search_stock_service(keyword)

@router.get("/market_etfs")
async def get_market_etfs():
    return await get_market_etfs_service()