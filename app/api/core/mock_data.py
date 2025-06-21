import random
from datetime import datetime, timedelta

def get_mock_stock_quote(symbol: str):
    """
    Generates a mock real-time stock quote for a given symbol.
    """
    base_price = random.uniform(100, 500)
    change = random.uniform(-5, 5)
    return {
        'symbol': symbol,
        'regularMarketPrice': round(base_price, 2),
        'regularMarketChange': round(change, 2),
        'regularMarketChangePercent': round((change / base_price) * 100, 2),
        'regularMarketVolume': random.randint(1_000_000, 100_000_000),
        'shortName': f"{symbol} Inc.",
        'previousClose': round(base_price - change, 2),
        'open': round(base_price + random.uniform(-1, 1), 2),
        'high': round(base_price + random.uniform(1, 3), 2),
        'low': round(base_price - random.uniform(1, 3), 2)
    }

def get_mock_company_overview(symbol: str):
    """
    Generates a mock company overview for a given symbol.
    """
    return {
        'symbol': symbol,
        'shortName': f"{symbol} Corporation",
        'sector': random.choice(['Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical']),
        'industry': 'Software - Infrastructure',
        'marketCap': f"{random.randint(100, 3000)}B",
        'description': f'This is a mock description for {symbol}. It is a leading company in its industry.'
    }

def get_mock_performance(symbol: str):
    """
    Generates mock performance data for different time periods.
    """
    return {
        "3M": round(random.uniform(-15, 20), 2),
        "6M": round(random.uniform(-25, 30), 2),
        "1Y": round(random.uniform(-30, 50), 2)
    }

def get_mock_financials(symbol: str):
    """
    Combines mock quote and overview data.
    """
    quote = get_mock_stock_quote(symbol)
    overview = get_mock_company_overview(symbol)
    return {symbol: {**quote, **overview}} 