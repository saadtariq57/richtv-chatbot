"""
LangGraph nodes for an explicit perceive -> reason -> act -> observe loop.

Each node receives the full state and returns a partial state update.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.api.schemas import Citation, QueryResponse
from app.core.classifier import QueryType
from app.core.orchestrator import (
    categorize_market_data,
    fetch_data_by_classification,
    fetch_multiple_symbols,
    extract_citations,
)
from app.llm.client import get_llm_client
from app.llm.generator import generate_answer, generate_conversational_answer, llm_classify_query
from app.core.validator import validate_response
from app.utils.ticker_resolver import (
    resolve_entity_to_symbol,
    validate_symbols,
    DEFAULT_MARKET_SYMBOLS,
)

from app.langgraph.state import GraphState

QUERY_TYPE_MAPPING = {
    "price": QueryType.PRICE,
    "historical": QueryType.HISTORICAL,
    "fundamentals": QueryType.FUNDAMENTALS,
    "analysis": QueryType.ANALYSIS,
    "market": QueryType.MARKET,
    "general": QueryType.GENERAL,
    "news": QueryType.NEWS,
}

ALLOWED_NEXT_ACTIONS = {
    "build_general_response",
    "market_fetch",
    "entity_resolution",
    "data_fetch",
    "answer",
    "build_market_error_response",
}


def _context_has_usable_data(context: Dict[str, Any]) -> bool:
    """Check whether fetched context contains actionable data for an answer."""
    if not context or context.get("error"):
        return False

    if context.get("market_overview"):
        return True

    entities = context.get("entities") or {}
    for entity_payload in entities.values():
        data = (entity_payload or {}).get("data") or {}
        if any(value for value in data.values()):
            return True

    return False


def _fallback_next_action(
    query_type_enum: QueryType,
    state: GraphState,
    observation: Dict[str, Any],
) -> str:
    """Choose a safe deterministic next action when planner output is unavailable."""
    context = state.get("context") or {}
    last_action = observation.get("last_action")
    if last_action is None:
        last_action = state.get("last_action")
    resolved_symbols = observation.get("resolved_symbols") or state.get("resolved_symbols") or []
    entities_list = observation.get("entities") or state.get("entities_list") or []

    if query_type_enum == QueryType.GENERAL and (
        state.get("general_answer") or state.get("chat_history")
    ):
        return "build_general_response"
    if state.get("market_error"):
        return "build_market_error_response"
    if query_type_enum == QueryType.MARKET and not _context_has_usable_data(context):
        return "market_fetch" if last_action != "market_fetch" else "answer"
    if entities_list and not resolved_symbols:
        return "entity_resolution" if last_action != "entity_resolution" else "answer"
    if resolved_symbols and not _context_has_usable_data(context):
        return "data_fetch" if last_action != "data_fetch" else "answer"
    return "answer"


def _planner_observation(state: GraphState, observation: Dict[str, Any]) -> Dict[str, Any]:
    """Build a compact planning view for the LLM reasoner."""
    context = state.get("context") or {}
    entities = context.get("entities") or {}
    query_type_enum = state.get("query_type_enum")
    query_type_value = query_type_enum.value if query_type_enum else None
    observation_entities = observation.get("entities") or state.get("entities_list") or []
    observation_symbols = observation.get("symbols") or state.get("symbols_list") or []
    observation_resolved_symbols = observation.get("resolved_symbols") or state.get("resolved_symbols") or []
    last_action = observation.get("last_action")
    if last_action is None:
        last_action = state.get("last_action")

    return {
        "user_query": observation.get("user_query", state["user_query"]),
        "query_type": query_type_value or observation.get("query_type"),
        "confidence": state.get("confidence"),
        "entities": observation_entities,
        "symbols": observation_symbols,
        "resolved_symbols": observation_resolved_symbols,
        "last_action": last_action,
        "iterations": state.get("iterations", 0),
        "max_iterations": state.get("max_iterations", 3),
        "has_general_answer": bool(state.get("general_answer")),
        "has_chat_history": bool(state.get("chat_history")),
        "market_error": state.get("market_error"),
        "context_error": context.get("error"),
        "has_usable_data": _context_has_usable_data(context),
        "has_market_overview": bool(context.get("market_overview")),
        "entity_count_with_data": sum(
            1
            for entity_payload in entities.values()
            if any(((entity_payload or {}).get("data") or {}).values())
        ),
    }


def _plan_next_action_with_llm(
    state: GraphState,
    observation: Dict[str, Any],
    query_type_enum: QueryType,
) -> tuple[Optional[str], Optional[str]]:
    """Ask the LLM to choose the next action from the graph's action space."""
    planner_view = _planner_observation(state, observation)
    llm = get_llm_client()
    prompt = f"""You are the reasoning module for a financial assistant agent.

Choose the SINGLE best next action for the current state of the agent.

Allowed actions:
- build_general_response: use when this is a general/conversational query and no market data fetch is needed
- market_fetch: fetch market overview data for planned symbols
- entity_resolution: resolve extracted entities to ticker symbols
- data_fetch: fetch financial data for already resolved symbols
- answer: answer now because enough information exists or no more useful tool action remains
- build_market_error_response: return the current market fetch error to the user

Rules:
1. Choose exactly one action from the allowed list.
2. Do not choose an action that is impossible from the current state.
3. Prefer `answer` when enough data already exists.
4. Prefer `answer` instead of repeating the exact same failed action.
5. If the query type is `general`, prefer `build_general_response` when possible.
6. If there is a market error, choose `build_market_error_response`.

Current state:
{json.dumps(planner_view, indent=2)}

Return exactly this format:
ACTION: <one allowed action>
RATIONALE: <one short sentence>
"""
    response = llm.generate(prompt, temperature=0.1)
    if not response:
        return None, None

    action = None
    rationale = None
    for line in response.splitlines():
        stripped = line.strip()
        if stripped.startswith("ACTION:"):
            action = stripped.replace("ACTION:", "", 1).strip()
        elif stripped.startswith("RATIONALE:"):
            rationale = stripped.replace("RATIONALE:", "", 1).strip()

    if action and action not in ALLOWED_NEXT_ACTIONS:
        return None, rationale

    return action, rationale


