#!/usr/bin/env python
"""
Interactive Query Classifier Tester - LLM Edition

Run: python scripts/test_classifier.py

Test your queries and see how they get classified by the LLM in real-time!

NOTE: This now uses the new LLM-based classification instead of rule-based patterns.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm.generator import llm_classify_query


def print_banner():
    """Print welcome banner."""
    print("\n" + "="*70)
    print("🤖 LLM QUERY CLASSIFIER - INTERACTIVE TESTER")
    print("="*70)
    print("\n✨ Test how the LLM classifies your queries!")
    print("   (Now handles informal language & context better!)")
    print("\nAvailable query types:")
    print("  • PRICE       - Real-time stock prices")
    print("  • HISTORICAL  - Past price data & trends")
    print("  • FUNDAMENTALS- Financial statements & metrics")
    print("  • ANALYSIS    - Investment analysis & recommendations")
    print("  • MARKET      - Market indices & overall status")
    print("  • GENERAL     - Conceptual financial questions")
    print("\nCommands:")
    print("  • Type any query to classify it")
    print("  • 'examples' - Show example queries")
    print("  • 'quit' or 'exit' - Exit the tester")
    print("="*70 + "\n")


def show_examples():
    """Show example queries - including informal language the LLM can handle!"""
    examples = {
        "PRICE (Formal & Informal)": [
            "What's NVDA price?",
            "How much is Apple trading at?",
            "Tell me Tesla's current value",
            "What's Microsoft worth right now?"
        ],
        "HISTORICAL": [
            "NVDA performance last month",
            "Show me Apple's stock over the year",
            "How did Tesla do in 2023?",
            "Microsoft trends last quarter"
        ],
        "FUNDAMENTALS": [
            "What is NVDA revenue?",
            "Apple quarterly earnings",
            "Show me Microsoft financials",
            "Tesla's profit margins"
        ],
        "ANALYSIS": [
            "Should I buy NVDA?",
            "Is Apple a good investment?",
            "What do you think about Tesla?",
            "Give me your take on Microsoft stock"
        ],
        "MARKET": [
            "How's the market doing?",
            "What's the S&P 500 at?",
            "How's the stock market today?",
            "Show me the Nasdaq"
        ],
        "GENERAL (Conceptual)": [
            "What is a dividend?",
            "How does compound interest work?",
            "What's a bear market?",
            "Explain P/E ratio"
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


def classify_and_display(query: str):
    """Classify a query using LLM and display results."""
    import time
    
    # Call LLM classifier (now returns 5 values)
    start_time = time.time()
    query_type, confidence, entity, answer, symbols = llm_classify_query(query)
    elapsed_time = time.time() - start_time
    
    # Color coding for confidence
    confidence_colors = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🔴"
    }
    confidence_icon = confidence_colors.get(confidence, "⚪")
    
    print(f"\n{'─'*70}")
    print(f"Query: \"{query}\"")
    print(f"{'─'*70}")
    
    # Query type
    print(f"\n📋 LLM Classification:")
    print(f"  • Type: {query_type.upper()}")
    
    # Confidence
    print(f"\n{confidence_icon} Confidence: {confidence.upper()}")
    
    # Extracted entity or symbols
    if symbols:
        print(f"\n📊 Symbols to Fetch (Market Query):")
        print(f"  • Count: {len(symbols)}")
        print(f"  • Symbols: {', '.join(symbols[:10])}")
        if len(symbols) > 10:
            print(f"  • ... and {len(symbols) - 10} more")
        print(f"  ℹ️  Note: Will fetch all in parallel via Mboum API")
    elif entity:
        print(f"\n🎯 Extracted Entity:")
        print(f"  • {entity}")
        print(f"  ℹ️  Note: Will be resolved via Mboum Search API")
        print(f"     (e.g., 'BTC' → 'BTC-USD', 'Apple' → 'AAPL')")
    else:
        print(f"\n🎯 No entity/symbols extracted (general query)")
    
    # If general query, show the answer
    if answer:
        print(f"\n💬 LLM Answer (General Query):")
        # Truncate long answers for display
        answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
        print(f"  {answer_preview}")
    
    # Data sources that would be called
    print(f"\n🔄 Orchestration Flow:")
    if query_type == "general" and answer:
        print(f"  ✅ Answered immediately (no data fetching)")
        print(f"  📊 Total LLM calls: 1 (optimized!)")
    else:
        print(f"  1️⃣  Entity resolution (Mboum Search API)")
        source_mapping = {
            "price": "2️⃣  Fetch: Mboum API (real-time prices)",
            "historical": "2️⃣  Fetch: FMP Historical API (past data)",
            "fundamentals": "2️⃣  Fetch: FMP Fundamentals API (financials)",
            "news": "2️⃣  Fetch: RAG Vector Store (news articles)",
            "market": "2️⃣  Fetch: Mboum API (market/index data)",
            "analysis": "2️⃣  Fetch: Multiple sources (comprehensive analysis)"
        }
        print(f"  {source_mapping.get(query_type, '2️⃣  Fetch: Unknown source')}")
        print(f"  3️⃣  Generate answer with LLM")
        print(f"  📊 Total LLM calls: 2 (classify + generate)")
    
    # Performance
    print(f"\n⚡ Classification Time: {elapsed_time:.2f}s")
    
    print(f"\n{'─'*70}\n")


def main():
    """Main interactive loop."""
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
            
            elif query.lower() == 'examples':
                show_examples()
            
            elif query.lower() == 'help':
                print_banner()
            
            elif query.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
            
            else:
                # Classify the query using LLM
                classify_and_display(query)
        
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for testing! Goodbye.\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

