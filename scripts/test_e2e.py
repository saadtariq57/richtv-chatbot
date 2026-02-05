"""
End-to-End Test Script

Tests the complete flow:
1. User query → API endpoint
2. Classification → Data fetching → LLM → Validation → Response
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_query(query: str, description: str):
    """Test a single query end-to-end"""
    print("\n" + "="*70)
    print(f"TEST: {description}")
    print("="*70)
    print(f"Query: {query}")
    print("-"*70)
    
    try:
        response = await orchestrate_query(query)
        
        print(f"\n[RESPONSE]")
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Data Timestamp: {response.data_timestamp}")
        print(f"\nCitations ({len(response.citations)}):")
        for citation in response.citations:
            print(f"  - {citation.source}")
        
        if response.context:
            sources = response.context.get("sources_used", [])
            print(f"\nSources Used: {', '.join(sources)}")
            if "fetch_errors" in response.context.get("data", {}):
                errors = response.context["data"]["fetch_errors"]
                if errors:
                    print(f"\n[WARNINGS] {len(errors)} fetch error(s):")
                    for err in errors:
                        print(f"  - {err}")
        
        print(f"\n[SUCCESS] Query processed successfully")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all end-to-end tests"""
    print("\n" + "="*70)
    print("END-TO-END SYSTEM TEST")
    print("="*70)
    print("\nTesting complete flow: Query -> Classification -> API -> LLM -> Response")
    
    test_cases = [
        # PRICE queries
        ("What's the price of NVDA?", "PRICE - Single stock"),
        ("How much is Apple trading at?", "PRICE - Alternative phrasing (company name)"),
        ("What's TSLA worth right now?", "PRICE - Current value"),
        
        # HISTORICAL queries
        ("Show me NVDA's price history", "HISTORICAL - Price history"),
        ("What was NVDA's price last month?", "HISTORICAL - Time-based"),
        
        # FUNDAMENTALS queries
        ("What are NVDA's earnings?", "FUNDAMENTALS - Earnings"),
        ("Show me NVDA's revenue", "FUNDAMENTALS - Revenue"),
        
        # MARKET queries
        ("How's the market doing?", "MARKET - General market"),
        ("What's the S&P 500 at?", "MARKET - Specific index"),
        
        # ANALYSIS queries (should fetch multiple sources)
        ("Should I buy NVDA?", "ANALYSIS - Investment advice"),
        ("Tell me about NVDA stock", "ANALYSIS - General analysis"),
    ]
    
    results = []
    for query, description in test_cases:
        success = await test_query(query, description)
        results.append((description, success))
        # Small delay between tests to avoid rate limiting
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {description}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll end-to-end tests passed!")
    else:
        print(f"\n{total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

