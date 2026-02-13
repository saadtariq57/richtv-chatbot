"""
Ticker Resolution Module

Resolves company names to ticker symbols using Mboum search API.
Strongly prefers US exchanges (NYSE/NASDAQ) for consistency.
"""

import httpx
from typing import Optional, List, Dict
from app.config import settings


# US exchanges to prioritize
US_EXCHANGES = ['NYSE', 'NASDAQ', 'NYSEARCA', 'AMEX']


async def resolve_ticker(company_name: str) -> Optional[str]:
    """
    Resolve company name to ticker symbol using Mboum search.
    
    Strategy:
    1. Search Mboum for company name
    2. Strongly prefer US exchanges (NYSE/NASDAQ)
    3. Fall back to highest-scored international listing
    4. Handle all asset types (equity, crypto, index, ETF)
    
    Args:
        company_name: Company name to search (e.g., "Apple", "Bitcoin", "SAP")
        
    Returns:
        Ticker symbol (e.g., "AAPL", "BTC-USD", "SAP") or None if not found
    """
    results = await search_mboum(company_name)
    
    if not results:
        return None
    
    best_ticker = filter_best_ticker(results)
    return best_ticker


async def search_mboum(query: str) -> List[Dict]:
    """
    Search Mboum API for ticker symbols.
    
    Args:
        query: Search query (company name, ticker, etc.)
        
    Returns:
        List of search results with symbol, name, exchange, score, etc.
    """
    if not settings.mboum_api_key:
        print("Warning: Mboum API key not configured")
        return []
    
    url = "https://api.mboum.com/v1/markets/search"
    params = {
        "search": query,
        "apikey": settings.mboum_api_key
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("body", [])
        else:
            print(f"Mboum search error: {response.status_code}")
            return []
            
    except httpx.RequestError as e:
        print(f"Mboum search request error: {e}")
        return []


def filter_best_ticker(search_results: List[Dict]) -> Optional[str]:
    """
    Pick the best ticker from Mboum search results.
    
    Strategy (Option A - Hard US Preference):
    1. For EQUITY: Strongly prefer US exchanges, take highest-scored US listing
    2. For CRYPTO/INDEX/ETF: Take highest-scored result (no exchange preference)
    3. If no US listing exists: Fall back to highest international
    
    Args:
        search_results: List of search results from Mboum
        
    Returns:
        Best matching ticker symbol or None
    """
    if not search_results:
        return None
    
    # Group results by quote type
    equities = []
    cryptos = []
    indices = []
    etfs = []
    others = []
    
    for result in search_results:
        qtype = result.get('quoteType', '').upper()
        
        if qtype == 'EQUITY':
            equities.append(result)
        elif qtype == 'CRYPTOCURRENCY':
            cryptos.append(result)
        elif qtype == 'INDEX':
            indices.append(result)
        elif qtype == 'ETF':
            etfs.append(result)
        else:
            others.append(result)
    
    # Handle EQUITY: Strong US preference
    if equities:
        # Filter for US exchanges
        us_equities = [r for r in equities if r.get('exchDisp') in US_EXCHANGES]
        
        # Additionally filter out symbols with dots (foreign tickers like 1S2.SG)
        clean_us_equities = [r for r in us_equities if '.' not in r.get('symbol', '')]
        
        if clean_us_equities:
            # Return highest-scored clean US equity
            clean_us_equities.sort(key=lambda x: x.get('score', 0), reverse=True)
            return clean_us_equities[0]['symbol']
        elif us_equities:
            # No clean US equities, but we have US listings
            us_equities.sort(key=lambda x: x.get('score', 0), reverse=True)
            return us_equities[0]['symbol']
        else:
            # No US listing at all, fall back to highest international
            equities.sort(key=lambda x: x.get('score', 0), reverse=True)
            return equities[0]['symbol']
    
    # Handle CRYPTOCURRENCY: No exchange preference, just take highest score
    if cryptos:
        cryptos.sort(key=lambda x: x.get('score', 0), reverse=True)
        return cryptos[0]['symbol']
    
    # Handle INDEX: No exchange preference
    if indices:
        indices.sort(key=lambda x: x.get('score', 0), reverse=True)
        return indices[0]['symbol']
    
    # Handle ETF: Prefer US but not as strictly as equity
    if etfs:
        us_etfs = [r for r in etfs if r.get('exchDisp') in US_EXCHANGES]
        if us_etfs:
            us_etfs.sort(key=lambda x: x.get('score', 0), reverse=True)
            return us_etfs[0]['symbol']
        else:
            etfs.sort(key=lambda x: x.get('score', 0), reverse=True)
            return etfs[0]['symbol']
    
    # Handle other types: Just take highest score
    if others:
        others.sort(key=lambda x: x.get('score', 0), reverse=True)
        return others[0]['symbol']
    
    return None


def extract_company_name_from_query(query: str) -> Optional[str]:
    """
    Extract likely company name from user query.
    
    Examples:
    - "What's Apple trading at?" → "Apple"
    - "Show me Figma stock price" → "Figma"
    - "Bitcoin price" → "Bitcoin"
    
    Args:
        query: User query string
        
    Returns:
        Extracted company name or None
    """
    # Remove common question/noise words
    noise_words = {
        'what', 'whats', 'is', 'the', 'price', 'of', 'stock', 'trading', 
        'at', 'how', 'much', 'tell', 'me', 'about', 'show', 'get',
        'current', 'todays', 'today', 'worth', 'value', 'quote',
        'a', 'an', 'and', 'or', 'for', 'to', 'in', 's'
    }
    
    # Replace contractions and strip punctuation
    query_cleaned = query.lower()
    # Remove apostrophes (what's -> whats, it's -> its)
    query_cleaned = query_cleaned.replace("'", "")
    
    # Tokenize, strip punctuation, then filter noise words
    tokens = query_cleaned.split()
    clean_tokens = []
    
    for token in tokens:
        # Strip remaining punctuation
        cleaned = token.strip('?,!."')
        # Check if it's not a noise word
        if cleaned and cleaned not in noise_words:
            clean_tokens.append(cleaned)
    
    # Return first meaningful token (likely the company name)
    if clean_tokens:
        return clean_tokens[0].capitalize()
    
    return None

