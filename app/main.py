import uvicorn
import logging # Import logging module
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import api_router
from app.database.connection import create_stock_price_table, close_db_connection
from app.config.settings import CORS_ORIGINS

# Configure logging
logging.basicConfig(level=logging.DEBUG) # Set root logger level to DEBUG

app = FastAPI(
    title="MSignalAI Backend",
    description="API for MSignalAI to fetch stock data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    await create_stock_price_table()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_connection()

@app.get("/")
def read_root():
    """
    Root endpoint to welcome users to the API.
    """
    return {"message": "Welcome to the MSignalAI API"}

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)