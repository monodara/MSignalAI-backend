# backend/app/services/utils.py
import pandas as pd
import numpy as np
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_data_length(data: list, min_length: int, indicator_name: str) -> bool:
    """
    Validates if the data has the minimum required length for a calculation.
    """
    if len(data) < min_length:
        logger.warning(f"{indicator_name}: Insufficient data. Need {min_length}, got {len(data)}.")
        return False
    return True

def clean_series_data(series: pd.Series) -> List[Optional[float]]:
    """
    Cleans a pandas Series by replacing NaN, inf, and NA values with None.
    """
    return series.replace({pd.NA: None, np.nan: None, np.inf: None, -np.inf: None}).tolist()
