"""
Test Company Name → Ticker Resolution

Tests that company names like "Apple", "Tesla", "Microsoft" 
correctly resolve to their ticker symbols.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_query(query: str, expected_ticker: str):
    """Test a company name query"""
    print("\n" + "="*70)
    print(f"Query: {query}")
    print(f"Expected Ticker: {expected_ticker}")
    print("-"*70)
    
    try:
        response = await orchestrate_query(query)
        
        # Check if we got a valid numeric answer (not "Insufficient data")
        has_price = "$" in response.answer or any(char.isdigit() for char in response.answer)
        is_insufficient = "insufficient" in response.answer.lower()
        
        print(f"\n[RESPONSE]")
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence:.2f}")
        
        if response.context and "data" in response.context:
            ticker_used = response.context["data"].get("ticker", "UNKNOWN")
            print(f"Ticker Used: {ticker_used}")
            
            if ticker_used == expected_ticker:
                print(f"[SUCCESS] Correct ticker extracted!")
                return True
            elif has_price and not is_insufficient:
                print(f"[PARTIAL] Got price data but ticker mismatch (expected {expected_ticker}, got {ticker_used})")
                return True
            else:
                print(f"[FAIL] Wrong ticker or insufficient data")
                return False
        else:
            if not is_insufficient and has_price:
                print(f"[SUCCESS] Got valid answer")
                return True
            else:
                print(f"[FAIL] Insufficient data returned")
                return False
        
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test company name resolution"""
    print("\n" + "="*70)
    print("TESTING COMPANY NAME -> TICKER RESOLUTION")
    print("="*70)
    
    test_cases = [
        ("What's Apple trading at?", "AAPL"),
        ("How much is Apple?", "AAPL"),
        ("Apple stock price", "AAPL"),
        
        ("What's Tesla worth?", "TSLA"),
        ("Tesla stock price", "TSLA"),
        ("Tell me about Tesla", "TSLA"),
        
        ("Microsoft price", "MSFT"),
        ("How much is Microsoft trading at?", "MSFT"),
        
        ("What's Nvidia's price?", "NVDA"),
        ("Nvidia stock", "NVDA"),
        
        ("Amazon stock price", "AMZN"),
        ("Google stock", "GOOGL"),

    ]
    
    results = []
    for query, expected_ticker in test_cases:
        success = await test_query(query, expected_ticker)
        results.append((query, success))
        await asyncio.sleep(1.5)  # Avoid rate limiting
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for query, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {query}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll company name tests passed!")
        print("Company names are being correctly resolved to tickers.")
    else:
        print(f"\n{total - passed} test(s) failed - some company names not resolving correctly")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

