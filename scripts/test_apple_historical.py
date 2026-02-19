"""
Test script for historical date range query

Tests: "Show Apple performance from 1 Jan 2020 to 15 March 2020"

Shows:
1. How date range queries are classified
2. What data is fetched (and if date range is respected)
3. How the LLM interprets the data
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_historical_query():
    """Test the historical Apple query with detailed output"""
    query = "Show Apple performance from 1 Jan 2020 to 15 March 2020"
    
    print("\n" + "="*80)
    print("TESTING HISTORICAL QUERY WITH DATE RANGE")
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
            print(f"\nQuery Type: {response.context.get('sources_used', [])}")
            print(f"Classification Confidence: {response.context.get('classification_confidence', 'N/A')}")
            
            # Entities resolved
            entities = response.context.get('entities', [])
            resolved_symbols = response.context.get('resolved_symbols', [])
            
            print(f"\nEntities Extracted: {entities}")
            print(f"Symbols Resolved: {resolved_symbols}")
            
            # Show the actual data structure sent to LLM
            if 'data' in response.context:
                data = response.context['data']
                
                # Check for historical data
                if 'entities' in data:
                    print(f"\nEntities Data Structure:")
                    for entity_name, entity_info in data['entities'].items():
                        print(f"\n   Entity: {entity_name}")
                        print(f"   Symbol: {entity_info.get('symbol', 'N/A')}")
                        
                        entity_data = entity_info.get('data', {})
                        
                        # Check for historical data
                        if 'historical_data' in entity_data:
                            hist_data = entity_data['historical_data']
                            if hist_data.get('status') == 'success':
                                historical = hist_data.get('historical', [])
                                print(f"   Historical Data Points: {len(historical)}")
                                
                                if historical:
                                    # Show first and last dates
                                    print(f"   Date Range:")
                                    print(f"      First: {historical[-1].get('date', 'N/A')}")
                                    print(f"      Last:  {historical[0].get('date', 'N/A')}")
                                    
                                    # Show sample data points
                                    print(f"\n   Sample Data Points (first 5):")
                                    for i, point in enumerate(historical[:5]):
                                        date = point.get('date', 'N/A')
                                        close = point.get('close', 'N/A')
                                        change = point.get('change', 'N/A')
                                        change_pct = point.get('changePercent', 'N/A')
                                        print(f"      {i+1}. {date}: Close=${close}, Change={change} ({change_pct}%)")
                            else:
                                print(f"   Historical Data Status: {hist_data.get('status', 'N/A')}")
                                if 'error' in hist_data:
                                    print(f"   Error: {hist_data.get('error')}")
                        
                        # Check for price data
                        if 'price' in entity_data:
                            print(f"\n   Current Price Data:")
                            price_data = entity_data['price']
                            if isinstance(price_data, dict):
                                print(f"      Price: ${price_data.get('price', 'N/A')}")
                                print(f"      Change: {price_data.get('change', 'N/A')} ({price_data.get('change_percent', 'N/A')}%)")
            
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
        
        # Show the raw context structure (abbreviated)
        print("\n" + "="*80)
        print("RAW CONTEXT STRUCTURE (for debugging)")
        print("="*80)
        if response.context and 'data' in response.context:
            data_keys = response.context['data'].keys()
            print(f"Top-level keys in context: {list(data_keys)}")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_historical_query())
    exit(0 if success else 1)

