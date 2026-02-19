"""
Test script for comparison query

Tests: "Which performed better over 1 year: Apple or Nasdaq?"

This tests:
1. Multi-entity extraction (Apple, Nasdaq)
2. Comparison logic
3. Timeframe understanding (1 year)
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import orchestrate_query


async def test_comparison_query():
    """Test the comparison query"""
    query = "Which performed better over 1 year: Apple or Nasdaq?"
    
    print("\n" + "="*80)
    print("TESTING COMPARISON QUERY")
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
            
            # Entities resolved
            entities = response.context.get('entities', [])
            resolved_symbols = response.context.get('resolved_symbols', [])
            
            print(f"\nEntities Extracted: {entities}")
            print(f"Symbols Resolved: {resolved_symbols}")
            
            # Show data fetched for each entity
            if 'data' in response.context:
                data = response.context['data']
                
                if 'entities' in data:
                    print(f"\nData Fetched for Entities:")
                    for entity_name, entity_info in data['entities'].items():
                        print(f"\n  Entity: {entity_name}")
                        print(f"  Symbol: {entity_info.get('symbol', 'N/A')}")
                        
                        entity_data = entity_info.get('data', {})
                        
                        # Check what data types were fetched
                        data_types = []
                        if 'price' in entity_data or 'price_data' in entity_data:
                            data_types.append("current_price")
                        if 'price_change_data' in entity_data:
                            data_types.append("price_change")
                            # Show 1Y performance
                            pc_data = entity_data['price_change_data']
                            if pc_data.get('status') == 'success':
                                price_change = pc_data.get('price_change', {})
                                one_year = price_change.get('1Y', 'N/A')
                                print(f"  1-Year Performance: {one_year}%")
                        if 'historical_data' in entity_data:
                            data_types.append("historical")
                        if 'fundamentals_data' in entity_data:
                            data_types.append("fundamentals")
                        
                        print(f"  Data Types: {', '.join(data_types) if data_types else 'None'}")
        
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
    success = asyncio.run(test_comparison_query())
    exit(0 if success else 1)

