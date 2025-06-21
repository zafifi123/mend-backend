import requests
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import random

# -- MOCK DATA SWITCH --
# Set to True to use mock data instead of calling the real Alpha Vantage API
USE_MOCK_DATA = True

# Mock Data Generation (self-contained for the worker)
def get_mock_financials(symbol: str):
    base_price = random.uniform(100, 500)
    change = random.uniform(-5, 5)
    quote = {
        'symbol': symbol,
        'regularMarketPrice': round(base_price, 2),
        'regularMarketChange': round(change, 2),
        'regularMarketChangePercent': round((change / base_price) * 100, 2),
        'regularMarketVolume': random.randint(1_000_000, 100_000_000),
    }
    overview = {
        'shortName': f"{symbol} MockCorp",
        'sector': random.choice(['Technology', 'Healthcare', 'Financials']),
        'marketCap': f"{random.randint(100, 3000)}B",
    }
    return {symbol: {**quote, **overview}}

def get_mock_performance(symbol: str):
    return {
        "3M": round(random.uniform(-15, 20), 2),
        "6M": round(random.uniform(-25, 30), 2),
        "1Y": round(random.uniform(-30, 50), 2)
    }

# Alpha Vantage API Configuration
ALPHA_VANTAGE_API_KEY = 'FTGFCC0SFOR6VT65'
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'

# Hardcoded top 100 stocks (example subset, expand as needed)
TOP_100_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'BRK.B', 'JPM', 'V',
    # ... add up to 100 symbols ...
]

LLAMA_API_URL = "http://localhost:11434/api/generate"
NEWS_API_URL = "http://localhost:8000/api/news"
LLAMA_MODEL = "llama3"

# Use the same DB connection logic as your API
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'mend_db')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASS = os.getenv('DB_PASS', 'password')

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def get_stock_quote_alpha_vantage(symbol: str):
    """
    Fetch real-time stock quote from Alpha Vantage
    """
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }
    
    try:
        print(f"Fetching quote for {symbol}...")
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Quote response for {symbol}: {data}")
        
        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            result = {
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
            print(f"Quote data for {symbol}: {result}")
            return result
        else:
            print(f"No quote data found for {symbol}")
            return None
    except Exception as e:
        print(f"Alpha Vantage API call failed for {symbol}: {e}")
        return None

def get_company_overview_alpha_vantage(symbol: str):
    """
    Fetch company overview from Alpha Vantage
    """
    params = {
        'function': 'OVERVIEW',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }
    
    try:
        print(f"Fetching overview for {symbol}...")
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Overview response for {symbol}: {data}")
        
        if data and 'Symbol' in data:
            result = {
                'symbol': data.get('Symbol', symbol),
                'shortName': data.get('Name', symbol),
                'sector': data.get('Sector', ''),
                'industry': data.get('Industry', ''),
                'marketCap': data.get('MarketCapitalization', ''),
                'description': data.get('Description', '')
            }
            print(f"Overview data for {symbol}: {result}")
            return result
        else:
            print(f"No overview data found for {symbol}")
            return None
    except Exception as e:
        print(f"Alpha Vantage company overview failed for {symbol}: {e}")
        return None

def get_performance_alpha_vantage(symbol: str):
    """
    Get performance data for different time periods using Alpha Vantage
    """
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY,
        'outputsize': 'compact'  # Use compact for faster response
    }
    
    try:
        print(f"Fetching performance for {symbol}...")
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Performance response keys for {symbol}: {list(data.keys())}")
        
        # Extract time series data
        time_series_key = None
        for key in data.keys():
            if 'Time Series' in key:
                time_series_key = key
                break
        
        if not time_series_key or time_series_key not in data:
            print(f"No time series data found for {symbol}")
            return {"error": "Could not retrieve historical data."}
        
        time_series = data[time_series_key]
        print(f"Time series data points for {symbol}: {len(time_series)}")
        
        # Convert to sorted list of (date, close_price) tuples
        price_data = []
        for date, values in time_series.items():
            try:
                close_price = float(values.get('4. close', 0))
                price_data.append((date, close_price))
            except (ValueError, TypeError):
                continue
        
        if not price_data:
            print(f"No valid price data found for {symbol}")
            return {"error": "No valid price data found."}
        
        # Sort by date (newest first)
        price_data.sort(key=lambda x: x[0], reverse=True)
        
        # Get current price (most recent)
        current_price = price_data[0][1]
        
        # Calculate performance for different periods
        performance = {}
        today = datetime.now()
        
        periods = {
            "3M": today - timedelta(days=90),
            "6M": today - timedelta(days=180),
            "1Y": today - timedelta(days=365)
        }
        
        for period, start_date in periods.items():
            # Find the closest available date in history
            target_date = start_date.strftime('%Y-%m-%d')
            
            # Find the closest date in our data
            past_price = None
            for date, price in price_data:
                if date <= target_date:
                    past_price = price
                    break
            
            if past_price and past_price != 0:
                change_percent = ((current_price - past_price) / past_price) * 100
                performance[period] = round(change_percent, 2)
            else:
                performance[period] = "N/A"
        
        print(f"Performance data for {symbol}: {performance}")
        return performance
        
    except Exception as e:
        print(f"Could not retrieve performance data for {symbol}: {e}")
        return {"error": str(e)}

