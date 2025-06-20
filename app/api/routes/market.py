from fastapi import APIRouter
from api.models import MarketOverview, MarketMover
import requests
from bs4 import BeautifulSoup
from api.core.cache import get_tickers_info
import yfinance as yf
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/financials/{symbol}")
def get_financials(symbol: str):
    return get_tickers_info([symbol])

@router.get("/performance/{symbol}")
def get_performance(symbol: str):
    ticker = yf.Ticker(symbol)
    today = datetime.now()
    periods = {
        "3M": today - timedelta(days=90),
        "6M": today - timedelta(days=180),
        "1Y": today - timedelta(days=365)
    }
    
    performance = {}
    
    try:
        hist = ticker.history(period="1y")
        if hist.empty:
            return {"error": "Could not retrieve historical data."}

        current_price = hist['Close'].iloc[-1]

        for period, start_date in periods.items():
            # Find the closest available date in history
            past_date = hist.index[hist.index.searchsorted(start_date, side='right') -1]
            past_price = hist.loc[past_date]['Close']
            
            if past_price != 0:
                change_percent = ((current_price - past_price) / past_price) * 100
                performance[period] = round(change_percent, 2)
            else:
                performance[period] = "N/A"

    except Exception as e:
        print(f"Could not retrieve performance data for {symbol}: {e}")
        return {"error": str(e)}

    return performance

def get_yahoo_movers(page='gainers'):
    """Scrapes Yahoo Finance for top gainers or losers."""
    url = f"https://finance.yahoo.com/{page}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table')
        if not table:
            return []
            
        symbols = []
        for row in table.find_all('tr')[1:]:
            symbol_link = row.find('a', {'data-test': 'symbol'})
            if symbol_link:
                symbols.append(symbol_link.text)
            if len(symbols) >= 5:
                break
        return symbols
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Yahoo Finance {page} page: {e}")
        return []
    except Exception as e:
        print(f"Error parsing Yahoo Finance {page} page: {e}")
        return []

@router.get("/overview", response_model=list[MarketOverview])
def get_market_overview():
    indices = { "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI" }
    tickers_info = get_tickers_info(list(indices.values()))
    result = []

    for name, symbol in indices.items():
        try:
            info = tickers_info.get(symbol, {})
            if not info:
                continue
            value = info.get("regularMarketPrice", 0.0)
            change = info.get("regularMarketChange", 0.0)
            change_percent = info.get("regularMarketChangePercent", 0.0)
            result.append(MarketOverview(
                index=name, value=value, change=change, changePercent=change_percent
            ))
        except Exception as e:
            print(f"Could not process index {symbol}: {e}")
            continue
    return result

@router.get("/movers", response_model=list[MarketMover])
def get_market_movers():
    movers = []
    
    try:
        top_gainers_symbols = get_yahoo_movers('gainers')
        top_losers_symbols = get_yahoo_movers('losers')
        symbols = top_gainers_symbols + top_losers_symbols
        if not symbols:
            raise Exception("Scraping returned no symbols")
    except Exception as e:
        print(f"Could not fetch top movers by scraping: {e}")
        symbols = ["AAPL", "TSLA", "AMZN", "GOOGL", "MSFT"]

    if not symbols:
        return []

    tickers_info = get_tickers_info(symbols)
    for symbol in symbols:
        try:
            info = tickers_info.get(symbol, {})
            if not info or info.get("regularMarketPrice") is None:
                continue

            movers.append(MarketMover(
                symbol=symbol,
                name=info.get("shortName", symbol),
                price=info.get("regularMarketPrice", 0.0),
                change=info.get("regularMarketChange", 0.0),
                changePercent=info.get("regularMarketChangePercent", 0.0) * 100,
                volume=info.get("regularMarketVolume", 0)
            ))
        except Exception as e:
            print(f"Could not process symbol {symbol}: {e}")
            continue
            
    return movers 