"""
Response Validator - Ensures LLM output matches fetched data

Implements the validation logic from docs/response_validator.md:
1. Extract numbers and entities from LLM response
2. Verify all numbers match the context
3. Assign confidence score
4. Reject or flag unverifiable output
"""

import re
from typing import Tuple


def validate_response(llm_answer: str, context: dict) -> Tuple[str, float]:
    """
    Validate LLM response against structured context.
    
    Args:
        llm_answer: Text response from LLM
        context: Structured data from fetchers
        
    Returns:
        Tuple of (validated_answer, confidence_score)
        - validated_answer: Original or corrected answer
        - confidence_score: 0.0-1.0
    """
    # Step 1: Extract numbers from LLM answer
    extracted_numbers = extract_numbers(llm_answer)
    
    # Step 2: Extract expected numbers from context
    context_numbers = extract_context_numbers(context)
    
    # Step 3: Verify all extracted numbers match context
    verification_result = verify_numbers(extracted_numbers, context_numbers)
    
    # Step 4: Assign confidence score based on verification
    confidence = calculate_confidence(verification_result, llm_answer, context)
    
    # Step 5: Return validated answer
    # For now, we trust the LLM if numbers match
    # Future: Could correct mismatched numbers automatically
    validated_answer = llm_answer
    
    return validated_answer, confidence


def extract_numbers(text: str) -> dict:
    """
    Extract numbers from text using regex.
    
    Returns:
        Dictionary of number_type: value
    """
    numbers = {}
    
    # Extract decimal numbers (prices, etc.)
    price_pattern = r'\$?(\d+\.?\d*)'
    prices = re.findall(price_pattern, text)
    if prices:
        numbers['prices'] = [float(p) for p in prices]
    
    # Extract percentages
    percent_pattern = r'(-?\d+\.?\d*)\s*%'
    percentages = re.findall(percent_pattern, text)
    if percentages:
        numbers['percentages'] = [float(p) for p in percentages]
    
    # Extract ticker symbols
    ticker_pattern = r'\b([A-Z]{1,5})\b'
    tickers = re.findall(ticker_pattern, text)
    if tickers:
        # Filter out common words that might match
        common_words = {'USD', 'CEO', 'IPO', 'ETF', 'NVDA', 'AI'}
        numbers['tickers'] = [t for t in tickers if t in common_words or len(t) <= 4]
    
    return numbers


def extract_context_numbers(context: dict) -> dict:
    """
    Extract expected numbers from context data.
    
    Returns:
        Dictionary of number_type: value
    """
    numbers = {}
    
    if 'price' in context:
        numbers['prices'] = [float(context['price'])]
    
    if 'change_percent' in context:
        numbers['percentages'] = [float(context['change_percent'])]
    
    if 'ticker' in context:
        numbers['tickers'] = [context['ticker']]
    
    return numbers


def verify_numbers(extracted: dict, expected: dict) -> dict:
    """
    Verify extracted numbers match expected values.
    
    Returns:
        Dictionary with verification results
    """
    result = {
        'all_match': True,
        'matches': [],
        'mismatches': [],
        'missing': []
    }
    
    # Check prices
    if 'prices' in extracted and 'prices' in expected:
        for exp_price in expected['prices']:
            found = False
            for ext_price in extracted['prices']:
                # Allow small floating point differences
                if abs(ext_price - exp_price) < 0.01:
                    result['matches'].append(f"price: {exp_price}")
                    found = True
                    break
            if not found:
                result['mismatches'].append(f"price: expected {exp_price}, found {extracted['prices']}")
                result['all_match'] = False
    
    # Check percentages
    if 'percentages' in extracted and 'percentages' in expected:
        for exp_pct in expected['percentages']:
            found = False
            for ext_pct in extracted['percentages']:
                if abs(ext_pct - exp_pct) < 0.1:
                    result['matches'].append(f"percentage: {exp_pct}%")
                    found = True
                    break
            if not found:
                result['mismatches'].append(f"percentage: expected {exp_pct}%, found {extracted['percentages']}")
                result['all_match'] = False
    
    # Check tickers
    if 'tickers' in extracted and 'tickers' in expected:
        for exp_ticker in expected['tickers']:
            if exp_ticker in extracted['tickers']:
                result['matches'].append(f"ticker: {exp_ticker}")
            else:
                result['mismatches'].append(f"ticker: expected {exp_ticker}, not found")
                result['all_match'] = False
    
    return result


def calculate_confidence(verification: dict, llm_answer: str, context: dict) -> float:
    """
    Calculate confidence score based on verification results.
    
    Confidence levels:
    - 0.9-1.0: All numbers match perfectly
    - 0.7-0.9: Most numbers match, minor discrepancies
    - 0.5-0.7: Partial match
    - 0.0-0.5: Major mismatches or hallucinations
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Check for error messages
    if "insufficient data" in llm_answer.lower() or "cannot answer" in llm_answer.lower():
        return 0.3
    
    if "error" in llm_answer.lower():
        return 0.1
    
    # All numbers match perfectly
    if verification['all_match'] and len(verification['matches']) > 0:
        return 0.95
    
    # No numbers extracted (might be a general question)
    if len(verification['matches']) == 0 and len(verification['mismatches']) == 0:
        return 0.6
    
    # Calculate ratio of matches to total
    total_checks = len(verification['matches']) + len(verification['mismatches'])
    if total_checks > 0:
        match_ratio = len(verification['matches']) / total_checks
        
        if match_ratio >= 0.9:
            return 0.85
        elif match_ratio >= 0.7:
            return 0.7
        elif match_ratio >= 0.5:
            return 0.55
        else:
            return 0.3
    
    # Default: medium-low confidence
    return 0.5