def _validate_planned_action(
    action: Optional[str],
    query_type_enum: QueryType,
    state: GraphState,
    observation: Dict[str, Any],
) -> Optional[str]:
    """Validate that the planner's chosen action is executable in the current state."""
    if action not in ALLOWED_NEXT_ACTIONS:
        return None

    context = state.get("context") or {}
    entities_list = observation.get("entities") or state.get("entities_list") or []
    resolved_symbols = observation.get("resolved_symbols") or state.get("resolved_symbols") or []

    if action == "build_general_response":
        if query_type_enum != QueryType.GENERAL:
            return None
        if not (state.get("general_answer") or state.get("chat_history")):
            return None
    elif action == "market_fetch":
        if query_type_enum != QueryType.MARKET:
            return None
        if _context_has_usable_data(context):
            return None
    elif action == "entity_resolution":
        if not entities_list:
            return None
        if resolved_symbols:
            return None
    elif action == "data_fetch":
        if not resolved_symbols:
            return None
        if _context_has_usable_data(context):
            return None
    elif action == "build_market_error_response":
        if not state.get("market_error"):
            return None

    return action


def perceive_node(state: GraphState) -> Dict[str, Any]:
    """Assemble the current observation before the agent reasons about the next step."""
    context = state.get("context") or {}
    return {
        "observation": {
            "user_query": state["user_query"],
            "chat_history": state.get("chat_history") or [],
            "query_type": state.get("query_type_str"),
            "entities": state.get("entities_list") or [],
            "symbols": state.get("symbols_list") or [],
            "resolved_symbols": state.get("resolved_symbols") or [],
            "has_context": bool(context),
            "context_error": context.get("error"),
            "market_error": state.get("market_error"),
            "last_action": state.get("last_action"),
            "iterations": state.get("iterations", 0),
        }
    }


