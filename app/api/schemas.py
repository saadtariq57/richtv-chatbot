from pydantic import BaseModel
from typing import List, Optional

class PromptRequest(BaseModel):
    prompt: str

class Citation(BaseModel):
    source: str
    url: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    confidence: float
    data_timestamp: str
    context: Optional[dict] = None  # Temporary for backward compatibility

