# Query Classifier Guide

## Overview

The rule-based query classifier routes user queries to appropriate data sources:
- **Mboum/FMP APIs** for structured data (prices, fundamentals)
- **RAG** for unstructured data (news, articles)

## Query Types

| Type | Description | Data Source | Example |
|------|-------------|-------------|---------|
| **PRICE** | Real-time stock prices | Mboum API | "What's NVDA price?" |
| **HISTORICAL** | Past price data | FMP API | "NVDA price last month" |
| **FUNDAMENTALS** | Financial statements | FMP API | "NVDA quarterly earnings" |
| **NEWS** | News articles | RAG | "Latest NVDA news" |
| **MARKET** | Market data | FMP API | "How's the tech sector?" |
| **ANALYSIS** | Investment analysis | Multiple sources | "Should I buy NVDA?" |

## Usage

### In Your Code

```python
from app.core.query_classifier import get_classifier

# Get classifier instance
classifier = get_classifier()

# Classify a query
result = classifier.classify("What's NVDA price?")

# Check results
print(result.query_types)  # [QueryType.PRICE]
print(result.confidence)    # "high"
print(result.matched_patterns)  # ["price:price"]
```

### Interactive Testing

Test queries interactively:

```bash
python scripts/test_classifier.py
```

### Running Tests

```bash
# Run all classifier tests
pytest tests/test_classifier.py -v

# Run demo
python tests/test_classifier.py
```

## How It Works

### 1. Pattern Matching

The classifier uses keyword patterns to identify query types:

```python
PATTERNS = {
    QueryType.PRICE: {
        'price', 'trading at', 'worth', 'cost', ...
    },
    QueryType.NEWS: {
        'news', 'latest', 'recent', 'headline', ...
    },
    # ... more patterns
}
```

### 2. Multi-Type Detection

Queries can match multiple types:

```
"NVDA price and recent news"
→ [QueryType.PRICE, QueryType.NEWS]
→ Calls both Mboum API and RAG
```

### 3. Confidence Scoring

```
HIGH   - Explicit patterns matched ("price?", "latest news")
MEDIUM - Some patterns matched, or multiple types
LOW    - No clear patterns, using default
```

## Adding New Patterns

### Method 1: Update the Code

Edit `app/core/query_classifier.py`:

```python
PATTERNS = {
    QueryType.PRICE: {
        'price',
        'trading at',
        # Add your new patterns here:
        'how expensive',
        'how much does it cost',
    }
}
```

### Method 2: Add Dynamically

```python
classifier = get_classifier()
classifier.add_pattern(QueryType.PRICE, "how expensive")
```

## Common Query Patterns

### Price Queries
```
✅ "What's NVDA price?"
✅ "How much is AAPL?"
✅ "MSFT trading at?"
✅ "Current value of GOOGL"
```

### Historical Queries
```
✅ "NVDA price last month"
✅ "Show me AAPL performance over the year"
✅ "Historical chart for TSLA"
✅ "How did MSFT do in 2023?"
```

### Fundamentals Queries
```
✅ "What is NVDA revenue?"
✅ "AAPL quarterly earnings"
✅ "Show me MSFT P/E ratio"
✅ "GOOGL balance sheet"
```

### News Queries
```
✅ "Latest NVDA news"
✅ "Recent headlines for AAPL"
✅ "What's happening with TSLA?"
✅ "Any announcements from MSFT?"
```

### Hybrid Queries
```
✅ "NVDA price and recent news"
✅ "Tell me about AAPL earnings and stock performance"
✅ "Should I buy MSFT based on recent news?"
```

## Monitoring & Improvement

### Get Classification Stats

```python
stats = classifier.get_classification_stats()

print(f"Total: {stats['total_classifications']}")
print(f"Confidence: {stats['confidence_distribution']}")
print(f"Types: {stats['query_type_distribution']}")
```

### Continuous Improvement

1. **Monitor real queries** in production
2. **Identify misclassifications** from logs
3. **Add new patterns** for common queries
4. **Test changes** with test suite
5. **Deploy and repeat**

Example workflow:

```python
# 1. User queries not being classified correctly
user_query = "How costly is NVDA?"

# 2. Classify and check
result = classifier.classify(user_query)
# → Default to PRICE, but low confidence

# 3. Add missing pattern
classifier.add_pattern(QueryType.PRICE, "how costly")

# 4. Test again
result = classifier.classify(user_query)
# → PRICE with high confidence ✅
```

## Best Practices

### ✅ DO:
- Keep patterns simple and clear
- Test new patterns before deploying
- Monitor classification confidence in production
- Add patterns based on real user queries
- Use the interactive tester to experiment

### ❌ DON'T:
- Don't make patterns too specific ("nvda price?" won't match "AAPL price?")
- Don't overlap patterns between types (causes confusion)
- Don't forget to test after adding patterns
- Don't hardcode ticker symbols in patterns

## Troubleshooting

### Query gets wrong classification

**Problem**: "Tell me about NVDA" → defaults to PRICE

**Solution**: This is expected! Ambiguous queries default to PRICE. Users should be more specific, or you can add patterns:

```python
classifier.add_pattern(QueryType.ANALYSIS, "tell me about")
```

### Query matches too many types

**Problem**: "NVDA news today" → [PRICE, NEWS]

**Check**: If "today" is in PRICE patterns, remove it:

```python
# Before: QueryType.PRICE has 'today' keyword
# After: Move 'today' to NEWS patterns only
```

### Low confidence on clear queries

**Problem**: "What's the price?" → Low confidence

**Solution**: Add to HIGH_CONFIDENCE_PATTERNS:

```python
HIGH_CONFIDENCE_PATTERNS = {
    QueryType.PRICE: {
        'price?',
        'what is the price',
        'current price',
        "what's the price",  # Add this
    }
}
```

## Future Enhancements

When you need more sophisticated classification:

1. **LLM-based classification** for ambiguous queries
2. **Ticker extraction** improvements
3. **Context-aware** classification (conversation history)
4. **Multi-language** support
5. **Fuzzy matching** for typos

For now, rule-based classification is:
- ✅ Fast (~1ms)
- ✅ Free ($0/query)
- ✅ Good enough for 80-90% of queries
- ✅ Easy to improve over time

---

## Quick Reference

```python
from app.core.query_classifier import get_classifier, QueryType

# Get classifier
classifier = get_classifier()

# Classify
result = classifier.classify("Your query here")

# Check results
result.query_types      # List[QueryType]
result.confidence       # "high" | "medium" | "low"
result.matched_patterns # List[str]

# Add pattern
classifier.add_pattern(QueryType.PRICE, "new keyword")

# Get stats
stats = classifier.get_classification_stats()
```

