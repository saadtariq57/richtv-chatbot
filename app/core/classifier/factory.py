"""
Classifier Factory

Manages classifier instances using singleton pattern.
"""

from typing import Optional
from app.core.classifier.rule_based import RuleBasedClassifier


class ClassifierFactory:
    """
    Factory for creating and managing classifier instances.
    
    Uses singleton pattern to ensure only one classifier instance exists.
    """
    
    _instance: Optional[RuleBasedClassifier] = None
    
    @classmethod
    def get_classifier(cls) -> RuleBasedClassifier:
        """
        Get the global classifier instance.
        
        Creates a new instance if one doesn't exist yet.
        
        Returns:
            RuleBasedClassifier instance
        """
        if cls._instance is None:
            cls._instance = RuleBasedClassifier()
        return cls._instance
    
    @classmethod
    def reset_classifier(cls) -> None:
        """
        Reset the classifier instance.
        
        Useful for testing or when you want to clear classification logs.
        """
        cls._instance = None
    
    @classmethod
    def create_new_classifier(cls) -> RuleBasedClassifier:
        """
        Create a new classifier instance without affecting the singleton.
        
        Useful for testing or when you need multiple independent classifiers.
        
        Returns:
            New RuleBasedClassifier instance
        """
        return RuleBasedClassifier()

