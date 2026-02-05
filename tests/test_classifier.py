"""
Tests for the rule-based query classifier
"""

import pytest
from app.core.classifier import RuleBasedClassifier, QueryType


class TestQueryClassifier:
    """Test suite for query classification."""
    
    def setup_method(self):
        """Setup classifier for each test."""
        self.classifier = RuleBasedClassifier()
    
    # Price queries
    def test_price_query_simple(self):
        """Test simple price queries."""
        queries = [
            "What is the price of NVDA?",
            "How much is NVDA worth?",
            "NVDA stock price?",
            "What's NVDA trading at?"
        ]
        
        for query in queries:
            result = self.classifier.classify(query)
            assert QueryType.PRICE in result.query_types
            assert result.confidence in ["high", "medium"]
    
    # Historical queries
    def test_historical_query(self):
        """Test historical data queries."""
        queries = [
            "What was NVDA price last month?",
            "NVDA price history",
            "Show me NVDA performance over the last year",
            "Historical data for NVDA"
        ]
        
        for query in queries:
            result = self.classifier.classify(query)
            assert QueryType.HISTORICAL in result.query_types
    
    # Fundamentals queries
    def test_fundamentals_query(self):
        """Test financial fundamentals queries."""
        queries = [
            "What is NVDA revenue?",
            "NVDA earnings report",
            "Show me NVDA quarterly earnings",
            "What's NVDA P/E ratio?"
        ]
        
        for query in queries:
            result = self.classifier.classify(query)
            assert QueryType.FUNDAMENTALS in result.query_types
    
    # News queries
    def test_news_query(self):
        """Test news-related queries."""
        queries = [
            "Latest NVDA news",
            "What's the news about NVDA?",
            "Recent headlines for NVDA",
            "NVDA announcements"
        ]
        
        for query in queries:
            result = self.classifier.classify(query)
            assert QueryType.NEWS in result.query_types
    
    # Analysis queries
    def test_analysis_query(self):
        """Test investment analysis queries."""
        queries = [
            "Should I buy NVDA?",
            "Is NVDA a good investment?",
            "What's your opinion on NVDA?",
            "NVDA investment recommendation"
        ]
        
        for query in queries:
            result = self.classifier.classify(query)
            assert QueryType.ANALYSIS in result.query_types
    
    # Hybrid queries (multiple types)
    def test_hybrid_query(self):
        """Test queries that need multiple data sources."""
        query = "What's NVDA price and recent news?"
        result = self.classifier.classify(query)
        
        assert QueryType.PRICE in result.query_types
        assert QueryType.NEWS in result.query_types
        assert len(result.query_types) >= 2
    
    # Edge cases
    def test_empty_query(self):
        """Test empty query handling."""
        result = self.classifier.classify("")
        assert QueryType.PRICE in result.query_types  # Default
        assert result.confidence == "low"
    
    def test_ambiguous_query(self):
        """Test ambiguous queries."""
        query = "Tell me about NVDA"  # Could be anything
        result = self.classifier.classify(query)
        # Should return something (default to PRICE)
        assert len(result.query_types) > 0
    
    # Pattern matching
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        queries = [
            "WHAT IS THE PRICE OF NVDA?",
            "what is the price of nvda?",
            "What Is The Price Of NVDA?"
        ]
        
        for query in queries:
            result = self.classifier.classify(query)
            assert QueryType.PRICE in result.query_types
    
    # Confidence levels
    def test_high_confidence_patterns(self):
        """Test high-confidence pattern matching."""
        query = "What is the price?"
        result = self.classifier.classify(query)
        assert result.confidence == "high"
    
    def test_add_pattern_dynamically(self):
        """Test adding new patterns at runtime."""
        classifier = RuleBasedClassifier()
        
        # Add custom pattern
        classifier.add_pattern(QueryType.PRICE, "how expensive")
        
        # Test it works
        result = classifier.classify("How expensive is NVDA?")
        assert QueryType.PRICE in result.query_types


# Manual testing function
def demo_classifier():
    """
    Demo function to test classifier with various queries.
    Run: python -m pytest tests/test_classifier.py::demo_classifier -v -s
    """
    classifier = RuleBasedClassifier()
    
    test_queries = [
        "What's NVDA price?",
        "Show me NVDA earnings",
        "Latest news on NVDA",
        "NVDA price last month",
        "Should I buy NVDA?",
        "What's NVDA worth and recent news?",
        "Tell me about NVDA",
        "NVDA market cap",
        "How's the tech sector doing?",
    ]
    
    print("\n" + "="*60)
    print("🧪 QUERY CLASSIFIER DEMO")
    print("="*60 + "\n")
    
    for query in test_queries:
        result = classifier.classify(query)
        
        print(f"Query: \"{query}\"")
        print(f"  ├─ Types: {[qt.value for qt in result.query_types]}")
        print(f"  ├─ Confidence: {result.confidence}")
        print(f"  └─ Patterns: {result.matched_patterns[:3]}")  # Show first 3
        print()
    
    # Show stats
    stats = classifier.get_classification_stats()
    print("\n" + "="*60)
    print("📊 CLASSIFICATION STATISTICS")
    print("="*60)
    print(f"Total queries: {stats['total_classifications']}")
    print(f"Confidence distribution: {stats['confidence_distribution']}")
    print(f"Type distribution: {stats['query_type_distribution']}")
    print(f"Avg types per query: {stats['avg_types_per_query']:.2f}")
    print()


if __name__ == "__main__":
    # Run demo
    demo_classifier()

