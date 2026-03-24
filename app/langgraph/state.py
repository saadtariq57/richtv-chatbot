"""
Graph state definition for the query orchestration workflow.

All keys are optional except those required for entry (user_query).
Nodes return partial updates that get merged into the state.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from app.api.schemas import Citation, QueryResponse
from app.core.classifier import QueryType


class GraphState(TypedDict, total=False):
    """State passed through the LangGraph workflow."""

    # Input
    user_query: str
    session_id: Optional[str]
    # Conversation context (last N messages for LLM)
    chat_history: Optional[List[Dict[str, str]]]
    # Set when using conversation flow; included in response
    conversation_id: Optional[str]
    # Explicit perception / reasoning loop state
    observation: Dict[str, Any]
    next_action: str
    planner_rationale: Optional[str]
    last_action: Optional[str]
    iterations: int
    max_iterations: int
    should_retry: bool

    # Classification (from llm_classify_query)
    query_type_str: str
    query_type_enum: QueryType
    confidence: str
    entities_list: Optional[List[str]]
    general_answer: Optional[str]
    symbols_list: Optional[List[str]]
    date_range: Optional[Dict[str, str]]

    # Entity resolution
    resolved_symbols: List[str]
    entities_metadata: List[Dict[str, Any]]

    # Fetched data and context for LLM
    context: Dict[str, Any]

    # Generation and validation
    llm_answer: str
    validated_answer: str
    answer_confidence: float
    citations: List[Citation]

    # Output
    response: QueryResponse

    # Error / early exit
    market_error: Optional[str]
