## Query Classifier - Modular Structure

### Overview

The query classifier has been refactored into a clean, modular structure for better maintainability and extensibility.

---

## 📁 Module Structure

```
app/core/classifier/
├── __init__.py           # Public API & exports
├── types.py              # Enums & dataclasses
├── patterns.py           # Pattern definitions
├── rule_based.py         # Classifier implementation
└── factory.py            # Singleton management
```

---

## 📦 Module Breakdown

### **1. `types.py`** - Type Definitions

**Purpose**: Defines enums and data structures

**Contains**:
- `QueryType` enum (PRICE, HISTORICAL, FUNDAMENTALS, NEWS, MARKET, ANALYSIS)
- `ClassificationResult` dataclass

**Example**:
```python
from app.core.classifier.types import QueryType, ClassificationResult

# Query types
print(QueryType.PRICE.value)  # "price"
print(QueryType.PRICE.data_source)  # "Mboum API"

# Classification result
result = ClassificationResult(
    query_types=[QueryType.PRICE],
    confidence="high",
    matched_patterns=["price:price"]
)
print(result.is_hybrid)  # False
print(result.data_sources)  # ["Mboum API"]
```

---

### **2. `patterns.py`** - Pattern Management

**Purpose**: Manages all keyword patterns for classification

**Contains**:
- `QueryPatterns` class with all pattern dictionaries
- Methods to add/modify patterns

**Example**:
```python
from app.core.classifier.patterns import QueryPatterns
from app.core.classifier.types import QueryType

# Get patterns
patterns = QueryPatterns.get_patterns(QueryType.PRICE)
print(len(patterns))  # 15+ patterns

# Add new pattern
QueryPatterns.add_pattern(QueryType.PRICE, "how expensive")

# Get pattern count
counts = QueryPatterns.pattern_count()
print(counts)  # {QueryType.PRICE: 16, ...}
```

---

### **3. `rule_based.py`** - Classifier Logic

**Purpose**: Core classification implementation

**Contains**:
- `RuleBasedClassifier` class
- Pattern matching logic
- Confidence calculation
- Statistics tracking

**Example**:
```python
from app.core.classifier.rule_based import RuleBasedClassifier

classifier = RuleBasedClassifier()

# Classify
result = classifier.classify("What's NVDA price?")
print(result.query_types)  # [QueryType.PRICE]
print(result.confidence)   # "high"

# Add pattern dynamically
classifier.add_pattern(QueryType.PRICE, "how costly")

# Get stats
stats = classifier.get_classification_stats()
print(stats['total_classifications'])
```

---

### **4. `factory.py`** - Instance Management

**Purpose**: Singleton pattern for classifier instances

**Contains**:
- `ClassifierFactory` class
- Global instance management

**Example**:
```python
from app.core.classifier.factory import ClassifierFactory

# Get singleton
classifier1 = ClassifierFactory.get_classifier()
classifier2 = ClassifierFactory.get_classifier()
assert classifier1 is classifier2  # Same instance ✅

# Create independent instance
independent = ClassifierFactory.create_new_classifier()
assert independent is not classifier1  # Different instance ✅

# Reset singleton
ClassifierFactory.reset_classifier()
```

---

### **5. `__init__.py`** - Public API

**Purpose**: Clean public interface

**Exports**:
- `get_classifier()` - Main entry point
- `QueryType` - Query type enum
- `ClassificationResult` - Result type
- All classes for advanced usage

**Example**:
```python
# Simple usage (recommended)
from app.core.classifier import get_classifier, QueryType

classifier = get_classifier()
result = classifier.classify("What's NVDA price?")

# Advanced usage
from app.core.classifier import (
    RuleBasedClassifier,
    QueryPatterns,
    ClassifierFactory
)
```

---

## 🔄 Migration Guide

### Old Code (Single File)

```python
# Old import
from app.core.query_classifier import get_classifier, QueryType

classifier = get_classifier()
result = classifier.classify("What's NVDA price?")
```

### New Code (Modular)

```python
# New import (just change the module name!)
from app.core.classifier import get_classifier, QueryType

classifier = get_classifier()
result = classifier.classify("What's NVDA price?")
```

**Note**: Old imports still work! Backward compatibility layer redirects to new structure.

---

## 🎯 Benefits of Modular Structure

### **1. Separation of Concerns**
- Types in one file
- Patterns in another
- Logic separate from data
- Easy to find and modify specific parts

### **2. Better Maintainability**
```
Want to add patterns? → Edit patterns.py
Want to change logic? → Edit rule_based.py
Want new query type? → Edit types.py, then patterns.py
```

