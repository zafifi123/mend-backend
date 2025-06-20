import yfinance as yf
import time
from threading import Lock

# Simple in-memory cache with a lock for thread safety
yf_cache = {}
CACHE_DURATION_SECONDS = 60  # Cache data for 60 seconds
cache_lock = Lock()

def get_tickers_info(symbols: list):
    """
    Fetches ticker information from yfinance, using a time-based cache
    to avoid excessive API calls.
    """
    if not symbols:
        return {}

    symbols_to_fetch = []
    cached_tickers = {}
    current_time = time.time()

    with cache_lock:
        # First, find which symbols are in cache and are still valid
        for symbol in symbols:
            if symbol in yf_cache:
                entry_time, data = yf_cache[symbol]
                if current_time - entry_time < CACHE_DURATION_SECONDS:
                    cached_tickers[symbol] = data
                else:
                    symbols_to_fetch.append(symbol)
            else:
                symbols_to_fetch.append(symbol)

    # Fetch new data for symbols that were not in cache or expired
    if symbols_to_fetch:
        retries = 3
        for attempt in range(retries):
            try:
                new_tickers_data = yf.Tickers(' '.join(symbols_to_fetch))
                with cache_lock:
                    for symbol in symbols_to_fetch:
                        ticker_info = new_tickers_data.tickers[symbol].info
                        if ticker_info and ticker_info.get("regularMarketPrice") is not None:
                             yf_cache[symbol] = (time.time(), ticker_info)
                             cached_tickers[symbol] = ticker_info
                        else:
                            cached_tickers[symbol] = yf_cache.get(symbol, ({},))[1] # Use old cache if new fetch fails
                break  # Success, exit retry loop
            except Exception as e:
                print(f"yfinance batch call failed on attempt {attempt + 1}/{retries}: {e}")
                if attempt < retries - 1:
                    time.sleep(1 + attempt)  # Wait longer on each retry
                else:
                    # On last failed attempt, fill with empty dicts
                    with cache_lock:
                        for symbol in symbols_to_fetch:
                            if symbol not in cached_tickers:
                                cached_tickers[symbol] = {}
    return cached_tickers 