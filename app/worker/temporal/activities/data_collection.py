import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
from temporalio import activity

@activity.defn
async def collect_market_data() -> Dict[str, Any]:
    """Collect comprehensive market data for analysis."""
    
    # List of stocks to analyze (you can expand this)
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
        'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'V', 'PYPL', 'ADBE', 'CRM'
    ]
    
    market_data = {}
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period="30d", interval="1d")
            
            # Get current info
            info = ticker.info
            
            # Calculate technical indicators
            technical_data = calculate_technical_indicators(hist)
            
            # Get recent news
            news_data = get_recent_news(symbol)
            
            market_data[symbol] = {
                'symbol': symbol,
                'current_price': info.get('regularMarketPrice', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'beta': info.get('beta', 0),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'technical_indicators': technical_data,
                'news_sentiment': analyze_news_sentiment(news_data),
                'historical_data': hist.to_dict('records')[-10:],  # Last 10 days
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error collecting data for {symbol}: {e}")
            continue
    
    return market_data

def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate technical indicators for a stock."""
    if df.empty:
        return {}
    
    # Simple Moving Averages
    sma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
    sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    macd = exp1.iloc[-1] - exp2.iloc[-1]
    
    # Bollinger Bands
    bb_middle = df['Close'].rolling(window=20).mean().iloc[-1]
    bb_std = df['Close'].rolling(window=20).std().iloc[-1]
    bb_upper = bb_middle + (bb_std * 2)
    bb_lower = bb_middle - (bb_std * 2)
    
    return {
        'sma_20': sma_20,
        'sma_50': sma_50,
        'rsi': rsi,
        'macd': macd,
        'bb_upper': bb_upper,
        'bb_middle': bb_middle,
        'bb_lower': bb_lower,
        'price_vs_sma20': (df['Close'].iloc[-1] / sma_20 - 1) * 100,
        'price_vs_sma50': (df['Close'].iloc[-1] / sma_50 - 1) * 100
    }

def get_recent_news(symbol: str) -> List[Dict[str, str]]:
    """Get recent news for a symbol."""
    try:
        # You can expand this to use multiple news sources
        url = f"https://finance.yahoo.com/quote/{symbol}/news"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # This is a simplified version - you might want to use a proper news API
        return [{'title': f'News for {symbol}', 'url': url}]
    except:
        return []

def analyze_news_sentiment(news_data: List[Dict[str, str]]) -> Dict[str, float]:
    """Analyze sentiment of news articles."""
    # Placeholder - you can implement proper sentiment analysis
    return {
        'sentiment_score': 0.0,
        'sentiment_label': 'neutral',
        'confidence': 0.5
    } 