"""
Test script for "What's happening with AI stocks?" query

This script provides detailed debugging output showing:
1. How the query is classified
2. What symbols are selected
3. What data is fetched
4. How the LLM uses the data to generate the answer
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_ai_stocks_query():
    """Test the AI stocks query with detailed output"""
    query = "What's happening with AI stocks?"
    
    print("\n" + "="*80)
    print("TESTING AI STOCKS QUERY")
    print("="*80)
    print(f"Query: '{query}'")
    print("="*80)
    print()
    
    try:
        # Run the orchestration (this will show internal logging)
        response = await orchestrate_query(query)
        
        # Display the final response
        print("\n" + "="*80)
        print("FINAL RESPONSE")
        print("="*80)
        print(f"\nAnswer:\n{response.answer}")
        print(f"\nConfidence: {response.confidence:.2f}")
        print(f"Data Timestamp: {response.data_timestamp}")
        
        # Show citations
        print(f"\nCitations ({len(response.citations)}):")
        for i, citation in enumerate(response.citations, 1):
            print(f"  {i}. {citation.source}")
        
        # Show detailed context information
        if response.context:
            print("\n" + "="*80)
            print("DETAILED CONTEXT ANALYSIS")
            print("="*80)
            
            # Query classification
            print(f"\nClassification Confidence: {response.context.get('classification_confidence', 'N/A')}")
            
            # Symbols used
            symbols_requested = response.context.get('symbols_requested', [])
            symbols_fetched = response.context.get('symbols_fetched', [])
            
            print(f"\nSymbols Requested: {len(symbols_requested)}")
            print(f"   {symbols_requested}")
            
            print(f"\nSymbols Successfully Fetched: {len(symbols_fetched)}")
            print(f"   {symbols_fetched}")
            
            # Show the actual data structure sent to LLM
            if 'data' in response.context:
                data = response.context['data']
                
                if 'market_overview' in data:
                    market_overview = data['market_overview']
                    
                    print(f"\nMarket Overview Data Structure:")
                    print(f"   - Indices: {len(market_overview.get('indices', {}))}")
                    print(f"   - Stocks: {len(market_overview.get('stocks', {}))}")
                    print(f"   - Crypto: {len(market_overview.get('crypto', {}))}")
                    print(f"   - Commodities: {len(market_overview.get('commodities', {}))}")
                    
                    # Show sample data for each category
                    print("\nSample Data by Category:")
                    
                    for category in ['indices', 'stocks', 'crypto', 'commodities']:
                        items = market_overview.get(category, {})
                        if items:
                            print(f"\n   {category.upper()}:")
                            for symbol, data in list(items.items())[:3]:  # Show first 3
                                price = data.get('price', 'N/A')
                                change_pct = data.get('change_percent', 'N/A')
                                print(f"      - {symbol}: ${price} ({change_pct}%)")
                            if len(items) > 3:
                                print(f"      ... and {len(items) - 3} more")
            
            # Check for any fetch errors
            if 'data' in response.context and 'fetch_errors' in response.context['data']:
                errors = response.context['data']['fetch_errors']
                if errors:
                    print(f"\nFETCH ERRORS ({len(errors)}):")
                    for err in errors:
                        print(f"   - {err}")
        
        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ai_stocks_query())
    exit(0 if success else 1)