def get_news_for_symbol(symbol):
    try:
        response = requests.get(f"{NEWS_API_URL}/{symbol}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news for {symbol}: {e}")
        return None

def get_financials_for_symbol(symbol):
    """
    Get financial data directly from Alpha Vantage or return mock data.
    """
    if USE_MOCK_DATA:
        print(f"Using MOCK financial data for {symbol}")
        return get_mock_financials(symbol)

    print(f"\n=== Getting REAL financials for {symbol} ===")
    quote_data = get_stock_quote_alpha_vantage(symbol)
    overview_data = get_company_overview_alpha_vantage(symbol)
    
    if quote_data and overview_data:
        # Merge quote and overview data
        result = {symbol: {**quote_data, **overview_data}}
        print(f"Combined financial data for {symbol}: {result}")
        return result
    elif quote_data:
        result = {symbol: quote_data}
        print(f"Quote-only financial data for {symbol}: {result}")
        return result
    else:
        print(f"No financial data available for {symbol}")
        return None

def get_general_news():
    try:
        response = requests.get(f"{NEWS_API_URL}/general")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching general news: {e}")
        return None

def get_performance_for_symbol(symbol):
    """
    Get performance data directly from Alpha Vantage or return mock data.
    """
    if USE_MOCK_DATA:
        print(f"Using MOCK performance data for {symbol}")
        return get_mock_performance(symbol)

    print(f"\n=== Getting REAL performance for {symbol} ===")
    return get_performance_alpha_vantage(symbol)

