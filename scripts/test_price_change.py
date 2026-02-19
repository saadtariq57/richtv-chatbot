"""
Test script for price-change endpoint integration

Tests queries that should benefit from price-change data:
1. "What's Apple's price?" (PRICE query)
2. "How is NVIDIA doing?" (ANALYSIS query)
3. "Tell me about Tesla stock" (ANALYSIS query)
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
    """Test a single query and show price-change data"""
    print("\n" + "="*80)
    print(f"TEST: {description}")
    print("="*80)
    print(f"Query: '{query}'")
    print("="*80)
    print()
    
    try:
        response = await orchestrate_query(query)
        
        # Display the final response
        print("\n" + "="*80)
        print("FINAL RESPONSE")
        print("="*80)
        print(f"\nAnswer:\n{response.answer}")
        print(f"\nConfidence: {response.confidence:.2f}")
        
        # Check if price-change data was fetched
        if response.context and 'data' in response.context:
            data = response.context['data']
            
            # Check for single entity
            if 'price_change_data' in data:
                print("\n" + "="*80)
                print("PRICE CHANGE DATA (Direct)")
                print("="*80)
                price_change = data['price_change_data'].get('price_change', {})
                if price_change:
                    print(f"\nSymbol: {price_change.get('symbol', 'N/A')}")
                    print(f"\nPerformance Summary:")
                    print(f"  1 Day:    {price_change.get('1D', 'N/A')}%")
                    print(f"  5 Days:   {price_change.get('5D', 'N/A')}%")
                    print(f"  1 Month:  {price_change.get('1M', 'N/A')}%")
                    print(f"  3 Months: {price_change.get('3M', 'N/A')}%")
                    print(f"  6 Months: {price_change.get('6M', 'N/A')}%")
                    print(f"  YTD:      {price_change.get('ytd', 'N/A')}%")
                    print(f"  1 Year:   {price_change.get('1Y', 'N/A')}%")
                    print(f"  3 Years:  {price_change.get('3Y', 'N/A')}%")
                    print(f"  5 Years:  {price_change.get('5Y', 'N/A')}%")
            
            # Check for entity structure
            if 'entities' in data:
                for entity_name, entity_info in data['entities'].items():
                    entity_data = entity_info.get('data', {})
                    if 'price_change_data' in entity_data:
                        print("\n" + "="*80)
                        print(f"PRICE CHANGE DATA ({entity_name})")
                        print("="*80)
                        price_change = entity_data['price_change_data'].get('price_change', {})
                        if price_change:
                            print(f"\nSymbol: {price_change.get('symbol', 'N/A')}")
                            print(f"\nPerformance Summary:")
                            print(f"  1 Day:    {price_change.get('1D', 'N/A')}%")
                            print(f"  5 Days:   {price_change.get('5D', 'N/A')}%")
                            print(f"  1 Month:  {price_change.get('1M', 'N/A')}%")
                            print(f"  3 Months: {price_change.get('3M', 'N/A')}%")
                            print(f"  6 Months: {price_change.get('6M', 'N/A')}%")
                            print(f"  YTD:      {price_change.get('ytd', 'N/A')}%")
                            print(f"  1 Year:   {price_change.get('1Y', 'N/A')}%")
                            print(f"  3 Years:  {price_change.get('3Y', 'N/A')}%")
                            print(f"  5 Years:  {price_change.get('5Y', 'N/A')}%")
            
            # Show sources used
            sources = response.context.get("sources_used", [])
            print(f"\nSources Used: {sources}")
        
        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all price-change tests"""
    print("\n" + "="*80)
    print("TESTING PRICE-CHANGE ENDPOINT INTEGRATION")
    print("="*80)
    
    test_cases = [
        ("What's Apple's price?", "PRICE query - should include price-change data"),
        ("How is NVIDIA doing?", "ANALYSIS query - should include price-change data"),
        ("Tell me about Tesla stock", "ANALYSIS query - comprehensive data"),
    ]
    
    results = []
    for query, description in test_cases:
        success = await test_query(query, description)
        results.append((description, success))
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
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

