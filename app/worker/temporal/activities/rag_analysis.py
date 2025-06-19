import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from rag.vector_store import FinancialVectorStore, SAMPLE_DOCUMENTS
from typing import Dict, List, Any
from temporalio import activity
import requests
from bs4 import BeautifulSoup
import json

@activity.defn
async def get_rag_context(market_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Get relevant context for each stock using RAG."""
    
    # Initialize vector store
    vector_store = FinancialVectorStore()
    
    # Load existing documents or add sample documents
    try:
        vector_store.load("financial_docs")
    except:
        # Add sample documents if no existing store
        vector_store.add_documents(SAMPLE_DOCUMENTS)
        
        # Fetch recent news for stocks
        recent_news = await fetch_recent_news(list(market_data.keys()))
        vector_store.add_documents(recent_news)
        
        # Save the vector store
        vector_store.save("financial_docs")
    
    # Get context for each stock
    rag_context = {}
    
    for symbol, data in market_data.items():
        try:
            # Create queries based on stock data
            queries = generate_queries(symbol, data)
            
            # Search for relevant documents
            relevant_docs = []
            for query in queries:
                docs = vector_store.search(query, k=3, symbol_filter=symbol)
                relevant_docs.extend(docs)
            
            # Also get general market context
            market_docs = vector_store.search(f"market analysis {symbol} sector {data.get('sector', '')}", k=2)
            relevant_docs.extend(market_docs)
            
            # Remove duplicates and sort by relevance
            unique_docs = remove_duplicates(relevant_docs)
            unique_docs.sort(key=lambda x: x['score'], reverse=True)
            
            rag_context[symbol] = unique_docs[:5]  # Top 5 most relevant documents
            
        except Exception as e:
            print(f"Error getting RAG context for {symbol}: {e}")
            rag_context[symbol] = []
    
    return rag_context

def generate_queries(symbol: str, data: Dict[str, Any]) -> List[str]:
    """Generate search queries based on stock data."""
    queries = []
    
    # Basic stock query
    queries.append(f"{symbol} stock analysis")
    
    # Sector-specific query
    sector = data.get('sector', '')
    if sector:
        queries.append(f"{symbol} {sector} sector performance")
    
    # Technical analysis query
    tech = data.get('technical_indicators', {})
    if tech.get('rsi', 50) < 30:
        queries.append(f"{symbol} oversold RSI technical analysis")
    elif tech.get('rsi', 50) > 70:
        queries.append(f"{symbol} overbought RSI technical analysis")
    
    # Volume analysis
    volume = data.get('volume', 0)
    if volume > 10000000:  # High volume
        queries.append(f"{symbol} high volume trading analysis")
    
    # Market cap based query
    market_cap = data.get('market_cap', 0)
    if market_cap > 1000000000000:  # Large cap
        queries.append(f"{symbol} large cap stock analysis")
    elif market_cap < 10000000000:  # Small cap
        queries.append(f"{symbol} small cap stock analysis")
    
    return queries

async def fetch_recent_news(symbols: List[str]) -> List[Dict[str, Any]]:
    """Fetch recent news for symbols."""
    news_documents = []
    
    for symbol in symbols[:5]:  # Limit to first 5 symbols to avoid rate limiting
        try:
            # Fetch news from Yahoo Finance
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract news headlines (this is a simplified version)
                news_items = soup.find_all('h3', class_='Mb(5px)')[:3]  # Get first 3 news items
                
                for item in news_items:
                    title = item.get_text().strip()
                    if title:
                        news_documents.append({
                            'title': title,
                            'content': f"Recent news about {symbol}: {title}",
                            'source': 'Yahoo Finance',
                            'date': '2024-01-15',  # You can extract actual dates
                            'symbol': symbol,
                            'type': 'news'
                        })
            
        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            continue
    
    return news_documents

def remove_duplicates(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate documents based on title."""
    seen_titles = set()
    unique_docs = []
    
    for doc in documents:
        title = doc.get('title', '')
        if title not in seen_titles:
            seen_titles.add(title)
            unique_docs.append(doc)
    
    return unique_docs

@activity.defn
async def update_rag_knowledge_base():
    """Update the RAG knowledge base with new documents."""
    
    vector_store = FinancialVectorStore()
    
    try:
        vector_store.load("financial_docs")
    except:
        vector_store.add_documents(SAMPLE_DOCUMENTS)
    
    # Fetch latest news and earnings reports
    latest_news = await fetch_latest_financial_news()
    vector_store.add_documents(latest_news)
    
    # Save updated vector store
    vector_store.save("financial_docs")
    
    return {"status": "success", "documents_added": len(latest_news)}

async def fetch_latest_financial_news() -> List[Dict[str, Any]]:
    """Fetch latest financial news from multiple sources."""
    # This is a placeholder - you would implement actual news fetching
    # from APIs like Alpha Vantage, NewsAPI, or web scraping
    
    return [
        {
            'title': 'Market Update: Tech Stocks Rally',
            'content': 'Technology stocks showed strong performance today with major indices up 2%.',
            'source': 'MarketWatch',
            'date': '2024-01-15',
            'symbol': 'MARKET',
            'type': 'market_analysis'
        }
    ] 