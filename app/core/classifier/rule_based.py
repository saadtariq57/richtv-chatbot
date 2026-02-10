"""
Rule-Based Query Classifier

Implements keyword-based pattern matching for query classification.
Fast, predictable, and cost-free classification.
"""

from typing import List, Set, Dict, Optional, Tuple
from app.core.classifier.types import QueryType, ClassificationResult
from app.core.classifier.patterns import QueryPatterns
from app.llm.generator import classify_and_answer_if_general


class RuleBasedClassifier:
    """
    Rule-based query classifier using keyword pattern matching.
    
    Features:
    - Fast classification (~1ms)
    - Zero cost per query
    - Predictable results
    - Easy to debug and improve
    - Multi-type detection for hybrid queries
    """
    
    def __init__(self):
        """Initialize classifier."""
        self.patterns = QueryPatterns()
        self.classification_log: List[Dict] = []  # For monitoring/improvement
    
    def classify(self, query: str) -> ClassificationResult:
        """
        Classify a user query into one or more query types.
        
        Args:
            query: User's question/query
            
        Returns:
            ClassificationResult with detected types and confidence
        """
        if not query or not query.strip():
            return ClassificationResult(
                query_types=[QueryType.PRICE],  # Default
                confidence="low",
                matched_patterns=[]
            )
        
        query_lower = query.lower().strip()
        
        # Find matching query types
        matches = self._find_matches(query_lower)
        
        # Determine confidence
        confidence = self._calculate_confidence(query_lower, matches)
        
        # Get matched patterns for logging/debugging
        matched_patterns = self._get_matched_patterns(query_lower, matches)
        
        # Sort by relevance (priority order)
        sorted_types = self._sort_by_priority(matches)
        
        # If no matches, use LLM to classify and potentially answer
        llm_answer = None
        llm_ticker = None
        if not sorted_types:
            classification, answer, ticker = classify_and_answer_if_general(query)
            
            if classification == "general":
                # It's a general question, LLM has answered it
                sorted_types = [QueryType.GENERAL]
                confidence = "medium"  # LLM-assisted
                llm_answer = answer
                matched_patterns.append("llm:general")
                
            elif classification == "specific":
                # It's about a specific stock
                sorted_types = [QueryType.PRICE]
                confidence = "medium"  # LLM-assisted
                llm_ticker = ticker
                matched_patterns.append(f"llm:specific:{ticker}")
                
            else:  # unclear
                # Can't classify, default to PRICE with low confidence
                sorted_types = [QueryType.PRICE]
                confidence = "low"
                matched_patterns.append("llm:unclear")
        
        result = ClassificationResult(
            query_types=sorted_types,
            confidence=confidence,
            matched_patterns=matched_patterns,
            llm_answer=llm_answer,
            llm_ticker=llm_ticker
        )
        
        # Log for analysis
        self._log_classification(query, result)
        
        return result
    
    def _find_matches(self, query_lower: str) -> Set[QueryType]:
        """
        Find all query types that match the query.
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Set of matching query types
        """
        matches = set()
        
        for query_type, patterns in self.patterns.PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    matches.add(query_type)
                    break  # One match per type is enough
        
        return matches
    
    def _calculate_confidence(self, query_lower: str, matches: Set[QueryType]) -> str:
        """
        Calculate confidence level based on pattern matches.
        
        Confidence levels:
        - high: Explicit, clear patterns matched
        - medium: Some patterns matched, or multiple types (ambiguous)
        - low: No clear patterns, using default
        
        Args:
            query_lower: Lowercase query string
            matches: Set of matched query types
            
        Returns:
            Confidence level string
        """
        if not matches:
            return "low"
        
        # Check for high-confidence patterns
        for query_type in matches:
            high_conf_patterns = self.patterns.get_high_confidence_patterns(query_type)
            if any(pattern in query_lower for pattern in high_conf_patterns):
                return "high"
        
        # Multiple matches = medium confidence (ambiguous)
        if len(matches) > 2:
            return "medium"
        
        # Single clear match = high confidence
        if len(matches) == 1:
            return "high"
        
        return "medium"
    
    def _get_matched_patterns(self, query_lower: str, matches: Set[QueryType]) -> List[str]:
        """
        Get list of actual patterns that matched.
        
        Useful for debugging and understanding classification decisions.
        
        Args:
            query_lower: Lowercase query string
            matches: Set of matched query types
            
        Returns:
            List of matched patterns in "type:pattern" format
        """
        matched = []
        
        for query_type in matches:
            patterns = self.patterns.get_patterns(query_type)
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    matched.append(f"{query_type.value}:{pattern}")
        
        return matched
    
    def _sort_by_priority(self, matches: Set[QueryType]) -> List[QueryType]:
        """
        Sort query types by priority for execution.
        
        Priority order (most important first):
        1. PRICE - Most common, users want real-time data
        2. FUNDAMENTALS - Financial data
        3. HISTORICAL - Past data
        4. NEWS - Text/narrative
        5. MARKET - Market context
        6. ANALYSIS - Requires all others
        
        Args:
            matches: Set of matched query types
            
        Returns:
            Sorted list of query types
        """
        priority = [
            QueryType.PRICE,
            QueryType.FUNDAMENTALS,
            QueryType.HISTORICAL,
            QueryType.NEWS,
            QueryType.MARKET,
            QueryType.ANALYSIS
        ]
        
        return [qt for qt in priority if qt in matches]
    
    def _log_classification(self, query: str, result: ClassificationResult) -> None:
        """
        Log classification for monitoring and improvement.
        
        Args:
            query: Original query
            result: Classification result
        """
        self.classification_log.append({
            "query": query,
            "result": result
        })
    
    def add_pattern(self, query_type: QueryType, pattern: str) -> None:
        """
        Dynamically add a new pattern.
        
        Useful for continuous improvement based on real user queries.
        
        Args:
            query_type: Query type to add pattern to
            pattern: Pattern string to add
        
        Example:
            classifier.add_pattern(QueryType.PRICE, "how expensive")
        """
        self.patterns.add_pattern(query_type, pattern)
    
    def get_classification_stats(self) -> Dict:
        """
        Get statistics about classifications for monitoring.
        
        Returns:
            Dictionary with classification statistics
        """
        if not self.classification_log:
            return {}
        
        total = len(self.classification_log)
        confidence_counts = {
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        type_counts = {qt: 0 for qt in QueryType}
        
        for log_entry in self.classification_log:
            result = log_entry["result"]
            confidence_counts[result.confidence] += 1
            for qt in result.query_types:
                type_counts[qt] += 1
        
        return {
            "total_classifications": total,
            "confidence_distribution": confidence_counts,
            "query_type_distribution": {
                qt.value: count for qt, count in type_counts.items()
            },
            "avg_types_per_query": sum(
                len(log["result"].query_types) 
                for log in self.classification_log
            ) / total
        }
    
    def clear_logs(self) -> None:
        """Clear classification logs."""
        self.classification_log.clear()

