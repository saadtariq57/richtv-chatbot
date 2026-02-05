"""
Query Classifier Module

Rule-based query classification for routing to appropriate data sources.

Public API:
    - QueryType: Enum of query types
    - ClassificationResult: Result of classification
    - get_classifier(): Get classifier instance
    - RuleBasedClassifier: Main classifier class

Usage:
    from app.core.classifier import get_classifier, QueryType
    
    classifier = get_classifier()
    result = classifier.classify("What's NVDA price?")
    
    print(result.query_types)  # [QueryType.PRICE]
    print(result.confidence)   # "high"
"""

from app.core.classifier.types import QueryType, ClassificationResult
from app.core.classifier.patterns import QueryPatterns
from app.core.classifier.rule_based import RuleBasedClassifier
from app.core.classifier.factory import ClassifierFactory

# Public API
__all__ = [
    # Main function
    'get_classifier',
    
    # Types
    'QueryType',
    'ClassificationResult',
    
    # Classes
    'RuleBasedClassifier',
    'QueryPatterns',
    'ClassifierFactory',
]

# Convenience function for most common use case
def get_classifier() -> RuleBasedClassifier:
    """
    Get the global classifier instance.
    
    This is the main entry point for using the classifier.
    
    Returns:
        RuleBasedClassifier instance
    
    Example:
        >>> from app.core.classifier import get_classifier
        >>> classifier = get_classifier()
        >>> result = classifier.classify("What's NVDA price?")
        >>> print(result.query_types)
        [<QueryType.PRICE: 'price'>]
    """
    return ClassifierFactory.get_classifier()

