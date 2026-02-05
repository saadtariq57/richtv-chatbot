"""
Validator Tests

Tests the response validation logic
"""

import pytest
from app.core.validator import (
    validate_response,
    extract_numbers,
    extract_context_numbers,
    verify_numbers,
    calculate_confidence
)


def test_extract_numbers_prices():
    """Test extraction of prices from text."""
    text = "NVDA stock is trading at $875.23 today."
    numbers = extract_numbers(text)
    assert 'prices' in numbers
    assert 875.23 in numbers['prices']


def test_extract_numbers_percentages():
    """Test extraction of percentages from text."""
    text = "The stock is down 3.8% from yesterday."
    numbers = extract_numbers(text)
    assert 'percentages' in numbers
    assert 3.8 in numbers['percentages']


def test_extract_numbers_negative_percentage():
    """Test extraction of negative percentages."""
    text = "The stock changed by -3.8%."
    numbers = extract_numbers(text)
    assert 'percentages' in numbers
    assert -3.8 in numbers['percentages']


def test_extract_context_numbers():
    """Test extraction of numbers from context."""
    context = {
        "ticker": "NVDA",
        "price": 875.23,
        "change_percent": -3.8
    }
    numbers = extract_context_numbers(context)
    assert numbers['prices'] == [875.23]
    assert numbers['percentages'] == [-3.8]
    assert numbers['tickers'] == ["NVDA"]


def test_verify_numbers_match():
    """Test verification when numbers match."""
    extracted = {
        'prices': [875.23],
        'percentages': [-3.8]
    }
    expected = {
        'prices': [875.23],
        'percentages': [-3.8]
    }
    result = verify_numbers(extracted, expected)
    assert result['all_match'] is True
    assert len(result['matches']) > 0


def test_verify_numbers_mismatch():
    """Test verification when numbers don't match."""
    extracted = {
        'prices': [880.00],
        'percentages': [-3.8]
    }
    expected = {
        'prices': [875.23],
        'percentages': [-3.8]
    }
    result = verify_numbers(extracted, expected)
    assert result['all_match'] is False
    assert len(result['mismatches']) > 0


def test_calculate_confidence_high():
    """Test high confidence score."""
    verification = {
        'all_match': True,
        'matches': ['price: 875.23', 'percentage: -3.8%'],
        'mismatches': []
    }
    confidence = calculate_confidence(verification, "NVDA is trading at 875.23", {})
    assert confidence >= 0.9


def test_calculate_confidence_low():
    """Test low confidence for errors."""
    verification = {'all_match': False, 'matches': [], 'mismatches': ['price mismatch']}
    confidence = calculate_confidence(verification, "Error occurred", {})
    assert confidence < 0.2


def test_validate_response_integration():
    """Test full validation flow."""
    llm_answer = "NVDA stock is trading at $875.23, down 3.8% today."
    context = {
        "ticker": "NVDA",
        "price": 875.23,
        "change_percent": -3.8
    }
    
    validated_answer, confidence = validate_response(llm_answer, context)
    
    assert validated_answer == llm_answer
    assert confidence > 0.8  # Should be high confidence since numbers match


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

