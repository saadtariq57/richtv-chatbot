"""
Test LLM Rescue Functionality

Tests edge case queries that would fail with rule-based extraction
but should succeed with LLM rescue fallback.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_query(query: str, description: str):
    """Test a single query and show results"""
    print("\n" + "="*70)
    print(f"Test: {description}")
    print(f"Query: {query}")
    print("-"*70)
    
    try:
        response = await orchestrate_query(query)
        
        # Check if rescue was applied
        rescue_applied = False
        llm_extracted = None
        if response.context and response.context.get("rescue_applied"):
            rescue_applied = True
            llm_extracted = response.context.get("llm_extracted_name")
        
        # Check result
        has_data = "$" in response.answer or any(char.isdigit() for char in response.answer)
        is_insufficient = "insufficient" in response.answer.lower()
        
        print(f"\nAnswer: {response.answer[:120]}..." if len(response.answer) > 120 
              else f"\nAnswer: {response.answer}")
        print(f"Confidence: {response.confidence:.2f}")
        
        if rescue_applied:
            print(f"LLM Rescue: APPLIED (extracted: '{llm_extracted}')")
        
        if has_data and not is_insufficient:
            print("Status: SUCCESS")
            return True
        else:
            print("Status: FAILED (insufficient data)")
            return False
            
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        return False


async def main():
    """Run edge case tests"""
    print("\n" + "="*70)
    print("LLM RESCUE TESTS - Edge Cases with Rule-Based Extraction Failures")
    print("="*70)
    
    test_cases = [
        # Possessive forms
        ("Tell me Nvidia's price", "Possessive form (Nvidia's)"),
        ("What's Tesla's stock worth?", "Possessive form (Tesla's)"),
        
        # Different phrasing
        ("How much for Apple?", "Short form"),
        ("Price of Microsoft", "Preposition phrasing"),
        ("Give me Bitcoin", "Command form"),
        
        # Contractions
        ("What's Figma trading at?", "Contraction (What's)"),
        ("How's Tesla doing?", "Contraction (How's)"),
        
        # Complex queries
        ("I want to know about Coinbase", "Long form"),
        ("Can you tell me Palantir?", "Polite form"),
        
        # Should still work (baseline)
        ("Apple price", "Simple baseline"),
        ("Tesla stock", "Simple baseline"),
    ]
    
    results = []
    for query, description in test_cases:
        success = await test_query(query, description)
        results.append((query, description, success))
        await asyncio.sleep(2)  # Avoid rate limiting
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    for query, description, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {description:35} | {query}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed >= total * 0.8:  # 80% pass rate
        print("\nLLM rescue working well!")
    else:
        print(f"\n{total - passed} test(s) failed - may need adjustment")
    
    return passed >= total * 0.8


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

