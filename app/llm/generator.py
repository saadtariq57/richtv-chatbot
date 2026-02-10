import requests
import json
from typing import Dict, Optional, Tuple
from app.config import settings

def generate_answer(context: dict, user_query: str) -> str:
    """
    Generate an answer using Gemini LLM based on structured context.
    
    Args:
        context: Structured financial data from fetchers
        user_query: User's question
        
    Returns:
        Generated answer text
    """
    # Build URL with API key from config
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Create prompt with strict instructions
    prompt_text = f"""
You are RichTVBot, a financial assistant. Only use the following financial data. 
Do not invent numbers. Answer the user's question based only on this data.
If the data is insufficient, respond with "I have insufficient data to answer this question."

Data: {json.dumps(context, indent=2)}

User Question: {user_query}

Answer:"""
    
    # Prepare API body
    body = {
        "contents": [
            {
                "parts": [{"text": prompt_text}]
            }
        ]
    }
    
    try:
        # Make POST request
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            # Gemini `generateContent` response format:
            # data["candidates"][0]["content"]["parts"][0]["text"]
            answer = data["candidates"][0]["content"]["parts"][0]["text"]
            return answer.strip()
        else:
            return f"LLM API Error: {resp.status_code}"
            
    except requests.exceptions.Timeout:
        return "LLM request timed out"
    except requests.exceptions.RequestException as e:
        return f"LLM request failed: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error parsing LLM response: {str(e)}"


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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt_text = f"""
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
    
    body = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        
        if resp.status_code != 200:
            return ("unclear", None, None)
            
        data = resp.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Parse the response
        if answer.startswith("ANSWER:"):
            # It's a general question with an answer
            clean_answer = answer.replace("ANSWER:", "").strip()
            return ("general", clean_answer, None)
            
        elif answer.startswith("NEEDS_DATA:"):
            # It's a specific stock query
            ticker = answer.replace("NEEDS_DATA:", "").strip()
            return ("specific", None, ticker)
            
        else:  # CANNOT_ANSWER or unexpected format
            return ("unclear", None, None)
            
    except requests.exceptions.Timeout:
        return ("unclear", None, None)
    except requests.exceptions.RequestException:
        return ("unclear", None, None)
    except (KeyError, IndexError):
        return ("unclear", None, None)

