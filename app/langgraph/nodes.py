"""
LangGraph nodes: classification, entity resolution, data fetch, answer, validation, finalize.

Each node receives the full state and returns a partial state update.
"""

from datetime import datetime
from typing import Any, Dict, List

from app.api.schemas import Citation, QueryResponse
from app.core.classifier import QueryType
from app.core.orchestrator import (
    categorize_market_data,
    fetch_data_by_classification,
    fetch_multiple_symbols,
    extract_citations,
)
from app.llm.generator import generate_answer, llm_classify_query
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


def classification_node(state: GraphState) -> Dict[str, Any]:
    """Run LLM classification and populate state with query type, entities, symbols, dates."""
    user_query = state["user_query"]
    (
        query_type_str,
        confidence,
        entities_list,
        general_answer,
        symbols_list,
        date_range,
    ) = llm_classify_query(user_query)
    query_type_enum = QUERY_TYPE_MAPPING.get(query_type_str, QueryType.GENERAL)
    return {
        "query_type_str": query_type_str,
        "query_type_enum": query_type_enum,
        "confidence": confidence,
        "entities_list": entities_list,
        "general_answer": general_answer,
        "symbols_list": symbols_list,
        "date_range": date_range,
    }


def build_general_response_node(state: GraphState) -> Dict[str, Any]:
    """Build QueryResponse for general queries (no data fetch)."""
    return {
        "response": QueryResponse(
            answer=state["general_answer"] or "",
            citations=[Citation(source="LLM Knowledge", url="")],
            confidence=0.85,
            data_timestamp=datetime.utcnow().isoformat(),
            context={
                "sources_used": ["general"],
                "classification_confidence": state.get("confidence"),
                "query_type": state.get("query_type_str"),
            },
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
    return {"context": context, "market_error": None}


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

    return {"resolved_symbols": resolved_symbols, "entities_metadata": entities_metadata}


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
            }
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

    return {"context": context}


def answer_node(state: GraphState) -> Dict[str, Any]:
    """Generate LLM answer from context."""
    context = state.get("context") or {}
    user_query = state["user_query"]
    llm_answer = generate_answer(context, user_query)
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
        )
    }
