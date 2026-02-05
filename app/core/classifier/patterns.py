"""
Query Classification Patterns

Keyword patterns for rule-based query classification.
Add new patterns here as you learn from real user queries.
"""

from typing import Dict, Set
from app.core.classifier.types import QueryType


class QueryPatterns:
    """
    Container for all query classification patterns.
    
    Organized by query type with high-confidence patterns separated.
    """
    
    # Main patterns for each query type
    PATTERNS: Dict[QueryType, Set[str]] = {
        QueryType.PRICE: {
            # Direct price questions
            'price', 'trading at', 'worth', 'cost', 'value',
            'current price', 'stock price', 'how much',
            'quote', 'ticker price', 'share price',
            # Price-related verbs
            'priced at', 'valued at', 'trading',
            # Variations
            '$', 'dollar', 'valuation'
        },
        
        QueryType.HISTORICAL: {
            # Time references
            'last week', 'last month', 'last year', 'yesterday',
            'past week', 'past month', 'past year',
            'historical', 'history', 'previous',
            # Ago references
            'ago', 'before', 'earlier',
            # Specific timeframes
            'ytd', 'year to date', '52 week', 'annual',
            # Chart/graph related
            'chart', 'graph', 'performance over'
        },
        
        QueryType.FUNDAMENTALS: {
            # Financial metrics
            'revenue', 'earnings', 'profit', 'loss',
            'eps', 'earnings per share',
            'p/e ratio', 'pe ratio', 'price to earnings',
            'market cap', 'market capitalization',
            # Financial statements
            'income statement', 'balance sheet', 'cash flow',
            'quarterly report', 'annual report',
            'financial', 'financials',
            # Growth metrics
            'growth rate', 'revenue growth', 'margin',
            'debt', 'assets', 'liabilities'
        },
        
        QueryType.NEWS: {
            # News keywords
            'news', 'latest', 'recent', 'update', 'updates',
            'headline', 'headlines', 'article', 'articles',
            # Announcements
            'announcement', 'announced', 'press release',
            'statement', 'report says', 'according to',
            # Events
            'what happened', 'happening', 'going on',
            'event', 'development', 'situation',
            # Temporal news
            'today', 'this week', 'this month',
            'breaking', 'just', 'now'
        },
        
        QueryType.MARKET: {
            # Market indicators
            'market', 'sector', 'industry',
            'index', 'sp500', 's&p 500', 'dow jones', 'nasdaq',
            'bull market', 'bear market',
            # Market movements
            'trending', 'gainers', 'losers',
            'volume', 'trading volume',
            'volatility', 'sentiment'
        },
        
        QueryType.ANALYSIS: {
            # Investment questions
            'should i buy', 'should i sell', 'should i invest',
            'recommend', 'recommendation', 'advice',
            'opinion', 'think', 'outlook',
            # Analysis keywords
            'analysis', 'analyze', 'evaluate', 'assess',
            'forecast', 'predict', 'expect',
            'good investment', 'bad investment',
            'undervalued', 'overvalued',
            'buy or sell', 'hold or sell'
        }
    }
    
    # High-confidence patterns (when these match, we're very confident)
    HIGH_CONFIDENCE_PATTERNS: Dict[QueryType, Set[str]] = {
        QueryType.PRICE: {
            'price?',
            'what is the price',
            'current price',
            'trading at'
        },
        QueryType.NEWS: {
            'latest news',
            'recent news',
            'news about'
        },
        QueryType.FUNDAMENTALS: {
            'revenue',
            'earnings report',
            'quarterly earnings'
        },
        QueryType.HISTORICAL: {
            'historical price',
            'price history',
            'past performance'
        }
    }
    
    @classmethod
    def add_pattern(cls, query_type: QueryType, pattern: str) -> None:
        """
        Add a new pattern to a query type.
        
        Args:
            query_type: The query type to add pattern to
            pattern: The pattern string to add
        
        Example:
            QueryPatterns.add_pattern(QueryType.PRICE, "how expensive")
        """
        cls.PATTERNS[query_type].add(pattern.lower())
    
    @classmethod
    def add_high_confidence_pattern(cls, query_type: QueryType, pattern: str) -> None:
        """
        Add a new high-confidence pattern.
        
        Args:
            query_type: The query type to add pattern to
            pattern: The pattern string to add
        """
        if query_type not in cls.HIGH_CONFIDENCE_PATTERNS:
            cls.HIGH_CONFIDENCE_PATTERNS[query_type] = set()
        cls.HIGH_CONFIDENCE_PATTERNS[query_type].add(pattern.lower())
    
    @classmethod
    def get_patterns(cls, query_type: QueryType) -> Set[str]:
        """Get all patterns for a specific query type."""
        return cls.PATTERNS.get(query_type, set())
    
    @classmethod
    def get_high_confidence_patterns(cls, query_type: QueryType) -> Set[str]:
        """Get high-confidence patterns for a specific query type."""
        return cls.HIGH_CONFIDENCE_PATTERNS.get(query_type, set())
    
    @classmethod
    def get_all_patterns(cls) -> Dict[QueryType, Set[str]]:
        """Get all patterns for all query types."""
        return cls.PATTERNS.copy()
    
    @classmethod
    def pattern_count(cls) -> Dict[QueryType, int]:
        """Get count of patterns per query type."""
        return {qt: len(patterns) for qt, patterns in cls.PATTERNS.items()}

