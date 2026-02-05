"""
Query Classifier - Backward Compatibility Layer

DEPRECATED: This module is deprecated. Use app.core.classifier instead.

This module now redirects to the new modularized classifier structure.
Kept for backward compatibility with existing imports.

New imports:
    from app.core.classifier import get_classifier, QueryType, ClassificationResult

Old imports (still work):
    from app.core.query_classifier import get_classifier, QueryType, ClassificationResult
"""

import warnings

# Import from new modular structure
from app.core.classifier import (
    QueryType,
    ClassificationResult,
    RuleBasedClassifier,
    QueryPatterns,
    get_classifier as _get_classifier
)

# Show deprecation warning
warnings.warn(
    "app.core.query_classifier is deprecated. Use app.core.classifier instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything for backward compatibility
__all__ = [
    'QueryType',
    'ClassificationResult',
    'RuleBasedClassifier',
    'QueryPatterns',
    'get_classifier',
]


def get_classifier() -> RuleBasedClassifier:
    """
    Get the global classifier instance.
    
    DEPRECATED: Import from app.core.classifier instead.
    
    Returns:
        RuleBasedClassifier instance
    """
    return _get_classifier()