def get_llama_recommendation(symbol, news_articles, financials, performance, general_news):
    news_summary = "\n".join([f"- {article['title']}" for article in news_articles]) if news_articles else "No recent news available."
    
    general_news_summary = "\n".join([f"- {article['title']}" for article in general_news]) if general_news else "No recent general news available."

    financials_summary = "No recent financial data available."
    if financials and financials.get(symbol):
        # Assuming the structure of the financials response
        financials_summary = f"Price: {financials.get(symbol, {}).get('regularMarketPrice', 'N/A')}, "
        financials_summary += f"Change: {financials.get(symbol, {}).get('regularMarketChange', 'N/A')}, "
        financials_summary += f"Sector: {financials.get(symbol, {}).get('sector', 'N/A')}, "
        financials_summary += f"Market Cap: {financials.get(symbol, {}).get('marketCap', 'N/A')}"

    performance_summary = "No performance data available."
    if performance and not performance.get("error"):
        performance_summary = f"3M: {performance.get('3M', 'N/A')}%, 6M: {performance.get('6M', 'N/A')}%, 1Y: {performance.get('1Y', 'N/A')}%"

    prompt = f"""
    Given the following general news:
    {general_news_summary}

    And the following recent news for {symbol}:
    {news_summary}

    And the following financial data for {symbol}:
    {financials_summary}

    And the following performance data for {symbol}:
    {performance_summary}

    Give a trading recommendation for {symbol}.
    Respond in JSON with the following fields:
    symbol, action (BUY/SELL/HOLD), confidence (0-1), reasoning, risk_level (low/medium/high),
    timeframe (short/medium/long), price_target, stop_loss, llama_confidence (0-1). Respond only with valid JSON. Do not write an introduction or summary.
    """
    response = requests.post(
        LLAMA_API_URL,
        headers={"Content-Type": "application/json"},
        json={
            "model": LLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 150,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "stop": ["\n\n", "User:", "Human:", "Assistant:"]
            }
        }
    )
    response.raise_for_status()
    # Llama may return a string, so parse JSON from the response
    import json
    try:
        data = json.loads(response.json()["response"])
    except Exception as e:
        return None
    return data

def insert_recommendation(rec):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO recommendations (
                    symbol, action, confidence, reasoning, risk_level, timeframe,
                    price_target, stop_loss, ml_confidence, llama_confidence, consensus_score, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                rec["symbol"],
                rec["action"],
                rec["confidence"],
                rec["reasoning"],
                rec["risk_level"],
                rec["timeframe"],
                rec["price_target"],
                rec["stop_loss"],
                0.0,  
                rec["llama_confidence"],
                rec["confidence"], 
                datetime.now()
            ))
        conn.commit()

def test_alpha_vantage():
    """
    Test Alpha Vantage API connectivity. Skips test if using mock data.
    """
    if USE_MOCK_DATA:
        print("=== MOCK DATA is ON. Skipping real Alpha Vantage API test. ===")
        return

    print("=== Testing Alpha Vantage API ===")
    print(f"API Key: {ALPHA_VANTAGE_API_KEY}")
    print(f"Base URL: {ALPHA_VANTAGE_BASE_URL}")
    
    # Test with a simple stock
    test_symbol = "AAPL"
    
    print(f"\nTesting quote for {test_symbol}...")
    quote = get_stock_quote_alpha_vantage(test_symbol)
    if quote:
        print(f"✅ Quote test passed: {quote}")
    else:
        print("❌ Quote test failed")
    
    print(f"\nTesting overview for {test_symbol}...")
    overview = get_company_overview_alpha_vantage(test_symbol)
    if overview:
        print(f"✅ Overview test passed: {overview}")
    else:
        print("❌ Overview test failed")
    
    print(f"\nTesting performance for {test_symbol}...")
    performance = get_performance_alpha_vantage(test_symbol)
    if performance and not performance.get("error"):
        print(f"✅ Performance test passed: {performance}")
    else:
        print(f"❌ Performance test failed: {performance}")

def main():
    # Test Alpha Vantage first
    test_alpha_vantage()
    
    print("\n=== Starting main worker process ===")
    general_news = get_general_news()
    for symbol in TOP_100_STOCKS:
        print(f"Processing {symbol}...")
        news = get_news_for_symbol(symbol)
        financials = get_financials_for_symbol(symbol)
        performance = get_performance_for_symbol(symbol)
        if not news:
            print(f"Skipping {symbol} due to news fetch error.")
            continue
        rec = get_llama_recommendation(symbol, news, financials, performance, general_news)
        print(rec)
        if rec:
            insert_recommendation(rec)
            print(f"Inserted recommendation for {symbol}")
        else:
            print(f"No recommendation for {symbol}")
        time.sleep(1)  # Be nice to the API

if __name__ == "__main__":
    main() 