import requests
import time
from threading import Lock
from .config import ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_BASE_URL, CACHE_DURATION_SECONDS, USE_MOCK_DATA
import os
from .mock_data import get_mock_stock_quote, get_mock_company_overview

# Simple in-memory cache with a lock for thread safety
av_cache = {}
cache_lock = Lock()

def get_stock_quote(symbol: str):
    """
    Fetch real-time stock quote from Alpha Vantage or return mock data.
    """
    if USE_MOCK_DATA:
        return get_mock_stock_quote(symbol)

    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            return {
                'symbol': quote.get('01. symbol', symbol),
                'regularMarketPrice': float(quote.get('05. price', 0)),
                'regularMarketChange': float(quote.get('09. change', 0)),
                'regularMarketChangePercent': float(quote.get('10. change percent', '0').replace('%', '')),
                'regularMarketVolume': int(quote.get('06. volume', 0)),
                'shortName': symbol,  # Alpha Vantage doesn't provide company name in quote
                'previousClose': float(quote.get('08. previous close', 0)),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0))
            }
        return None
    except Exception as e:
        print(f"Alpha Vantage API call failed for {symbol}: {e}")
        return None

def get_company_overview(symbol: str):
    """
    Fetch company overview from Alpha Vantage or return mock data.
    """
    if USE_MOCK_DATA:
        return get_mock_company_overview(symbol)

    params = {
        'function': 'OVERVIEW',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and 'Symbol' in data:
            return {
                'symbol': data.get('Symbol', symbol),
                'shortName': data.get('Name', symbol),
                'sector': data.get('Sector', ''),
                'industry': data.get('Industry', ''),
                'marketCap': data.get('MarketCapitalization', ''),
                'description': data.get('Description', '')
            }
        return None
    except Exception as e:
        print(f"Alpha Vantage company overview failed for {symbol}: {e}")
        return None

def get_tickers_info(symbols: list):
    """
    Fetches ticker information from Alpha Vantage, using a time-based cache
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
            if symbol in av_cache:
                entry_time, data = av_cache[symbol]
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
                with cache_lock:
                    for symbol in symbols_to_fetch:
                        # Get quote data
                        quote_data = get_stock_quote(symbol)
                        if quote_data:
                            # Get company overview for additional info
                            overview_data = get_company_overview(symbol)
                            if overview_data:
                                # Merge quote and overview data
                                ticker_info = {**quote_data, **overview_data}
                            else:
                                ticker_info = quote_data
                            
                            av_cache[symbol] = (time.time(), ticker_info)
                            cached_tickers[symbol] = ticker_info
                        else:
                            # Use old cache if new fetch fails
                            cached_tickers[symbol] = av_cache.get(symbol, ({},))[1]
                
                break  # Success, exit retry loop
            except Exception as e:
                print(f"Alpha Vantage batch call failed on attempt {attempt + 1}/{retries}: {e}")
                if attempt < retries - 1:
                    time.sleep(1 + attempt)  # Wait longer on each retry
                else:
                    # On last failed attempt, fill with empty dicts
                    with cache_lock:
                        for symbol in symbols_to_fetch:
                            if symbol not in cached_tickers:
                                cached_tickers[symbol] = {}
    return cached_tickers 