"""
Test script for GENERAL query handling with LLM fallback.

Tests the new feature where unmatched patterns trigger an LLM call
that can either answer general questions or extract tickers.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_query(query: str, description: str):
    """Test a single query"""
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
        print(f"Sources: {response.context.get('sources_used', [])}")
        print(f"\n[SUCCESS]")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests for general and specific queries"""
    print("\n" + "="*70)
    print("TESTING GENERAL QUERY HANDLING")
    print("="*70)
    
    test_cases = [
        # General conceptual questions (should be answered by LLM)
        ("What is a dividend?", "GENERAL - Financial concept"),
        ("How does the stock market work?", "GENERAL - Conceptual question"),
        ("What is crypto?", "GENERAL - Definition"),
        
        # Specific stock queries (should fetch data)
        ("What's NVDA's price?", "SPECIFIC - Clear ticker"),
        ("How much is Apple trading at?", "SPECIFIC - Company name (LLM extracts AAPL)"),
        ("Tell me about Tesla stock", "SPECIFIC - Company name (LLM extracts TSLA)"),
        
        # Edge cases
        ("What's the weather like?", "OFF-TOPIC - Should be rejected"),
    ]
    
    results = []
    for query, description in test_cases:
        success = await test_query(query, description)
        results.append((description, success))
        await asyncio.sleep(1)  # Avoid rate limiting
    
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
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

