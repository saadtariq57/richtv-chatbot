import json
from typing import Optional, Tuple
from app.llm.client import get_llm_client


def generate_answer(context: dict, user_query: str) -> str:
    """
    Generate an answer using LLM based on structured context.
    
    Args:
        context: Structured financial data from fetchers
        user_query: User's question
        
    Returns:
        Generated answer text
    """
    # Create prompt with strict instructions
    prompt = f"""
You are RichTVBot, a financial assistant. Only use the following financial data. 
Do not invent numbers. Answer the user's question based only on this data.
If the data is insufficient, respond with "I have insufficient data to answer this question."

Data: {json.dumps(context, indent=2)}

User Question: {user_query}

Answer:"""
    
    # Use LLM client
    llm = get_llm_client()
    response = llm.generate(prompt, temperature=0.3)
    
    if response:
        return response
    else:
        return "I have insufficient data to answer this question."


def classify_and_answer_if_general(user_query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Combined LLM call to classify intent and answer if it's a general question.
    
    This is used when rule-based patterns don't match, to determine:
    1. Is this a general financial question? → Answer it directly
    2. Is this about a specific stock? → Extract ticker for data fetching
    3. Is it unclear/off-topic? → Reject it
    
    Args:
        user_query: User's question
        
    Returns:
        Tuple of (classification, answer, ticker):
        - ("general", "Answer text", None) if general question
        - ("specific", None, "NVDA") if specific stock query
        - ("unclear", None, None) if off-topic/unclear
    """
    prompt = f"""
You are a financial query analyzer. Analyze this user query and respond in ONE of these formats:

1. If it's a GENERAL financial/investing question (concepts, definitions, how things work):
   → Provide a clear, concise answer
   → Format: ANSWER: [your answer here]

2. If it's about a SPECIFIC stock, company, or ticker:
   → Extract the ticker symbol (or best guess if company name given)
   → Format: NEEDS_DATA: [TICKER]

3. If it's unclear, off-topic, or not about finance/investing:
   → Format: CANNOT_ANSWER

Examples:
- "What is a dividend?" → ANSWER: A dividend is a payment made by a corporation to its shareholders...
- "How much is Apple trading at?" → NEEDS_DATA: AAPL
- "What's NVDA price?" → NEEDS_DATA: NVDA
- "Tell me about Tesla stock" → NEEDS_DATA: TSLA
- "What's the weather?" → CANNOT_ANSWER

User Query: "{user_query}"

Your Response:"""
    
    # Use LLM client
    llm = get_llm_client()
    response = llm.generate(prompt, temperature=0.3)
    
    if not response:
        return ("unclear", None, None)
    
    # Parse the response
    if response.startswith("ANSWER:"):
        # It's a general question with an answer
        clean_answer = response.replace("ANSWER:", "").strip()
        return ("general", clean_answer, None)
        
    elif response.startswith("NEEDS_DATA:"):
        # It's a specific stock query
        ticker = response.replace("NEEDS_DATA:", "").strip()
        return ("specific", None, ticker)
        
    else:  # CANNOT_ANSWER or unexpected format
        return ("unclear", None, None)


def llm_quick_check(user_query: str) -> Tuple[str, Optional[str]]:
    """
    Lightweight LLM check for queries with low/medium confidence.
    
    Used when rule-based classification is uncertain.
    Much cheaper and faster than full classification+answer.
    
    Args:
        user_query: User's question
        
    Returns:
        Tuple of (intent, ticker):
        - ("needs_data", "NVDA") if about specific stock
        - ("general", None) if conceptual question
        - ("unclear", None) if off-topic
    """
    prompt = f"""
Quick intent check for: "{user_query}"

Respond with ONE line only:
- DATA:<TICKER> (if asking about a specific stock/company, provide ticker symbol)
- GENERAL (if asking a conceptual/educational financial question)
- UNCLEAR (if off-topic or can't determine)

Examples:
- "Should I invest in tech stocks?" → GENERAL
- "Tell me about Apple stock" → DATA:AAPL
- "What's NVDA trading at?" → DATA:NVDA
- "How does compound interest work?" → GENERAL
- "What's the weather?" → UNCLEAR

Response:"""
    
    # Use LLM client
    llm = get_llm_client()
    response = llm.generate(prompt, temperature=0.2)
    
    if not response:
        return ("unclear", None)
    
    # Parse response
    if response.startswith("DATA:"):
        ticker = response.replace("DATA:", "").strip()
        return ("needs_data", ticker)
    elif response.startswith("GENERAL"):
        return ("general", None)
    else:
        return ("unclear", None)


async def llm_extract_company_name(user_query: str) -> Optional[str]:
    """
    Use LLM to extract company/asset name from query.
    
    This is a fallback when regex-based extraction fails.
    Used in post-failure rescue when initial query returns insufficient data.
    
    Args:
        user_query: User's original question
        
    Returns:
        Extracted company/asset name or None
    """
    llm = get_llm_client()
    
    prompt = f"""
Extract ONLY the company or asset name from this query. Return just the name, nothing else.

Examples:
- "What's Figma trading at?" → Figma
- "Tell me Nvidia's price" → Nvidia
- "How much for Tesla?" → Tesla
- "Show me Apple stock" → Apple
- "Bitcoin value?" → Bitcoin
- "Price of Coinbase?" → Coinbase
- "What is SAP worth?" → SAP

Query: "{user_query}"

Answer (company/asset name only):"""
    
    response = await llm.generate_async(prompt, temperature=0.1)
    
    if response:
        # Clean up the response
        cleaned = response.strip().strip('"\'.,!?')
        return cleaned if cleaned else None
    
    return None

