#!/usr/bin/env python
"""
Batch LLM Classifier Tester

Run: python scripts/test_llm_classifier_batch.py

Tests multiple queries at once and shows a summary table.
Perfect for quick validation of LLM classification accuracy!
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm.generator import llm_classify_query
import time


def test_queries():
    """Test a predefined set of queries."""
    
    test_cases = [
        # Price queries (formal)
        "What's NVDA price?",
        "How much is AAPL trading at?",
        "Current price of TSLA",
        "MSFT stock price",
        
        # Price queries (informal - the LLM should handle these!)
        "How much is Apple worth right now?",
        "What's Tesla trading for?",
        "Tell me Microsoft's value",
        "What's Nvidia at?",
        
        # Historical queries
        "Show me NVDA performance last month",
        "AAPL historical data",
        "How did Tesla do in 2023?",
        "Microsoft trends over the year",
        
        # Fundamentals
        "What is NVDA revenue?",
        "Apple quarterly earnings",
        "Show me Tesla financials",
        "Microsoft P/E ratio",
        
        # Analysis
        "Should I buy NVDA?",
        "Is Apple a good investment?",
        "What do you think about Tesla stock?",
        "Give me your opinion on Microsoft",
        
        # Market queries
        "How's the market doing?",
        "What's the S&P 500 at?",
        "Show me the Nasdaq",
        "How's the stock market today?",
        
        # General/conceptual queries
        "What is a dividend?",
        "How does compound interest work?",
        "What's a bear market?",
        "Explain P/E ratio to me",
        
        # Edge cases / informal language
        "Tell me about Apple",
        "What's happening with Tesla?",
        "Should I invest in tech stocks?",
        "What's Figma trading at?",
        
        # Market overview queries (should return multiple symbols!)
        "Give me market update",
        "How's the market doing?",
        "Show me the market today",
        "Market overview",
        "How's tech doing?",
        "Crypto market update",
    ]
    
    print("\n" + "="*90)
    print("🤖 LLM CLASSIFIER - BATCH TEST")
    print("="*90 + "\n")
    print(f"Testing {len(test_cases)} queries...\n")
    
    results = []
    total_time = 0
    
    for i, query in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Testing: {query[:60]}{'...' if len(query) > 60 else ''}")
        
        try:
            start = time.time()
            query_type, confidence, entities, answer, symbols, date_range = llm_classify_query(query)
            elapsed = time.time() - start
            total_time += elapsed
            
            # Determine what was extracted
            if symbols:
                extracted = f"{len(symbols)} syms"
            elif entities:
                if len(entities) > 1:
                    extracted = f"{len(entities)} ents"
                else:
                    extracted = entities[0][:10]
            else:
                extracted = 'N/A'
            
            results.append({
                'query': query,
                'type': query_type,
                'confidence': confidence,
                'extracted': extracted,
                'has_answer': '✓' if answer else '✗',
                'time': elapsed,
                'status': '✅'
            })
            
        except Exception as e:
            results.append({
                'query': query,
                'type': 'ERROR',
                'confidence': 'N/A',
                'extracted': 'N/A',
                'has_answer': '✗',
                'time': 0,
                'status': f'❌ {str(e)[:30]}'
            })
    
    # Print results table
    print("\n" + "="*95)
    print("📊 RESULTS SUMMARY")
    print("="*95 + "\n")
    print("ℹ️  Extracted = Entity name OR number of symbols (for market queries)")
    print("   Ans = Whether LLM provided immediate answer (✓ for general queries)\n")
    
    # Header
    print(f"{'Query':<35} | {'Type':<12} | {'Conf':<6} | {'Extracted':<10} | {'Ans':<3} | {'Time':<6} | {'St':<3}")
    print("-"*95)
    
    # Results
    for r in results:
        query_short = r['query'][:33] + '..' if len(r['query']) > 35 else r['query']
        confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(r['confidence'], "⚪")
        extracted_short = r['extracted'][:8] + '..' if len(r['extracted']) > 10 else r['extracted']
        
        print(f"{query_short:<35} | {r['type']:<12} | {confidence_icon} {r['confidence']:<3} | {extracted_short:<10} | {r['has_answer']:<3} | {r['time']:.2f}s | {r['status']}")
    
    # Statistics
    print("\n" + "="*90)
    print("📈 STATISTICS")
    print("="*90 + "\n")
    
    successful = len([r for r in results if r['status'] == '✅'])
    failed = len(results) - successful
    avg_time = total_time / len(results) if results else 0
    
    print(f"Total Queries:        {len(results)}")
    print(f"Successful:           {successful} ({successful/len(results)*100:.1f}%)")
    print(f"Failed:               {failed}")
    print(f"Average Response Time: {avg_time:.2f}s")
    print(f"Total Time:           {total_time:.2f}s")
    
    # Type distribution
    type_counts = {}
    for r in results:
        if r['type'] != 'ERROR':
            type_counts[r['type']] = type_counts.get(r['type'], 0) + 1
    
    print("\nType Distribution:")
    for qtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / successful) * 100 if successful > 0 else 0
        bar = "█" * int(pct / 3)
        print(f"  {qtype:<12} │{bar:<33}│ {count} ({pct:.1f}%)")
    
    # Confidence distribution
    conf_counts = {}
    for r in results:
        if r['confidence'] != 'N/A':
            conf_counts[r['confidence']] = conf_counts.get(r['confidence'], 0) + 1
    
    print("\nConfidence Distribution:")
    for conf in ['high', 'medium', 'low']:
        count = conf_counts.get(conf, 0)
        pct = (count / successful) * 100 if successful > 0 else 0
        bar = "█" * int(pct / 3)
        icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}[conf]
        print(f"  {icon} {conf:<8} │{bar:<33}│ {count} ({pct:.1f}%)")
    
    print("\n" + "="*90 + "\n")


if __name__ == "__main__":
    try:
        test_queries()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.\n")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()

