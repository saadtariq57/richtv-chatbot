"""
FMP Fetcher - Retrieves historical prices and fundamentals from
Financial Modeling Prep (FMP) APIs.

Docs:
- General: https://site.financialmodelingprep.com/developer/docs
- Historical prices: /api/v3/historical-price-full/{ticker}
- Income statement: /api/v3/income-statement/{ticker}
"""

from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.data_fetchers.base_fetcher import BaseFetcher


class FMPFetcher(BaseFetcher):
    """
    Fetches data from FMP for multiple use-cases:

    - Historical prices  → /historical-price-full/{ticker}
    - Fundamentals       → /income-statement/{ticker}
    - Market snapshot    → /quote/%5EGSPC etc. (simple index view)

    Authentication uses the `apikey` query parameter as per
    FMP docs: https://site.financialmodelingprep.com/developer/docs
    """

    BASE_URL: str = settings.fmp_base_url

    async def fetch(self, ticker: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch method required by BaseFetcher.

        Dispatches based on a `mode` kwarg:
        - mode="historical"   → historical prices
        - mode="fundamentals" → income statement
        - mode="market"       → simple market snapshot
        - mode="price_change" → price change summary (1D, 5D, 1M, 3M, 6M, YTD, 1Y, etc.)
        """
        mode = kwargs.pop("mode", "historical")

        if mode == "fundamentals":
            return await self._fetch_fundamentals(ticker, **kwargs)
        elif mode == "market":
            # For market-level data, the ticker argument is optional.
            return await self._fetch_market(ticker=ticker, **kwargs)
        elif mode == "price_change":
            return await self._fetch_price_change(ticker, **kwargs)
        else:
            # Default: historical
            return await self._fetch_historical(ticker, **kwargs)

    async def _fetch_historical(
        self,
        ticker: str,
        timeseries: int = 30,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Fetch historical OHLCV data for a ticker.

        Args:
            ticker: Stock ticker symbol
            timeseries: Number of data points to return (FMP `timeseries` param)
            from_date: Start date in YYYY-MM-DD format (optional)
            to_date: End date in YYYY-MM-DD format (optional)
            
        Note:
            If both from_date and to_date are provided, they take precedence over timeseries.
            If neither is provided, defaults to timeseries (last N days).
        """
        api_key: Optional[str] = settings.fmp_api_key
        ticker_upper = ticker.upper()

        if not api_key:
            return {
                "ticker": ticker_upper,
                "status": "error",
                "error": "MissingApiKey",
                "message": "FMP API key is not configured",
            }

        url = f"{self.BASE_URL}/historical-price-full/{ticker_upper}"
        params = {
            "apikey": api_key,
        }
        
        # Use date range if provided, otherwise use timeseries
        if from_date and to_date:
            params["from"] = from_date
            params["to"] = to_date
        else:
            params["timeseries"] = timeseries

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)

            if resp.status_code != 200:
                return {
                    "ticker": ticker_upper,
                    "status": "error",
                    "error": f"HTTP_{resp.status_code}",
                    "message": f"FMP historical request failed with status {resp.status_code}",
                }

            data = resp.json()
            # Expected format per docs: { "symbol": "...", "historical": [ ... ] }
            historical = data.get("historical") if isinstance(data, dict) else None

            return {
                "ticker": data.get("symbol", ticker_upper)
                if isinstance(data, dict)
                else ticker_upper,
                "status": "success",
                "source": "FMP Historical API",
                "timestamp": datetime.utcnow().isoformat(),
                "historical": historical or [],
                "raw": data,
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

    async def _fetch_fundamentals(
        self,
        ticker: str,
        limit: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Fetch income statement fundamentals for a ticker.

        Args:
            ticker: Stock ticker symbol
            limit: Number of periods to return (default 1 = latest)
        """
        api_key: Optional[str] = settings.fmp_api_key
        ticker_upper = ticker.upper()

        if not api_key:
            return {
                "ticker": ticker_upper,
                "status": "error",
                "error": "MissingApiKey",
                "message": "FMP API key is not configured",
            }

        url = f"{self.BASE_URL}/income-statement/{ticker_upper}"
        params = {
            "apikey": api_key,
            "limit": limit,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)

            if resp.status_code != 200:
                return {
                    "ticker": ticker_upper,
                    "status": "error",
                    "error": f"HTTP_{resp.status_code}",
                    "message": f"FMP fundamentals request failed with status {resp.status_code}",
                }

            data = resp.json()
            # Docs indicate an array of statements is returned.
            statements = data if isinstance(data, list) else []
            latest = statements[0] if statements else None

            summary = None
            if latest:
                summary = {
                    "date": latest.get("date"),
                    "revenue": latest.get("revenue"),
                    "netIncome": latest.get("netIncome"),
                    "eps": latest.get("eps"),
                }

            return {
                "ticker": ticker_upper,
                "status": "success",
                "source": "FMP Fundamentals API",
                "timestamp": datetime.utcnow().isoformat(),
                "summary": summary,
                "statements": statements,
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

    async def _fetch_market(
        self,
        ticker: str = "^GSPC",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Fetch a simple market snapshot.

        Uses the quote endpoint with a major index (default S&P 500).
        Docs: https://site.financialmodelingprep.com/developer/docs/quote
        """
        api_key: Optional[str] = settings.fmp_api_key
        symbol = ticker or "^GSPC"

        if not api_key:
            return {
                "ticker": symbol,
                "status": "error",
                "error": "MissingApiKey",
                "message": "FMP API key is not configured",
            }

        url = f"{self.BASE_URL}/quote/{symbol}"
        params = {
            "apikey": api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)

            if resp.status_code != 200:
                return {
                    "ticker": symbol,
                    "status": "error",
                    "error": f"HTTP_{resp.status_code}",
                    "message": f"FMP market quote request failed with status {resp.status_code}",
                }

            data = resp.json()
            quote = data[0] if isinstance(data, list) and data else data

            return {
                "ticker": quote.get("symbol", symbol) if isinstance(quote, dict) else symbol,
                "status": "success",
                "source": "FMP Market API",
                "timestamp": datetime.utcnow().isoformat(),
                "quote": quote,
            }
        except httpx.RequestError as e:
            return {
                "ticker": symbol,
                "status": "error",
                "error": "RequestError",
                "message": str(e),
            }
        except Exception as e:
            return {
                "ticker": symbol,
                "status": "error",
                "error": type(e).__name__,
                "message": str(e),
            }

    async def _fetch_price_change(
        self,
        ticker: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Fetch price change summary for a ticker across multiple timeframes.
        
        Returns performance metrics for 1D, 5D, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y, 10Y.
        
        Args:
            ticker: Stock ticker symbol
            
        Docs: https://financialmodelingprep.com/api/v3/stock-price-change/AAPL
        """
        api_key: Optional[str] = settings.fmp_api_key
        ticker_upper = ticker.upper()

        if not api_key:
            return {
                "ticker": ticker_upper,
                "status": "error",
                "error": "MissingApiKey",
                "message": "FMP API key is not configured",
            }

        url = f"{self.BASE_URL}/stock-price-change/{ticker_upper}"
        params = {
            "apikey": api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)

            if resp.status_code != 200:
                return {
                    "ticker": ticker_upper,
                    "status": "error",
                    "error": f"HTTP_{resp.status_code}",
                    "message": f"FMP price change request failed with status {resp.status_code}",
                }

            data = resp.json()
            # API returns a list with one item
            price_change = data[0] if isinstance(data, list) and data else data

            return {
                "ticker": price_change.get("symbol", ticker_upper) if isinstance(price_change, dict) else ticker_upper,
                "status": "success",
                "source": "FMP Price Change API",
                "timestamp": datetime.utcnow().isoformat(),
                "price_change": price_change,
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


