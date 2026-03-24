"""
LangGraph workflow with an explicit perceive -> reason -> act -> observe loop.
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
    load_recent_messages_by_budget,
    save_turn,
)
from app.services.title_service import generate_conversation_title


def _route_after_reason(state: GraphState) -> str:
    """Route to the action chosen by the reasoning step."""
    next_action = state.get("next_action")
    if next_action == "build_general_response":
        return "build_general_response"
    if next_action == "market_fetch":
        return "market_fetch"
    if next_action == "entity_resolution":
        return "entity_resolution"
    if next_action == "data_fetch":
        return "data_fetch"
    if next_action == "build_market_error_response":
        return "build_market_error_response"
    return "answer"


def _route_after_observe(state: GraphState) -> str:
    """Route back into the loop after observing action results."""
    if state.get("market_error"):
        return "build_market_error_response"
    if state.get("should_retry") and state.get("iterations", 0) < state.get("max_iterations", 3):
        return "perceive"
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
    builder.add_node("perceive", nodes.perceive_node)
    builder.add_node("reason", nodes.reason_node)
    builder.add_node("build_general_response", nodes.build_general_response_node)
    builder.add_node("market_fetch", nodes.market_fetch_node)
    builder.add_node("build_market_error_response", nodes.build_market_error_response_node)
    builder.add_node("entity_resolution", nodes.entity_resolution_node)
    builder.add_node("data_fetch", nodes.data_fetch_node)
    builder.add_node("observe", nodes.observe_node)
    builder.add_node("answer", nodes.answer_node)
    builder.add_node("validation", nodes.validation_node)
    builder.add_node("finalize", nodes.finalize_node)

    # Entry
    builder.set_entry_point("perceive")

    builder.add_edge("perceive", "reason")
    builder.add_conditional_edges("reason", _route_after_reason)

    # General path
    builder.add_edge("build_general_response", END)

    # Action -> observe loop
    builder.add_edge("market_fetch", "observe")
    builder.add_edge("entity_resolution", "observe")
    builder.add_edge("data_fetch", "observe")
    builder.add_conditional_edges("observe", _route_after_observe)

    # Final answer path
    builder.add_edge("build_market_error_response", END)
    builder.add_edge("answer", "validation")
    builder.add_edge("validation", "finalize")
    builder.add_edge("finalize", END)

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
    is_first_turn: bool = False

    if user_id:
        try:
            conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
        except (ValueError, TypeError):
            conv_uuid = None
        conv_id = await get_or_create_conversation(session, user_id, conv_uuid)
        chat_history = await load_recent_messages_by_budget(session, conv_id)
        is_first_turn = not bool(chat_history)

    initial: GraphState = {
        "user_query": user_query,
        "chat_history": chat_history,
        "conversation_id": str(conv_id) if conv_id else None,
        "iterations": 0,
        "max_iterations": 3,
    }
    final_state = await graph.ainvoke(initial)
    response: Optional[QueryResponse] = final_state.get("response")
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
        # Best‑effort title generation for new conversations.
        if is_first_turn:
            title = await generate_conversation_title(user_query, response.answer)
            if title:
                from app.models.conversation import Conversation  # local import to avoid cycles

                db_conv = await session.get(Conversation, conv_id)
                if db_conv and not db_conv.title:
                    db_conv.title = title
                    await session.commit()
        # Persist this turn (user + assistant messages).
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