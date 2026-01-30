import os
from dotenv import load_dotenv

load_dotenv()

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")
TWELVE_DATA_API_URL = "https://api.twelvedata.com"
TAVILY_API_URL = "https://api.tavily.com/search"
FMP_API_URL = "https://financialmodelingprep.com/stable"
SQLITE_DB_FILE = "./app/database/test.db" # Using a relative path for simplicity, adjust as needed

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD=os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

CORS_ORIGINS = [
    "http://localhost:3000",
    "https://monodara.github.io",
]

MARKET_ETFS = {
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "DIA": "Dow Jones ETF",
    "IWM": "Russell 2000 ETF"
}
