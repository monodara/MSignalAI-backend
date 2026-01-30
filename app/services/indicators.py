# backend/app/services/indicators.py
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()



