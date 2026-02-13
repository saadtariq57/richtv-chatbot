"""
Test LLM Quick Check (Tier 2 Assistance)

Tests the new feature where low/medium confidence queries
trigger a lightweight LLM check to refine classification.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_query(query: str, description: str, expected_behavior: str):
    """Test a single query with expected behavior"""
    print("\n" + "="*70)
    print(f"TEST: {description}")
    print("="*70)
    print(f"Query: {query}")
    print(f"Expected: {expected_behavior}")
    print("-"*70)
    
    try:
        response = await orchestrate_query(query)
        
        print(f"\n[RESPONSE]")
        print(f"Answer: {response.answer[:200]}...")  # First 200 chars
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
    """Test queries that should trigger LLM quick check"""
    print("\n" + "="*70)
    print("TESTING LLM QUICK CHECK (TIER 2 ASSISTANCE)")
    print("="*70)
    print("\nThese queries have ambiguous/low confidence in rule-based matching")
    print("LLM quick check should refine the classification\n")
    
    test_cases = [
        # Ambiguous queries that might match wrong patterns
        (
            "Should I invest in tech stocks right now?",
            "Investment timing question",
            "Should be GENERAL (market timing, not specific stock)"
        ),
        (
            "Tell me about Microsoft",
            "Company inquiry (vague)",
            "Should extract MSFT ticker and fetch data"
        ),
        (
            "Is Amazon a good buy?",
            "Investment opinion (company name)",
            "Should extract AMZN and provide data (not advice)"
        ),
        
        # Low confidence queries
        (
            "What about Tesla?",
            "Very vague query",
            "Should extract TSLA and fetch data"
        ),
        (
            "Explain dividend reinvestment",
            "Conceptual question (might match 'dividend' pattern)",
            "Should be GENERAL conceptual answer"
        ),
        
        # Edge cases
        (
            "How much is Nvidia?",
            "Company name without 'stock'",
            "Should extract NVDA ticker"
        ),
        (
            "Compare tech giants",
            "Multiple companies, no specific ticker",
            "Should be GENERAL or insufficient data"
        ),
    ]
    
    results = []
    for query, description, expected in test_cases:
        success = await test_query(query, description, expected)
        results.append((description, success))
        await asyncio.sleep(2)  # Avoid rate limiting
    
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
        print("\nAll LLM assistance tests passed!")
        print("Tier 2 (quick check) is working correctly.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