### **3. Easier Testing**
```python
# Test just patterns
from app.core.classifier.patterns import QueryPatterns
# Test just classification logic
from app.core.classifier.rule_based import RuleBasedClassifier
# Test just types
from app.core.classifier.types import QueryType
```

### **4. Extensibility**
Easy to add new classifier types:
```
app/core/classifier/
├── rule_based.py      # Current
├── ml_based.py        # Future: ML classifier
├── llm_based.py       # Future: LLM classifier
└── hybrid.py          # Future: Hybrid approach
```

### **5. Clear Dependencies**
```
types.py (no dependencies)
   ↓
patterns.py (depends on types)
   ↓
rule_based.py (depends on types, patterns)
   ↓
factory.py (depends on rule_based)
   ↓
__init__.py (exports everything)
```

---

## 📝 Usage Examples

### Basic Classification
```python
from app.core.classifier import get_classifier

classifier = get_classifier()
result = classifier.classify("What's NVDA price and recent news?")

print(result.query_types)  # [QueryType.PRICE, QueryType.NEWS]
print(result.confidence)   # "high"
print(result.is_hybrid)    # True
print(result.data_sources)  # ["Mboum API", "RAG Vector Store"]
```

### Adding Custom Patterns
```python
from app.core.classifier import get_classifier, QueryType

classifier = get_classifier()

# Add new pattern
classifier.add_pattern(QueryType.PRICE, "how expensive")

# Test it
result = classifier.classify("How expensive is NVDA?")
assert QueryType.PRICE in result.query_types  # ✅
```

### Monitoring Classifications
```python
from app.core.classifier import get_classifier

classifier = get_classifier()

# Classify some queries
classifier.classify("NVDA price?")
classifier.classify("AAPL news?")
classifier.classify("Should I buy MSFT?")

# Get statistics
stats = classifier.get_classification_stats()

print(f"Total: {stats['total_classifications']}")
print(f"Confidence: {stats['confidence_distribution']}")
print(f"Types: {stats['query_type_distribution']}")
```

### Advanced: Custom Classifier Instance
```python
from app.core.classifier import RuleBasedClassifier, QueryPatterns, QueryType

# Create independent classifier
my_classifier = RuleBasedClassifier()

# Customize patterns
my_classifier.add_pattern(QueryType.PRICE, "my custom pattern")

# Use it
result = my_classifier.classify("my custom query")
```

---

## 🔧 Extending the Module

### Adding a New Query Type

**1. Add to `types.py`:**
```python
class QueryType(Enum):
    PRICE = "price"
    # ... existing types ...
    TECHNICAL_ANALYSIS = "technical_analysis"  # New!
```

**2. Add patterns to `patterns.py`:**
```python
PATTERNS = {
    # ... existing patterns ...
    QueryType.TECHNICAL_ANALYSIS: {
        'rsi', 'macd', 'moving average',
        'support', 'resistance', 'chart pattern'
    }
}
```

**3. Update priority in `rule_based.py`:**
```python
def _sort_by_priority(self, matches):
    priority = [
        QueryType.PRICE,
        QueryType.FUNDAMENTALS,
        QueryType.TECHNICAL_ANALYSIS,  # Add here
        # ... rest ...
    ]
```

**Done!** The new type is now integrated.

---

## 📊 File Size Comparison

### Before (Single File)
```
app/core/query_classifier.py: 305 lines
```

### After (Modular)
```
app/core/classifier/types.py:        85 lines
app/core/classifier/patterns.py:     145 lines
app/core/classifier/rule_based.py:  180 lines
app/core/classifier/factory.py:      45 lines
app/core/classifier/__init__.py:     52 lines
─────────────────────────────────────────────
Total:                               507 lines
```

More lines, but:
- ✅ Each file has single responsibility
- ✅ Easier to navigate
- ✅ Easier to test
- ✅ Easier to extend
- ✅ Better organized

---

## ✅ Backward Compatibility

Old imports still work through `app/core/query_classifier.py`:

```python
# Old import (still works, but deprecated)
from app.core.query_classifier import get_classifier

# Shows deprecation warning, then works normally
classifier = get_classifier()
```

**Recommendation**: Update to new import gradually:
```python
# New import (recommended)
from app.core.classifier import get_classifier
```

---

## 🎯 Summary

**Before**: One large file with everything mixed together
**After**: Clean modular structure with:
- Separate concerns
- Easy to maintain
- Easy to test
- Easy to extend
- Clear dependencies

**Migration**: Just change import from `query_classifier` to `classifier`!

**Result**: Same functionality, better code organization! 🚀

