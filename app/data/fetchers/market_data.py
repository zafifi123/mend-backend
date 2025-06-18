import yfinance as yf
from datetime import datetime, timedelta

def get_price_data(symbol: str, interval: str = "1d", lookback_days: int = 30):
    ticker = yf.Ticker(symbol)
    end = datetime.now()
    start = end - timedelta(days=lookback_days)
    df = ticker.history(interval=interval, start=start, end=end)
    return df.reset_index().to_dict(orient="records")
