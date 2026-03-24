from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PromptRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


class Citation(BaseModel):
    source: str
    url: str


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    confidence: float
    data_timestamp: str
    context: Optional[dict] = None
    conversation_id: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MessageDTO(BaseModel):
    role: str
    content: str
    created_at: datetime