def reason_node(state: GraphState) -> Dict[str, Any]:
    """Decide the next action based on the current observation and prior results."""
    updates: Dict[str, Any] = {}
    observation = state.get("observation") or {}

    if state.get("query_type_enum") is None:
        user_query = observation.get("user_query", state["user_query"])
        (
            query_type_str,
            confidence,
            entities_list,
            general_answer,
            symbols_list,
            date_range,
        ) = llm_classify_query(user_query)
        query_type_enum = QUERY_TYPE_MAPPING.get(query_type_str, QueryType.GENERAL)
        updates.update(
            {
                "query_type_str": query_type_str,
                "query_type_enum": query_type_enum,
                "confidence": confidence,
                "entities_list": entities_list,
                "general_answer": general_answer,
                "symbols_list": symbols_list,
                "date_range": date_range,
            }
        )
    else:
        query_type_enum = state["query_type_enum"]

    # Snapshot of state + newly computed updates so planning uses the latest values.
    planning_state: GraphState = {**state, **updates}

    planned_action, planner_rationale = _plan_next_action_with_llm(
        planning_state,
        observation,
        query_type_enum,
    )
    next_action = _validate_planned_action(
        planned_action,
        query_type_enum,
        planning_state,
        observation,
    )
    if next_action is None:
        next_action = _fallback_next_action(query_type_enum, planning_state, observation)
        if planner_rationale:
            planner_rationale = f"Fallback applied after invalid planner action: {planner_rationale}"
        else:
            planner_rationale = "Fallback planner used because no valid LLM action was returned."

    updates["next_action"] = next_action
    updates["planner_rationale"] = planner_rationale
    if next_action in {"market_fetch", "entity_resolution", "data_fetch"}:
        updates["iterations"] = state.get("iterations", 0) + 1

    return updates


def build_general_response_node(state: GraphState) -> Dict[str, Any]:
    """Build QueryResponse for general queries (no data fetch)."""
    chat_history = state.get("chat_history")
    if chat_history:
        answer = generate_conversational_answer(state["user_query"], chat_history)
    else:
        answer = state["general_answer"] or ""

    return {
        "response": QueryResponse(
            answer=answer,
            citations=[Citation(source="LLM Knowledge", url="")],
            confidence=0.85,
            data_timestamp=datetime.utcnow().isoformat(),
            context={
                "sources_used": ["general"],
                "classification_confidence": state.get("confidence"),
                "query_type": state.get("query_type_str"),
            },
            conversation_id=state.get("conversation_id"),
        )
    }


