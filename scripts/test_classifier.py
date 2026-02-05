#!/usr/bin/env python
"""
Interactive Query Classifier Tester

Run: python scripts/test_classifier.py

Test your queries and see how they get classified in real-time!
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.classifier import get_classifier, QueryType


def print_banner():
    """Print welcome banner."""
    print("\n" + "="*70)
    print("🧪 QUERY CLASSIFIER - INTERACTIVE TESTER")
    print("="*70)
    print("\nTest how your queries get classified!")
    print("\nAvailable query types:")
    print("  • PRICE       - Real-time stock prices (Mboum API)")
    print("  • HISTORICAL  - Past price data (FMP API)")
    print("  • FUNDAMENTALS- Financial statements (FMP API)")
    print("  • NEWS        - News articles (RAG)")
    print("  • MARKET      - Market data (FMP API)")
    print("  • ANALYSIS    - Investment analysis (Multiple sources)")
    print("\nCommands:")
    print("  • Type any query to classify it")
    print("  • 'stats' - Show classification statistics")
    print("  • 'examples' - Show example queries")
    print("  • 'quit' or 'exit' - Exit the tester")
    print("="*70 + "\n")


def show_examples():
    """Show example queries."""
    examples = {
        "PRICE": [
            "What's NVDA price?",
            "How much is AAPL worth?",
            "MSFT trading at?"
        ],
        "HISTORICAL": [
            "NVDA price last month",
            "Show me AAPL performance over the year",
            "Historical data for TSLA"
        ],
        "FUNDAMENTALS": [
            "What is NVDA revenue?",
            "AAPL quarterly earnings",
            "Show me MSFT P/E ratio"
        ],
        "NEWS": [
            "Latest NVDA news",
            "Recent headlines for AAPL",
            "What's happening with TSLA?"
        ],
        "ANALYSIS": [
            "Should I buy NVDA?",
            "Is AAPL a good investment?",
            "Your opinion on TSLA?"
        ],
        "HYBRID": [
            "NVDA price and recent news",
            "Tell me about AAPL earnings and stock performance",
            "Should I buy MSFT based on recent news?"
        ]
    }
    
    print("\n" + "="*70)
    print("📝 EXAMPLE QUERIES")
    print("="*70 + "\n")
    
    for category, queries in examples.items():
        print(f"{category}:")
        for query in queries:
            print(f"  • {query}")
        print()


def classify_and_display(classifier, query: str):
    """Classify a query and display results."""
    result = classifier.classify(query)
    
    # Color coding for confidence
    confidence_colors = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🔴"
    }
    confidence_icon = confidence_colors.get(result.confidence, "⚪")
    
    print(f"\n{'─'*70}")
    print(f"Query: \"{query}\"")
    print(f"{'─'*70}")
    
    # Query types
    print(f"\n📋 Detected Query Types:")
    for qt in result.query_types:
        print(f"  • {qt.value.upper()}")
    
    # Confidence
    print(f"\n{confidence_icon} Confidence: {result.confidence.upper()}")
    
    # Matched patterns
    if result.matched_patterns:
        print(f"\n🎯 Matched Patterns:")
        for pattern in result.matched_patterns[:5]:  # Show first 5
            print(f"  • {pattern}")
        if len(result.matched_patterns) > 5:
            print(f"  ... and {len(result.matched_patterns) - 5} more")
    
    # Data sources that would be called
    print(f"\n🔄 Data Sources to Query:")
    source_mapping = {
        QueryType.PRICE: "Mboum API (real-time prices)",
        QueryType.HISTORICAL: "FMP Historical API (past data)",
        QueryType.FUNDAMENTALS: "FMP Fundamentals API (financials)",
        QueryType.NEWS: "RAG Vector Store (news articles)",
        QueryType.MARKET: "FMP Market API (market data)",
        QueryType.ANALYSIS: "Multiple sources (comprehensive analysis)"
    }
    
    for qt in result.query_types:
        source = source_mapping.get(qt, "Unknown source")
        print(f"  • {source}")
    
    print(f"\n{'─'*70}\n")


def show_stats(classifier):
    """Show classification statistics."""
    stats = classifier.get_classification_stats()
    
    if stats.get("total_classifications", 0) == 0:
        print("\n⚠️  No classifications yet. Try some queries first!\n")
        return
    
    print("\n" + "="*70)
    print("📊 CLASSIFICATION STATISTICS")
    print("="*70 + "\n")
    
    print(f"Total Queries Classified: {stats['total_classifications']}\n")
    
    print("Confidence Distribution:")
    for conf, count in stats['confidence_distribution'].items():
        pct = (count / stats['total_classifications']) * 100
        bar = "█" * int(pct / 2)
        print(f"  {conf.upper():8s} │{bar:50s}│ {count} ({pct:.1f}%)")
    
    print("\nQuery Type Distribution:")
    for qtype, count in sorted(stats['query_type_distribution'].items(), 
                               key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / stats['total_classifications']) * 100
            bar = "█" * int(pct / 2)
            print(f"  {qtype:12s} │{bar:50s}│ {count} ({pct:.1f}%)")
    
    print(f"\nAverage Types per Query: {stats['avg_types_per_query']:.2f}")
    print()


def main():
    """Main interactive loop."""
    classifier = get_classifier()
    print_banner()
    
    while True:
        try:
            # Get user input
            query = input("🔍 Enter query (or command): ").strip()
            
            if not query:
                continue
            
            # Handle commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for testing! Goodbye.\n")
                break
            
            elif query.lower() == 'stats':
                show_stats(classifier)
            
            elif query.lower() == 'examples':
                show_examples()
            
            elif query.lower() == 'help':
                print_banner()
            
            elif query.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
            
            else:
                # Classify the query
                classify_and_display(classifier, query)
        
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for testing! Goodbye.\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()

