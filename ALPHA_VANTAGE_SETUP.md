# Alpha Vantage API Integration

This project has been updated to use Alpha Vantage API instead of Yahoo Finance (yfinance) for all stock market data.

## Setup

### 1. Get Alpha Vantage API Key

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free account
3. Get your API key from the dashboard

### 2. Set Environment Variable

Set your Alpha Vantage API key as an environment variable:

```bash
export ALPHA_VANTAGE_API_KEY=your_api_key_here
```

Or add it to your `.env` file:

```
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

### 3. Install Dependencies

```bash
pip install -r app/api/requirements.txt
```

## API Rate Limits

- **Free Tier**: 5 API calls per minute, 500 per day
- **Premium Tier**: 1200 API calls per minute

The application includes caching to minimize API calls and respect rate limits.

## Changes Made

### Files Updated:
- `app/api/core/cache.py` - Replaced yfinance with Alpha Vantage API calls
- `app/api/data/fetchers/market_data.py` - Updated historical data fetching
- `app/api/routes/market.py` - Updated performance calculations
- `app/api/routes/trending.py` - Updated stock enrichment
- `app/api/routes/user.py` - Removed unused yfinance import
- `app/api/routes/recommendations.py` - Removed unused yfinance import
- `app/api/requirements.txt` - Replaced yfinance with alpha_vantage
- `app/api/core/config.py` - Added configuration file

### New Features:
- Real-time stock quotes via Alpha Vantage GLOBAL_QUOTE
- Company overview data via Alpha Vantage OVERVIEW
- Historical price data via Alpha Vantage TIME_SERIES
- Improved error handling and rate limiting
- Centralized configuration management

## API Endpoints

All existing endpoints remain the same, but now use Alpha Vantage data:

- `/api/market/financials/{symbol}` - Real-time stock data
- `/api/market/performance/{symbol}` - Historical performance
- `/api/market/overview` - Market indices
- `/api/market/movers` - Top gainers/losers
- `/api/trending/trending` - Trending stocks
- `/api/trending/movers` - Top movers

## Data Mapping

The application maps Alpha Vantage data to match the previous yfinance structure:

- `regularMarketPrice` - Current stock price
- `regularMarketChange` - Price change
- `regularMarketChangePercent` - Percentage change
- `regularMarketVolume` - Trading volume
- `shortName` - Company name

## Testing

To test the integration:

1. Set your API key
2. Start the application
3. Make a request to `/api/market/financials/AAPL`
4. Verify you receive stock data

## Troubleshooting

- **Rate Limit Errors**: The app includes caching to minimize API calls
- **API Key Issues**: Ensure your API key is correctly set in environment variables
- **Data Format**: Alpha Vantage returns data in a different format than yfinance, but the app handles the conversion 