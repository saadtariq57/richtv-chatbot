"""
LangGraph workflow: classification -> route -> [general | market | entity] -> finalize -> END.
"""

import uuid
from datetime import datetime
from typing import Optional

from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import QueryResponse
from app.langgraph.state import GraphState
from app.langgraph import nodes
from app.services.conversation_service import (
    get_or_create_conversation,
    load_recent_messages,
    save_turn,
)


def _route_after_classification(state: GraphState) -> str:
    """Route to general response, market fetch, or entity resolution."""
    if state.get("query_type_enum") is None:
        return "entity_resolution"
    from app.core.classifier import QueryType
    if state["query_type_enum"] == QueryType.GENERAL and state.get("general_answer"):
        return "build_general_response"
    if state["query_type_enum"] == QueryType.MARKET:
        return "market_fetch"
    return "entity_resolution"


def _route_after_market_fetch(state: GraphState) -> str:
    """Route to error response or to answer generation."""
    if state.get("market_error"):
        return "build_market_error_response"
    return "answer"


def create_graph(checkpointer=None):
    """
    Build the query orchestration graph.

    Args:
        checkpointer: Optional checkpointer for persistence (e.g. MemorySaver()).
                      Enables conversation memory and human-in-the-loop later.
    """
    builder = StateGraph(GraphState)

    # Nodes
    builder.add_node("classification", nodes.classification_node)
    builder.add_node("build_general_response", nodes.build_general_response_node)
    builder.add_node("market_fetch", nodes.market_fetch_node)
    builder.add_node("build_market_error_response", nodes.build_market_error_response_node)
    builder.add_node("entity_resolution", nodes.entity_resolution_node)
    builder.add_node("data_fetch", nodes.data_fetch_node)
    builder.add_node("answer", nodes.answer_node)
    builder.add_node("validation", nodes.validation_node)
    builder.add_node("finalize", nodes.finalize_node)

    # Entry
    builder.set_entry_point("classification")

    builder.add_conditional_edges("classification", _route_after_classification)
    # Conditional: after classification

    # General path
    builder.add_edge("build_general_response", END)

    # Market path
    builder.add_conditional_edges("market_fetch", _route_after_market_fetch)
    builder.add_edge("build_market_error_response", END)
    builder.add_edge("answer", "validation")
    builder.add_edge("validation", "finalize")
    builder.add_edge("finalize", END)

    # Entity path
    builder.add_edge("entity_resolution", "data_fetch")
    builder.add_edge("data_fetch", "answer")

    graph = builder.compile(checkpointer=checkpointer)
    return graph


# Default graph instance (no checkpointer for now)
_graph = None


def get_graph():
    """Get or create the default compiled graph."""
    global _graph
    if _graph is None:
        _graph = create_graph()
    return _graph


async def run_query(
    user_query: str,
    session: AsyncSession,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> QueryResponse:
    """
    Run the orchestration graph for a single query and return the response.

    If user_id is provided, conversation is created or resumed, recent messages
    are loaded for context, and the turn is saved after the response.

    Args:
        user_query: The user's financial question.
        session: Database session for conversation persistence.
        user_id: Optional user id from main app; when set, conversation is used.
        conversation_id: Optional UUID string to resume a conversation.

    Returns:
        QueryResponse with answer, citations, confidence, and conversation_id when applicable.
    """
    graph = get_graph()
    conv_id: Optional[uuid.UUID] = None
    chat_history: Optional[list] = None

    if user_id:
        try:
            conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
        except (ValueError, TypeError):
            conv_uuid = None
        conv_id = await get_or_create_conversation(session, user_id, conv_uuid)
        chat_history = await load_recent_messages(session, conv_id, limit=20)

    initial: GraphState = {
        "user_query": user_query,
        "chat_history": chat_history,
        "conversation_id": str(conv_id) if conv_id else None,
    }
    final_state = await graph.ainvoke(initial)
    response = final_state.get("response")
    if response is None:
        return QueryResponse(
            answer="An error occurred while processing your query.",
            citations=[],
            confidence=0.0,
            data_timestamp=datetime.utcnow().isoformat(),
            context={"error": "No response from graph"},
            conversation_id=str(conv_id) if conv_id else None,
        )

    if conv_id is not None:
        await save_turn(
            session,
            conv_id,
            user_message=user_query,
            assistant_response=response.answer,
            metadata={
                "confidence": response.confidence,
                "data_timestamp": response.data_timestamp,
            },
        )

    return response