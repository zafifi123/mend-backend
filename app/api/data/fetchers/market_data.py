import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from api.core.config import ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_BASE_URL

def get_price_data(symbol: str, interval: str = "1d", lookback_days: int = 30):
    """
    Fetch historical price data from Alpha Vantage
    """
    # Map interval to Alpha Vantage function
    interval_map = {
        "1d": "TIME_SERIES_DAILY",
        "1wk": "TIME_SERIES_WEEKLY",
        "1mo": "TIME_SERIES_MONTHLY"
    }
    
    function = interval_map.get(interval, "TIME_SERIES_DAILY")
    
    params = {
        'function': function,
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY,
        'outputsize': 'compact'  # Use compact for faster response
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract time series data
        time_series_key = None
        for key in data.keys():
            if 'Time Series' in key:
                time_series_key = key
                break
        
        if not time_series_key or time_series_key not in data:
            return []
        
        time_series = data[time_series_key]
        
        # Convert to list of records
        records = []
        for date, values in time_series.items():
            records.append({
                'Date': date,
                'Open': float(values.get('1. open', 0)),
                'High': float(values.get('2. high', 0)),
                'Low': float(values.get('3. low', 0)),
                'Close': float(values.get('4. close', 0)),
                'Volume': int(values.get('5. volume', 0))
            })
        
        # Sort by date and limit to lookback_days
        records.sort(key=lambda x: x['Date'], reverse=True)
        records = records[:lookback_days]
        
        return records
        
    except Exception as e:
        print(f"Alpha Vantage historical data failed for {symbol}: {e}")
        return []
