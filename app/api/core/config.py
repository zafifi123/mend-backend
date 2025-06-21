import os

# -- MOCK DATA SWITCH --
# Set to True to use mock data instead of calling the real Alpha Vantage API
USE_MOCK_DATA = True

# Alpha Vantage API Configuration
ALPHA_VANTAGE_API_KEY = 'FTGFCC0SFOR6VT65'
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'

# Cache Configuration
CACHE_DURATION_SECONDS = 60  # Cache data for 60 seconds

# API Rate Limiting (Alpha Vantage has rate limits)
# Free tier: 5 API calls per minute and 500 per day
# Premium tier: 1200 API calls per minute
MAX_REQUESTS_PER_MINUTE = 5  # Adjust based on your API tier 