"""
Test script for market update query

Tests: "Give me the market update"

This should trigger MARKET query type and fetch broad market data.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_market_update():
    """Test the market update query"""
    query = "Give me the market update"
    
    print("\n" + "="*80)
    print("TESTING MARKET UPDATE QUERY")
    print("="*80)
    print(f"Query: '{query}'")
    print("="*80)
    print()
    
    try:
        # Run the orchestration
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
            print(f"\nQuery Type: {response.context.get('sources_used', [])}")
            print(f"Classification Confidence: {response.context.get('classification_confidence', 'N/A')}")
            
            # Symbols used
            symbols_requested = response.context.get('symbols_requested', [])
            symbols_fetched = response.context.get('symbols_fetched', [])
            
            print(f"\nSymbols Requested: {len(symbols_requested)}")
            print(f"   {symbols_requested}")
            
            print(f"\nSymbols Successfully Fetched: {len(symbols_fetched)}")
            print(f"   {symbols_fetched}")
            
            # Show the market overview structure
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
                            for symbol, data in list(items.items())[:5]:  # Show first 5
                                price = data.get('price', 'N/A')
                                change_pct = data.get('change_percent', 'N/A')
                                name = data.get('name', symbol)
                                print(f"      - {symbol} ({name}): ${price} ({change_pct}%)")
                            if len(items) > 5:
                                print(f"      ... and {len(items) - 5} more")
        
        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_market_update())
    exit(0 if success else 1)

