"""
Test Ticker Resolution with Mboum Search

Tests the new ticker resolver for various companies including:
- New IPOs (Figma)
- International companies (SAP, Toyota)
- Cryptocurrencies (Bitcoin)
- Common US stocks (Apple, Tesla)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.ticker_resolver import resolve_ticker, search_mboum, filter_best_ticker


async def test_search_and_resolution(company_name: str, expected_symbol: str = None):
    """Test Mboum search and ticker resolution"""
    print("\n" + "="*70)
    print(f"Query: {company_name}")
    if expected_symbol:
        print(f"Expected: {expected_symbol}")
    print("-"*70)
    
    # Get raw search results
    results = await search_mboum(company_name)
    
    if not results:
        print("No results found")
        return False
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results[:5], 1):  # Show top 5
        symbol = result.get('symbol', 'N/A')
        exchange = result.get('exchDisp', 'N/A')
        qtype = result.get('quoteType', 'N/A')
        score = result.get('score', 0)
        name = result.get('shortname', 'N/A')
        print(f"  {i}. {symbol:12} | {exchange:15} | {qtype:15} | Score: {score} | {name}")
    
    # Apply filtering logic
    best_ticker = filter_best_ticker(results)
    
    print(f"\nFiltered Result: {best_ticker}")
    
    if expected_symbol:
        if best_ticker == expected_symbol:
            print(f"SUCCESS - Matched expected symbol!")
            return True
        else:
            print(f"MISMATCH - Expected {expected_symbol}, got {best_ticker}")
            return False
    
    return True


async def main():
    """Run ticker resolution tests"""
    print("\n" + "="*70)
    print("TICKER RESOLUTION TESTS - Mboum Search with US Exchange Preference")
    print("="*70)
    
    test_cases = [
        ("Figma", "FIG"),           # New IPO
        ("Apple", "AAPL"),          # Common US stock
        ("Tesla", "TSLA"),          # Common US stock
        ("SAP", "SAP"),             # International company with US listing
        ("Toyota", "TM"),           # Japanese company with US ADR
        ("Bitcoin", "BTC-USD"),     # Cryptocurrency
        ("Microsoft", "MSFT"),      # Common US stock
        ("Coinbase", "COIN"),       # Recent IPO
    ]
    
    results = []
    for company_name, expected in test_cases:
        success = await test_search_and_resolution(company_name, expected)
        results.append((company_name, expected, success))
        await asyncio.sleep(1)  # Avoid rate limiting
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    for company, expected, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {company:15} -> {expected}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll ticker resolution tests passed!")
    else:
        print(f"\n{total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