async def market_fetch_node(state: GraphState) -> Dict[str, Any]:
    """Fetch market data for symbols; set context or market_error."""
    symbols_list = state.get("symbols_list")
    if symbols_list:
        validated_symbols = validate_symbols(symbols_list, max_symbols=20)
    else:
        validated_symbols = DEFAULT_MARKET_SYMBOLS

    if not validated_symbols:
        return {
            "market_error": "I couldn't determine which market data to fetch. Please be more specific.",
            "context": {
                "query": state["user_query"],
                "query_type": "market",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "No symbols to fetch",
            },
        }
 
    market_data = await fetch_multiple_symbols(validated_symbols)
    success_rate = len(market_data) / len(validated_symbols) if validated_symbols else 0

    if success_rate < 0.5:
        return {
            "market_error": "I'm having trouble fetching market data right now. Most of the requested symbols are unavailable. Please try again later.",
            "context": {
                "query": state["user_query"],
                "query_type": "market",
                "timestamp": datetime.utcnow().isoformat(),
                "symbols_requested": validated_symbols,
                "symbols_fetched": list(market_data.keys()),
                "success_rate": f"{success_rate:.1%}",
            },
        }

    categorized_data = categorize_market_data(market_data)
    context = {
        "query": state["user_query"],
        "query_type": "market",
        "market_overview": categorized_data,
        "symbols_fetched": list(market_data.keys()),
        "total_symbols": len(validated_symbols),
        "success_count": len(market_data),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {"context": context, "market_error": None, "last_action": "market_fetch"}


def build_market_error_response_node(state: GraphState) -> Dict[str, Any]:
    """Build QueryResponse when market fetch failed."""
    return {
        "response": QueryResponse(
            answer=state.get("market_error", "Market data unavailable."),
            citations=[Citation(source="Mboum API - Market Data", url="")] if state.get("context") else [],
            confidence=0.2,
            data_timestamp=state.get("context", {}).get("timestamp", datetime.utcnow().isoformat()),
            context={
                "sources_used": ["market"],
                "classification_confidence": state.get("confidence"),
                **state.get("context", {}),
            },
            conversation_id=state.get("conversation_id"),
        )
    }


async def entity_resolution_node(state: GraphState) -> Dict[str, Any]:
    """Resolve entities to symbols using ticker resolver."""
    entities_list = state.get("entities_list") or []
    resolved_symbols: List[str] = []
    entities_metadata: List[Dict[str, Any]] = []

    for entity in entities_list:
        meta = await resolve_entity_to_symbol(entity)
        if meta:
            resolved_symbols.append(meta["symbol"])
            entities_metadata.append(meta)

    return {
        "resolved_symbols": resolved_symbols,
        "entities_metadata": entities_metadata,
        "last_action": "entity_resolution",
    }


async def data_fetch_node(state: GraphState) -> Dict[str, Any]:
    """Fetch data by classification for resolved symbols; build context."""
    user_query = state["user_query"]
    query_type_enum = state["query_type_enum"]
    date_range = state.get("date_range")
    resolved_symbols = state.get("resolved_symbols") or []
    entities_list = state.get("entities_list") or []
    entities_metadata = state.get("entities_metadata") or []

    if not resolved_symbols:
        return {
            "context": {
                "query": user_query,
                "timestamp": datetime.utcnow().isoformat(),
                "error": "No entities were resolved from the query",
            },
            "last_action": "data_fetch",
        }

    entities_data: Dict[str, Any] = {}
    for idx, symbol in enumerate(resolved_symbols):
        entity_data = await fetch_data_by_classification(symbol, [query_type_enum], date_range)
        entity_name = entities_list[idx] if idx < len(entities_list) else symbol
        entities_data[entity_name] = {
            "symbol": symbol,
            "data": entity_data,
            "metadata": entities_metadata[idx] if idx < len(entities_metadata) else None,
        }

    context = {
        "query": user_query,
        "entities": entities_data,
        "timestamp": datetime.utcnow().isoformat(),
    }

    has_data = any(
        e["data"].get("price") or e["data"].get("historical_data") or e["data"].get("fundamentals_data")
        for e in entities_data.values()
    )
    if not has_data and entities_list:
        context["error"] = f"Could not find data for '{', '.join(entities_list)}'"
        if not entities_metadata:
            context["error"] = f"Could not find symbols for '{', '.join(entities_list)}'. Please check the tickers or company names."

    return {"context": context, "last_action": "data_fetch"}


def observe_node(state: GraphState) -> Dict[str, Any]:
    """Inspect action results and decide whether to re-enter the loop."""
    context = state.get("context") or {}
    last_action = state.get("last_action")
    max_iterations = state.get("max_iterations", 3)
    iterations = state.get("iterations", 0)

    if state.get("market_error"):
        should_retry = False
    elif last_action == "entity_resolution":
        should_retry = bool(state.get("resolved_symbols")) and iterations < max_iterations
    elif last_action in {"market_fetch", "data_fetch"}:
        should_retry = _context_has_usable_data(context) and iterations < max_iterations
    else:
        should_retry = False

    return {"should_retry": should_retry}


def answer_node(state: GraphState) -> Dict[str, Any]:
    """Generate LLM answer from context and optional chat history."""
    context = state.get("context") or {}
    user_query = state["user_query"]
    chat_history = state.get("chat_history")
    llm_answer = generate_answer(context, user_query, chat_history=chat_history)
    return {"llm_answer": llm_answer}


def validation_node(state: GraphState) -> Dict[str, Any]:
    """Validate response and compute confidence."""
    llm_answer = state.get("llm_answer") or ""
    context = state.get("context") or {}
    validated_answer, answer_confidence = validate_response(llm_answer, context)
    citations = extract_citations(context)
    return {
        "validated_answer": validated_answer,
        "answer_confidence": answer_confidence,
        "citations": citations,
    }


def finalize_node(state: GraphState) -> Dict[str, Any]:
    """Build final QueryResponse from state (market success or entity path)."""
    context = state.get("context") or {}
    return {
        "response": QueryResponse(
            answer=state.get("validated_answer", ""),
            citations=state.get("citations") or [],
            confidence=state.get("answer_confidence", 0.5),
            data_timestamp=context.get("timestamp", datetime.utcnow().isoformat()),
            context={
                "sources_used": [state.get("query_type_enum", QueryType.GENERAL).value],
                "classification_confidence": state.get("confidence"),
                "entities": state.get("entities_list"),
                "resolved_symbols": state.get("resolved_symbols"),
                "data": context,
            },
            conversation_id=state.get("conversation_id"),
        )
    }
