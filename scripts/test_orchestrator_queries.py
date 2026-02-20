"""
Comprehensive Test Script for Orchestrator Queries

Tests various types of queries through the full orchestration pipeline:
- Historical performance queries
- Comparison queries
- Market overview queries
- Hypothetical investment scenarios
- Multi-entity queries

Results are saved to a timestamped log file for evaluation.
"""

import asyncio
import json
import sys
import os
import io
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.orchestrator import orchestrate_query
from app.config import settings


# Test cases to evaluate
TEST_CASES = [
    {
        "id": 1,
        "query": "Last 7 trading days performance of Tesla.",
        "description": "Historical performance - specific timeframe",
        "expected_type": "historical",
        "expected_entities": ["Tesla"]
    },
    {
        "id": 2,
        "query": "Performance during COVID crash.",
        "description": "Historical event-based query",
        "expected_type": "historical",
        "expected_entities": []  # May or may not extract a specific symbol
    },
    {
        "id": 3,
        "query": "Which performed better over 1 year: Apple or Nasdaq?",
        "description": "Comparison query - multiple entities",
        "expected_type": "historical/analysis",
        "expected_entities": ["Apple", "Nasdaq"]
    },
    {
        "id": 4,
        "query": "Give me last 2 months performace of nvidia",
        "description": "Historical performance - specific timeframe",
        "expected_type": "historical",
        "expected_entities": ["nvidia"]
    },
    {
        "id": 5,
        "query": "Compare Nvidia vs AMD volatility last 3 months.",
        "description": "Comparison query - volatility analysis",
        "expected_type": "analysis",
        "expected_entities": ["Nvidia", "AMD"]
    },
    {
        "id": 6,
        "query": "Which FAANG stock had the highest drawdown last year?",
        "description": "Multi-entity comparison - FAANG stocks",
        "expected_type": "analysis",
        "expected_entities": ["FAANG"]  # Should expand to FB, AAPL, AMZN, NFLX, GOOGL
    },
    {
        "id": 7,
        "query": "If I invested $5,000 in Nvidia 2 years ago, what's it worth today?",
        "description": "Hypothetical investment scenario",
        "expected_type": "historical/analysis",
        "expected_entities": ["Nvidia"]
    },
    {
        "id": 8,
        "query": "Why did Nvidia gain today?",
        "description": "Reasoning query (testing incorrect assumption)",
        "expected_type": "analysis/price",
        "expected_entities": ["Nvidia"],
        "note": "NVDA actually dropped - testing how bot handles incorrect assumptions"
    },
    {
        "id": 9,
        "query": "How did the US market perform today?",
        "description": "Market overview - current day",
        "expected_type": "market",
        "expected_entities": []
    },
    {
        "id": 10,
        "query": "Give me the market update",
        "description": "General market overview",
        "expected_type": "market",
        "expected_entities": []
    }
]


