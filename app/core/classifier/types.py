"""
Query Classification Types

Defines enums and data structures for query classification.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List


class QueryType(Enum):
    """
    Query types mapped to data sources.
    
    Each type corresponds to a specific data source or combination:
    - PRICE: Real-time stock prices (Mboum API)
    - HISTORICAL: Historical price data (FMP API)
    - FUNDAMENTALS: Financial statements and metrics (FMP API)
    - NEWS: News articles and press releases (RAG)
    - MARKET: Market-wide data and indices (Mboum API - same endpoint as PRICE)
    - ANALYSIS: Investment analysis requiring multiple sources
    """
    PRICE = "price"
    HISTORICAL = "historical"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    MARKET = "market"
    ANALYSIS = "analysis"
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    @property
    def data_source(self) -> str:
        """Get the primary data source for this query type."""
        source_mapping = {
            QueryType.PRICE: "Mboum API",
            QueryType.HISTORICAL: "FMP Historical API",
            QueryType.FUNDAMENTALS: "FMP Fundamentals API",
            QueryType.NEWS: "RAG Vector Store",
            QueryType.MARKET: "Mboum API",
            QueryType.ANALYSIS: "Multiple Sources"
        }
        return source_mapping.get(self, "Unknown")


@dataclass
class ClassificationResult:
    """
    Result of query classification.
    
    Attributes:
        query_types: List of detected query types (can be multiple)
        confidence: Confidence level - "high", "medium", or "low"
        matched_patterns: List of patterns that matched (for debugging)
    """
    query_types: List[QueryType]
    confidence: str  # "high" | "medium" | "low"
    matched_patterns: List[str]
    
    def __str__(self) -> str:
        """Human-readable representation."""
        types_str = ", ".join([qt.value for qt in self.query_types])
        return f"ClassificationResult(types=[{types_str}], confidence={self.confidence})"
    
    @property
    def primary_type(self) -> QueryType:
        """Get the primary (first) query type."""
        return self.query_types[0] if self.query_types else QueryType.PRICE
    
    @property
    def is_hybrid(self) -> bool:
        """Check if query requires multiple data sources."""
        return len(self.query_types) > 1
    
    @property
    def data_sources(self) -> List[str]:
        """Get list of data sources needed."""
        return [qt.data_source for qt in self.query_types]

