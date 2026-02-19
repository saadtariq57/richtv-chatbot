"""
Price Fetcher - Retrieves stock price data from Mboum's first-party API.

Uses the official Mboum API (not RapidAPI):
- Base URL: https://api.mboum.com
- Real-time quote: GET /v1/markets/stock/quotes
- Auth: Authorization: Bearer {YOUR_AUTH_KEY}
- Query params: ticker=<TICKER> (supports multiple tickers, comma-separated)
See: https://docs.mboum.com/ (Stocks → GET /v1/markets/stock/quotes)
"""

from typing import Dict, Any, Optional
from datetime import datetime

import httpx

from app.config import settings
from app.data_fetchers.base_fetcher import BaseFetcher


class PriceFetcher(BaseFetcher):
    """
    Fetches current price data for a single ticker using Mboum.

    API docs (Mboum Stocks /v1/markets/stock/quotes):
    - Base URL: https://api.mboum.com
    - Endpoint: /v1/markets/stock/quotes
    - Method: GET
    - Query params: ticker=<TICKER> (supports comma-separated multiple tickers)
    - Auth header: Authorization: Bearer {YOUR_AUTH_KEY}
    """

    MBOUM_BASE_URL = "https://api.mboum.com"

    async def fetch(self, ticker: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch real-time price data for ticker from Mboum.

        Args:
            ticker: Stock ticker symbol
            **kwargs: Reserved for future params (e.g., region)

        Returns:
            Dictionary with normalized price data or error info.
        """
        ticker_upper = ticker.upper()
        api_key: Optional[str] = settings.mboum_api_key

        if not api_key:
            return {
                "ticker": ticker_upper,
                "status": "error",
                "error": "MissingApiKey",
                "message": "Mboum API key is not configured",
            }

        # See Mboum docs: https://docs.mboum.com/ (Stocks → GET /v1/markets/stock/quotes)
        url = f"{self.MBOUM_BASE_URL}/v1/markets/stock/quotes"
        # Endpoint accepts `ticker` query param (supports comma-separated tickers)
        params = {"ticker": ticker_upper}
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params, headers=headers)

            if resp.status_code != 200:
                return {
                    "ticker": ticker_upper,
                    "status": "error",
                    "error": f"HTTP_{resp.status_code}",
                    "message": f"Mboum API request failed with status {resp.status_code}",
                }

            data = resp.json()

            # For /v1/markets/stock/quotes, Mboum wraps data in a `body` array,
            # but be defensive in case of different formats.
            if isinstance(data, dict) and "body" in data:
                items = data.get("body") or []
            elif isinstance(data, list):
                items = data
            else:
                items = []

            quote = items[0] if items else data
            if not isinstance(quote, dict):
                return {
                    "ticker": ticker_upper,
                    "status": "error",
                    "error": "InvalidResponse",
                    "message": "Unexpected Mboum response format",
                }

            price = self._safe_get(quote, ["regularMarketPrice", "price", "ask"])
            change = self._safe_get(quote, ["regularMarketChange", "change"])
            change_percent = self._safe_get(
                quote, ["regularMarketChangePercent", "changesPercentage"]
            )

            if price is None:
                return {
                    "ticker": ticker_upper,
                    "status": "error",
                    "error": "NoPriceData",
                    "message": "No price field found in Mboum response",
                    "raw": quote,
                }

            return {
                "ticker": ticker_upper,
                "price": float(price),
                "change": float(change) if change is not None else None,
                "change_percent": float(change_percent) if change_percent is not None else None,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "Mboum API",
                "status": "success",
                "raw": quote,
            }

        except httpx.RequestError as e:
            return {
                "ticker": ticker_upper,
                "status": "error",
                "error": "RequestError",
                "message": str(e),
            }
        except Exception as e:
            return {
                "ticker": ticker_upper,
                "status": "error",
                "error": type(e).__name__,
                "message": str(e),
            }

    async def fetch_batch(self, tickers: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch price data for multiple tickers in a single API call.
        
        Mboum API supports comma-separated tickers for efficient batch fetching.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dict mapping ticker → price data
        """
        if not tickers:
            return {}
        
        api_key: Optional[str] = settings.mboum_api_key
        
        if not api_key:
            # Return error for all tickers
            return {
                ticker: {
                    "ticker": ticker.upper(),
                    "status": "error",
                    "error": "MissingApiKey",
                    "message": "Mboum API key is not configured",
                }
                for ticker in tickers
            }
        
        # Join tickers with commas for batch request
        tickers_str = ",".join([t.upper() for t in tickers])
        
        url = f"{self.MBOUM_BASE_URL}/v1/markets/stock/quotes"
        params = {"ticker": tickers_str}
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params, headers=headers)
            
            if resp.status_code != 200:
                # Return error for all tickers
                error_result = {
                    "status": "error",
                    "error": f"HTTP_{resp.status_code}",
                    "message": f"Mboum API batch request failed with status {resp.status_code}",
                }
                return {ticker: {**error_result, "ticker": ticker.upper()} for ticker in tickers}
            
            data = resp.json()
            
            # Parse response - Mboum wraps data in a `body` array
            if isinstance(data, dict) and "body" in data:
                items = data.get("body") or []
            elif isinstance(data, list):
                items = data
            else:
                items = []
            
            # Map each quote to its ticker
            results = {}
            for quote in items:
                if not isinstance(quote, dict):
                    continue
                
                # Get ticker from quote
                ticker_symbol = quote.get("symbol", "").upper()
                if not ticker_symbol:
                    continue
                
                price = self._safe_get(quote, ["regularMarketPrice", "price", "ask"])
                change = self._safe_get(quote, ["regularMarketChange", "change"])
                change_percent = self._safe_get(
                    quote, ["regularMarketChangePercent", "changesPercentage"]
                )
                
                if price is not None:
                    results[ticker_symbol] = {
                        "ticker": ticker_symbol,
                        "price": float(price),
                        "change": float(change) if change is not None else None,
                        "change_percent": float(change_percent) if change_percent is not None else None,
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "Mboum API (Batch)",
                        "status": "success",
                        "raw": quote,
                    }
            
            # Fill in errors for tickers that weren't in the response
            for ticker in tickers:
                ticker_upper = ticker.upper()
                if ticker_upper not in results:
                    results[ticker_upper] = {
                        "ticker": ticker_upper,
                        "status": "error",
                        "error": "NoData",
                        "message": f"No data returned for {ticker_upper}",
                    }
            
            return results
            
        except httpx.RequestError as e:
            # Return error for all tickers
            error_result = {
                "status": "error",
                "error": "RequestError",
                "message": str(e),
            }
            return {ticker: {**error_result, "ticker": ticker.upper()} for ticker in tickers}
        except Exception as e:
            # Return error for all tickers
            error_result = {
                "status": "error",
                "error": type(e).__name__,
                "message": str(e),
            }
            return {ticker: {**error_result, "ticker": ticker.upper()} for ticker in tickers}

    @staticmethod
    def _safe_get(data: Dict[str, Any], keys: list) -> Optional[float]:
        """Try multiple possible keys and return the first non-null numeric-like value."""
        for key in keys:
            if key in data and data[key] is not None:
                try:
                    return float(data[key])
                except (TypeError, ValueError):
                    continue
        return None

