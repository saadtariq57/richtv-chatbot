"""
Test script to verify each API endpoint individually.

Tests:
1. Mboum /v1/quote endpoint
2. FMP /historical-price-full/{ticker} endpoint
3. FMP /income-statement/{ticker} endpoint
4. FMP /quote/{symbol} endpoint
"""

import asyncio
import json
from app.data_fetchers.price_fetcher import PriceFetcher
from app.data_fetchers.fmp_fetcher import FMPFetcher
from app.config import settings


async def test_mboum_quote():
    """Test Mboum /v1/quote endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Mboum API - GET /v1/quote")
    print("="*60)
    
    print(f"Endpoint: https://api.mboum.com/v1/quote")
    print(f"Auth: Authorization: Bearer {settings.mboum_api_key[:10]}..." if settings.mboum_api_key else "Auth: MISSING API KEY")
    print(f"Query param: ticker=NVDA")
    
    fetcher = PriceFetcher()
    result = await fetcher.fetch("NVDA")
    
    print(f"\nStatus: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"[SUCCESS]")
        print(f"   Ticker: {result.get('ticker')}")
        print(f"   Price: ${result.get('price')}")
        print(f"   Change: {result.get('change')}")
        print(f"   Change %: {result.get('change_percent')}%")
        print(f"   Source: {result.get('source')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    else:
        print(f"[FAILED]")
        print(f"   Error: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    
    return result.get('status') == 'success'


async def test_fmp_historical():
    """Test FMP /historical-price-full/{ticker} endpoint"""
    print("\n" + "="*60)
    print("TEST 2: FMP API - GET /historical-price-full/{ticker}")
    print("="*60)
    
    print(f"Endpoint: https://financialmodelingprep.com/api/v3/historical-price-full/NVDA")
    print(f"Auth: apikey={settings.fmp_api_key[:10]}..." if settings.fmp_api_key else "Auth: MISSING API KEY")
    print(f"Query param: timeseries=30")
    
    fetcher = FMPFetcher()
    result = await fetcher.fetch("NVDA", mode="historical", timeseries=30)
    
    print(f"\nStatus: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"[SUCCESS]")
        print(f"   Ticker: {result.get('ticker')}")
        historical = result.get('historical', [])
        print(f"   Historical data points: {len(historical)}")
        if historical:
            latest = historical[0]
            print(f"   Latest date: {latest.get('date')}")
            print(f"   Latest close: ${latest.get('close')}")
        print(f"   Source: {result.get('source')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    else:
        print(f"[FAILED]")
        print(f"   Error: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    
    return result.get('status') == 'success'


async def test_fmp_fundamentals():
    """Test FMP /income-statement/{ticker} endpoint"""
    print("\n" + "="*60)
    print("TEST 3: FMP API - GET /income-statement/{ticker}")
    print("="*60)
    
    print(f"Endpoint: https://financialmodelingprep.com/api/v3/income-statement/NVDA")
    print(f"Auth: apikey={settings.fmp_api_key[:10]}..." if settings.fmp_api_key else "Auth: MISSING API KEY")
    print(f"Query param: limit=1")
    
    fetcher = FMPFetcher()
    result = await fetcher.fetch("NVDA", mode="fundamentals", limit=1)
    
    print(f"\nStatus: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"[SUCCESS]")
        print(f"   Ticker: {result.get('ticker')}")
        summary = result.get('summary', {})
        if summary:
            print(f"   Date: {summary.get('date')}")
            print(f"   Revenue: ${summary.get('revenue')}")
            print(f"   Net Income: ${summary.get('netIncome')}")
            print(f"   EPS: ${summary.get('eps')}")
        statements = result.get('statements', [])
        print(f"   Statements returned: {len(statements)}")
        print(f"   Source: {result.get('source')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    else:
        print(f"[FAILED]")
        print(f"   Error: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    
    return result.get('status') == 'success'


async def test_mboum_market_index():
    """Test Mboum with market index (S&P 500) - same endpoint as stocks"""
    print("\n" + "="*60)
    print("TEST 4: Mboum API - GET /v1/markets/stock/quotes (Index)")
    print("="*60)
    
    print(f"Endpoint: https://api.mboum.com/v1/markets/stock/quotes")
    print(f"Auth: Authorization: Bearer {settings.mboum_api_key[:10]}..." if settings.mboum_api_key else "Auth: MISSING API KEY")
    print(f"Query param: ticker=^GSPC (S&P 500)")
    print(f"\nNote: Mboum handles indexes in the same endpoint as stocks!")
    
    fetcher = PriceFetcher()
    result = await fetcher.fetch("^GSPC")
    
    print(f"\nStatus: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"[SUCCESS]")
        print(f"   Ticker: {result.get('ticker')}")
        print(f"   Price: ${result.get('price')}")
        print(f"   Change: {result.get('change')}")
        print(f"   Change %: {result.get('change_percent')}%")
        print(f"   Source: {result.get('source')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    else:
        print(f"[FAILED]")
        print(f"   Error: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
        print(f"\n   FULL RESPONSE:")
        print(json.dumps(result, indent=4, default=str))
    
    return result.get('status') == 'success'


async def main():
    """Run all endpoint tests"""
    print("\n" + "="*60)
    print("API ENDPOINT VERIFICATION TEST")
    print("="*60)
    print("\nTesting each endpoint individually to verify correctness...")
    
    # Check API keys
    print("\nAPI Key Status:")
    print(f"   Mboum API Key: {'Set' if settings.mboum_api_key else 'Missing'}")
    print(f"   FMP API Key: {'Set' if settings.fmp_api_key else 'Missing'}")
    
    if not settings.mboum_api_key:
        print("\nWARNING: Mboum API key not found in .env")
    if not settings.fmp_api_key:
        print("\nWARNING: FMP API key not found in .env")
    
    # Run tests
    results = []
    
    results.append(("Mboum Quote (Stock)", await test_mboum_quote()))
    results.append(("FMP Historical", await test_fmp_historical()))
    results.append(("FMP Fundamentals", await test_fmp_fundamentals()))
    results.append(("Mboum Quote (Index)", await test_mboum_market_index()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"   {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll endpoints are working correctly!")
    else:
        print("\nSome endpoints failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