def format_test_result(test_case: dict, response: dict, duration: float, error: Exception = None) -> dict:
    """Format test results for logging"""
    result = {
        "test_id": test_case["id"],
        "query": test_case["query"],
        "description": test_case["description"],
        "expected_type": test_case["expected_type"],
        "expected_entities": test_case["expected_entities"],
        "duration_seconds": round(duration, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if error:
        result["status"] = "ERROR"
        result["error"] = str(error)
        result["error_type"] = type(error).__name__
    else:
        result["status"] = "SUCCESS"
        result["response"] = {
            "answer": response.answer,
            "confidence": response.confidence,
            "data_timestamp": response.data_timestamp,
            "citations": [{"source": c.source, "url": c.url} for c in response.citations],
            "context": response.context
        }
    
    if "note" in test_case:
        result["note"] = test_case["note"]
    
    return result


async def run_single_test(test_case: dict) -> dict:
    """Run a single test case"""
    print(f"\n{'='*80}")
    print(f"TEST {test_case['id']}: {test_case['description']}")
    print(f"{'='*80}")
    print(f"Query: \"{test_case['query']}\"")
    print(f"Expected Type: {test_case['expected_type']}")
    print(f"Expected Entities: {test_case['expected_entities']}")
    if "note" in test_case:
        print(f"Note: {test_case['note']}")
    print()
    
    start_time = datetime.utcnow()
    
    try:
        response = await orchestrate_query(test_case["query"])
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Display results
        print(f"\n[SUCCESS] (took {duration:.2f}s)")
        print(f"\nAnswer Preview:")
        print("-" * 80)
        # Show first 500 chars of answer
        answer_preview = response.answer[:500] + "..." if len(response.answer) > 500 else response.answer
        print(answer_preview)
        print("-" * 80)
        print(f"\nConfidence: {response.confidence}")
        print(f"Citations: {len(response.citations)} source(s)")
        
        # Show context summary
        if response.context:
            print(f"\nContext Summary:")
            if "classification_confidence" in response.context:
                print(f"   Classification Confidence: {response.context['classification_confidence']}")
            if "entities" in response.context:
                print(f"   Entities: {response.context['entities']}")
            if "resolved_symbols" in response.context:
                print(f"   Resolved Symbols: {response.context['resolved_symbols']}")
            if "sources_used" in response.context:
                print(f"   Sources Used: {response.context['sources_used']}")
        
        return format_test_result(test_case, response, duration)
        
    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n[ERROR] (after {duration:.2f}s)")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        import traceback
        print(f"\nTraceback:")
        print(traceback.format_exc())
        
        return format_test_result(test_case, None, duration, e)


async def main():
    """Run all test cases and save results"""
    print("="*80)
    print("ORCHESTRATOR QUERY TEST SUITE")
    print("="*80)
    print(f"\nTotal Test Cases: {len(TEST_CASES)}")
    print(f"Start Time: {datetime.utcnow().isoformat()}")
    
    # Check API keys
    print("\n" + "-"*80)
    print("API Configuration:")
    print(f"   Mboum API Key: {'[SET]' if settings.mboum_api_key else '[MISSING]'}")
    print(f"   FMP API Key: {'[SET]' if settings.fmp_api_key else '[MISSING]'}")
    print(f"   Gemini API Key: {'[SET]' if settings.gemini_api_key else '[MISSING]'}")
    print("-"*80)
    
    if not all([settings.mboum_api_key, settings.fmp_api_key, settings.gemini_api_key]):
        print("\nWARNING: Some API keys are missing. Tests may fail.")
    
    # Run all tests
    results = []
    start_time = datetime.utcnow()
    
    for test_case in TEST_CASES:
        result = await run_single_test(test_case)
        results.append(result)
        
        # Brief pause between tests to avoid rate limiting
        await asyncio.sleep(1)
    
    end_time = datetime.utcnow()
    total_duration = (end_time - start_time).total_seconds()
    
    # Generate summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "ERROR")
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Successful: {successful} [PASS]")
    print(f"Failed: {failed} [FAIL]")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Average Duration: {total_duration/len(results):.2f}s per test")
    
    # Show individual test statuses
    print("\nIndividual Results:")
    for result in results:
        status_mark = "[PASS]" if result["status"] == "SUCCESS" else "[FAIL]"
        print(f"   {status_mark} Test {result['test_id']}: {result['description']} ({result['duration_seconds']}s)")
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"orchestrator_test_{timestamp}.json"
    
    log_data = {
        "test_suite": "Orchestrator Query Tests",
        "timestamp": datetime.utcnow().isoformat(),
        "total_duration_seconds": total_duration,
        "summary": {
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/len(results)*100):.1f}%"
        },
        "configuration": {
            "mboum_api_key_set": bool(settings.mboum_api_key),
            "fmp_api_key_set": bool(settings.fmp_api_key),
            "gemini_api_key_set": bool(settings.gemini_api_key)
        },
        "results": results
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[LOG] Full results saved to: {log_file}")
    
    # Also save a human-readable version
    txt_file = log_dir / f"orchestrator_test_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("ORCHESTRATOR QUERY TEST RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"\nTest Run: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Total Duration: {total_duration:.2f}s\n")
        f.write(f"Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)\n")
        f.write("\n")
        
        for result in results:
            f.write("\n" + "="*80 + "\n")
            f.write(f"TEST {result['test_id']}: {result['description']}\n")
            f.write("="*80 + "\n")
            f.write(f"Query: \"{result['query']}\"\n")
            f.write(f"Duration: {result['duration_seconds']}s\n")
            f.write(f"Status: {result['status']}\n")
            
            if result['status'] == 'SUCCESS':
                resp = result['response']
                f.write(f"\nConfidence: {resp['confidence']}\n")
                f.write(f"\nAnswer:\n{'-'*80}\n{resp['answer']}\n{'-'*80}\n")
                
                f.write(f"\nCitations ({len(resp['citations'])}):\n")
                for cite in resp['citations']:
                    f.write(f"   - {cite['source']}\n")
                
                if resp.get('context'):
                    ctx = resp['context']
                    f.write(f"\nContext Details:\n")
                    if 'classification_confidence' in ctx:
                        f.write(f"   Classification Confidence: {ctx['classification_confidence']}\n")
                    if 'entities' in ctx:
                        f.write(f"   Entities: {ctx['entities']}\n")
                    if 'resolved_symbols' in ctx:
                        f.write(f"   Resolved Symbols: {ctx['resolved_symbols']}\n")
                    if 'sources_used' in ctx:
                        f.write(f"   Sources Used: {ctx['sources_used']}\n")
            else:
                f.write(f"\nError: {result.get('error', 'Unknown error')}\n")
                f.write(f"Error Type: {result.get('error_type', 'Unknown')}\n")
            
            if 'note' in result:
                f.write(f"\n⚠️  Note: {result['note']}\n")
            
            f.write("\n")
    
    print(f"[LOG] Human-readable results saved to: {txt_file}")
    
    # Final status
    print("\n" + "="*80)
    if successful == len(results):
        print("ALL TESTS PASSED!")
    else:
        print(f"WARNING: {failed} TEST(S) FAILED - Review logs for details")
    print("="*80)
    
    return successful == len(results)


if __name__ == "__main__":
    print("\nStarting Orchestrator Query Test Suite...\n")
    success = asyncio.run(main())
    exit(0 if success else 1)

