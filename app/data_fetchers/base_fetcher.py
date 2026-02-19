"""
Base Fetcher - Abstract base class for all data fetchers

Provides common interface and error handling for:
- PriceFetcher
- FundamentalsFetcher
- NewsFetcher
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio


class BaseFetcher(ABC):
    """
    Abstract base class for all data fetchers.
    
    Subclasses must implement the fetch() method.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize fetcher.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
    
    @abstractmethod
    async def fetch(self, ticker: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch data for given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with fetched data
            
        Raises:
            FetcherException: If fetch fails
        """
        pass
    
    async def fetch_with_timeout(self, ticker: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch data with timeout protection.
        
        Args:
            ticker: Stock ticker symbol
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with fetched data or error info
        """
        try:
            result = await asyncio.wait_for(
                self.fetch(ticker, **kwargs),
                timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error": "Timeout",
                "message": f"Fetch timed out after {self.timeout}s",
                "ticker": ticker
            }
        except Exception as e:
            return {
                "status": "error",
                "error": type(e).__name__,
                "message": str(e),
                "ticker": ticker
            }


class FetcherException(Exception):
    """Custom exception for fetcher errors."""
    pass

