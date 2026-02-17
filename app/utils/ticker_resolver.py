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

# Default market overview symbols (backup if LLM doesn't provide any)
DEFAULT_MARKET_SYMBOLS = [
    # Major Indices
    "^GSPC",    # S&P 500
    "^DJI",     # Dow Jones
    "^IXIC",    # Nasdaq
    # Top Tech Stocks
    "AAPL",     # Apple
    "MSFT",     # Microsoft
    "NVDA",     # NVIDIA
    "GOOGL",    # Google
    "AMZN",     # Amazon
    "TSLA",     # Tesla
    # Major Crypto
    "BTC-USD",  # Bitcoin
    "ETH-USD",  # Ethereum
    # Key Commodities
    "GC=F",     # Gold
    "CL=F",     # Crude Oil
]


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


async def resolve_entity_to_symbol(entity: str) -> Optional[Dict]:
    """
    Resolve any entity (company name, ticker, crypto) to a proper symbol.
    
    This is the main entry point for entity resolution in the orchestration flow.
    Always uses Mboum Search API to find the best match.
    
    Args:
        entity: Raw entity from LLM (e.g., "Apple", "BTC", "Tesla", "Ethereum")
        
    Returns:
        Dict with resolved symbol and metadata, or None if not found:
        {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'type': 'EQUITY',
            'exchange': 'NASDAQ',
            'score': 1.0
        }
    """
    if not entity:
        return None
    
    # Search Mboum for the entity
    results = await search_mboum(entity)
    
    if not results:
        print(f"Entity resolution: No results found for '{entity}'")
        return None
    
    # Get best matching symbol
    best_symbol = filter_best_ticker(results)
    
    if not best_symbol:
        return None
    
    # Find the full result for the best symbol
    best_result = next((r for r in results if r.get('symbol') == best_symbol), None)
    
    if best_result:
        return {
            'symbol': best_result.get('symbol'),
            'name': best_result.get('longname') or best_result.get('shortname', ''),
            'type': best_result.get('quoteType', ''),
            'exchange': best_result.get('exchDisp', ''),
            'score': best_result.get('score', 0)
        }
    
    # Fallback: just return symbol
    return {
        'symbol': best_symbol,
        'name': '',
        'type': '',
        'exchange': '',
        'score': 0
    }


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


def validate_symbols(symbols: List[str], max_symbols: int = 20) -> List[str]:
    """
    Validate and clean symbol list from LLM.
    
    Rules:
    1. Remove duplicates
    2. Remove empty/invalid symbols
    3. Limit to max_symbols
    4. Basic format validation
    
    Args:
        symbols: List of symbols from LLM
        max_symbols: Maximum number of symbols to return (default: 20)
        
    Returns:
        Cleaned and validated list of symbols
    """
    if not symbols:
        return []
    
    validated = []
    seen = set()
    
    for symbol in symbols:
        # Clean the symbol
        symbol = symbol.strip().upper()
        
        # Skip empty or already seen
        if not symbol or symbol in seen:
            continue
        
        # Basic validation: should contain alphanumeric chars
        # Valid formats: AAPL, BTC-USD, ^GSPC, GC=F
        if not any(c.isalnum() for c in symbol):
            continue
        
        # Skip if too long (likely invalid)
        if len(symbol) > 15:
            continue
        
        validated.append(symbol)
        seen.add(symbol)
        
        # Stop at max limit
        if len(validated) >= max_symbols:
            break
    
    return validated

