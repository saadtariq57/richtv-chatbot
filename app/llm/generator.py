import requests
import json
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
If the data is insufficient, respond with "Insufficient data to answer this question."

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

