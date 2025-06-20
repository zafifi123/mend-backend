import requests
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Hardcoded top 100 stocks (example subset, expand as needed)
TOP_100_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'BRK.B', 'JPM', 'V',
    # ... add up to 100 symbols ...
]

LLAMA_API_URL = "http://localhost:11434/api/generate"
NEWS_API_URL = "http://localhost:8000/api/news"
FINANCIALS_API_URL = "http://localhost:8000/api/financials"
PERFORMANCE_API_URL = "http://localhost:8000/api/market/performance"
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

def get_news_for_symbol(symbol):
    try:
        response = requests.get(f"{NEWS_API_URL}/{symbol}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news for {symbol}: {e}")
        return None

def get_financials_for_symbol(symbol):
    try:
        response = requests.get(f"{FINANCIALS_API_URL}/{symbol}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching financials for {symbol}: {e}")
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
    try:
        response = requests.get(f"{PERFORMANCE_API_URL}/{symbol}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching performance for {symbol}: {e}")
        return None

def get_llama_recommendation(symbol, news_articles, financials, performance, general_news):
    news_summary = "\n".join([f"- {article['title']}" for article in news_articles]) if news_articles else "No recent news available."
    
    general_news_summary = "\n".join([f"- {article['title']}" for article in general_news]) if general_news else "No recent general news available."

    financials_summary = "No recent financial data available."
    if financials and financials.get(symbol):
        # Assuming the structure of the financials response
        financials_summary = f"Price: {financials.get(symbol, {}).get('regularMarketPrice', 'N/A')}, "
        financials_summary += f"Change: {financials.get(symbol, {}).get('regularMarketChange', 'N/A')}, "
        financials_summary += f"Volume: {financials.get(symbol, {}).get('regularMarketVolume', 'N/A')}"

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

def main():
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