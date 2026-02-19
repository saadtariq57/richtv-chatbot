"""
Query Orchestrator - Coordinates the flow from query to response

Now with intelligent query classification and multi-source routing,
backed by real Mboum & FMP API integrations.
"""

from datetime import datetime
from typing import Dict, List, Optional
import asyncio

from app.api.schemas import QueryResponse, Citation
# Rule-based classifier - KEPT FOR REFERENCE BUT NOT USED
# from app.core.classifier import get_classifier, QueryType
from app.core.classifier import QueryType  # Keep QueryType enum for compatibility
from app.context.builder import build_context, is_valid_ticker
from app.llm.generator import (
    generate_answer, 
    llm_classify_query,  # NEW: LLM-based classification (optimized)
)
from app.core.validator import validate_response
from app.data_fetchers.price_fetcher import PriceFetcher
from app.data_fetchers.fmp_fetcher import FMPFetcher
from app.utils.ticker_resolver import (
    resolve_entity_to_symbol,
    validate_symbols,
    DEFAULT_MARKET_SYMBOLS
)


async def fetch_multiple_symbols(symbols: List[str]) -> Dict[str, Dict]:
    """
    Fetch price data for multiple symbols using batch API call.
    
    Used for market overview queries where we need data for many symbols at once.
    Uses Mboum's batch fetch capability (comma-separated tickers) for efficiency.
    
    Args:
        symbols: List of ticker symbols to fetch
        
    Returns:
        Dict mapping symbol → price data
        Only includes successful fetches
    """
    if not symbols:
        return {}
    
    print(f"📊 Fetching data for {len(symbols)} symbols in batch...")
    
    price_fetcher = PriceFetcher()
    
    # Use batch fetch - single API call for all symbols
    results = await price_fetcher.fetch_batch(symbols)
    
    # Process results
    data = {}
    success_count = 0
    
    for symbol, result in results.items():
        if isinstance(result, dict) and result.get("status") == "success":
            data[symbol] = result
            success_count += 1
            print(f"   ✅ {symbol}: ${result.get('price', 'N/A')}")
        else:
            # Show error details if available
            error_msg = result.get("error", "No data") if isinstance(result, dict) else "No data"
            print(f"   ⚠️  {symbol}: {error_msg}")
    
    print(f"📊 Successfully fetched {success_count}/{len(symbols)} symbols")
    
    return data


def categorize_market_data(data: Dict[str, Dict]) -> Dict:
    """
    Organize fetched market data into categories for better LLM presentation.
    
    Categories:
    - indices: Major market indices (^GSPC, ^DJI, etc.)
    - stocks: Individual stocks (AAPL, MSFT, etc.)
    - crypto: Cryptocurrencies (BTC-USD, ETH-USD, etc.)
    - commodities: Commodities (GC=F, CL=F, etc.)
    
    Args:
        data: Dict of symbol → price data
        
    Returns:
        Categorized dict with organized market data
    """
    categorized = {
        "indices": {},
        "stocks": {},
        "crypto": {},
        "commodities": {}
    }
    
    for symbol, info in data.items():
        if symbol.startswith("^"):
            # Index (^GSPC, ^DJI, ^IXIC)
            categorized["indices"][symbol] = info
        elif "-USD" in symbol or "-USDT" in symbol:
            # Cryptocurrency (BTC-USD, ETH-USD)
            categorized["crypto"][symbol] = info
        elif "=F" in symbol:
            # Commodity futures (GC=F, CL=F)
            categorized["commodities"][symbol] = info
        else:
            # Regular stock (AAPL, MSFT, NVDA)
            categorized["stocks"][symbol] = info
    
    return categorized


async def orchestrate_query(user_query: str) -> QueryResponse:
    """
    OPTIMIZED orchestration flow with LLM-first classification.
    
    Flow:
    1. LLM classifies query & answers general queries immediately (1 call)
    2. For data queries: Resolve entity → Fetch data → Generate answer
    3. Validate and return response
    
    Args:
        user_query: User's financial question
        
    Returns:
        QueryResponse with validated answer and metadata
    """
    # ========================================================================
    # STEP 1: LLM Classification (OPTIMIZED & SMART)
    # ========================================================================
    # This single LLM call does three things:
    # 1. Classify the query type
    # 2. Answer immediately if it's a general query (no data needed)
    # 3. For MARKET queries, determine which symbols to fetch
    # ========================================================================
    
    query_type_str, confidence, entities_list, general_answer, symbols_list, date_range = llm_classify_query(user_query)
    
    print(f"✨ LLM Classification:")
    print(f"   Type: {query_type_str}")
    print(f"   Confidence: {confidence}")
    print(f"   Entities: {entities_list if entities_list else 'None'}")
    print(f"   Symbols: {symbols_list if symbols_list else 'None'}")
    print(f"   Date Range: {date_range if date_range else 'None'}")
    print(f"   General Answer: {'Provided' if general_answer else 'None (needs data)'}")
    
    # Map string query type to QueryType enum
    query_type_mapping = {
        "price": QueryType.PRICE,
        "historical": QueryType.HISTORICAL,
        "fundamentals": QueryType.FUNDAMENTALS,
        "analysis": QueryType.ANALYSIS,
        "market": QueryType.MARKET,
        "general": QueryType.GENERAL,
        "news": QueryType.NEWS
    }
    
    query_type_enum = query_type_mapping.get(query_type_str, QueryType.GENERAL)
    
    # ========================================================================
    # STEP 2: Handle GENERAL queries (already answered in Step 1)
    # ========================================================================
    if query_type_enum == QueryType.GENERAL and general_answer:
        print("✅ General query - returning answer from LLM (no data fetching needed)")
        
        return QueryResponse(
            answer=general_answer,
            citations=[Citation(source="LLM Knowledge", url="")],
            confidence=0.85,  # High for general conceptual answers
            data_timestamp=datetime.utcnow().isoformat(),
            context={
                "sources_used": ["general"],
                "classification_confidence": confidence,
                "query_type": query_type_str
            }
        )
    
    # ========================================================================
    # STEP 2.5: Handle MARKET queries (multiple symbols)
    # ========================================================================
    if query_type_enum == QueryType.MARKET:
        print("🌍 Market query detected")
        
        # Validate and limit symbols from LLM
        if symbols_list:
            validated_symbols = validate_symbols(symbols_list, max_symbols=20)
            print(f"   LLM provided {len(symbols_list)} symbols")
            print(f"   After validation: {len(validated_symbols)} symbols")
        else:
            # No symbols from LLM - use default backup
            print("   ⚠️  No symbols from LLM - using default market overview")
            validated_symbols = DEFAULT_MARKET_SYMBOLS
        
        if not validated_symbols:
            # No symbols at all - can't proceed
            print("   ❌ No valid symbols to fetch")
            return QueryResponse(
                answer="I couldn't determine which market data to fetch. Please be more specific.",
                citations=[],
                confidence=0.3,
                data_timestamp=datetime.utcnow().isoformat(),
                context={
                    "sources_used": ["market"],
                    "classification_confidence": confidence,
                    "error": "No symbols to fetch"
                }
            )
        
        # Fetch all symbols in parallel
        market_data = await fetch_multiple_symbols(validated_symbols)
        
        # Check if we got enough data
        success_rate = len(market_data) / len(validated_symbols)
        
        if success_rate < 0.5:
            # More than half failed - data unavailable
            print(f"   ❌ Too many failures: {len(market_data)}/{len(validated_symbols)} succeeded")
            return QueryResponse(
                answer="I'm having trouble fetching market data right now. Most of the requested symbols are unavailable. Please try again later.",
                citations=[Citation(source="Mboum API - Market Data", url="")],
                confidence=0.2,
                data_timestamp=datetime.utcnow().isoformat(),
                context={
                    "sources_used": ["market"],
                    "classification_confidence": confidence,
                    "symbols_requested": validated_symbols,
                    "symbols_fetched": list(market_data.keys()),
                    "success_rate": f"{success_rate:.1%}"
                }
            )
        
        # Categorize the data for better LLM presentation
        categorized_data = categorize_market_data(market_data)
        
        # Build context for LLM
        context = {
            "query": user_query,
            "query_type": "market",
            "market_overview": categorized_data,
            "symbols_fetched": list(market_data.keys()),
            "total_symbols": len(validated_symbols),
            "success_count": len(market_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"   📊 Market data ready:")
        print(f"      Indices: {len(categorized_data['indices'])}")
        print(f"      Stocks: {len(categorized_data['stocks'])}")
        print(f"      Crypto: {len(categorized_data['crypto'])}")
        print(f"      Commodities: {len(categorized_data['commodities'])}")
        
        # Generate comprehensive market overview
        llm_answer = generate_answer(context, user_query)
        validated_answer, answer_confidence = validate_response(llm_answer, context)
        
        return QueryResponse(
            answer=validated_answer,
            citations=[Citation(source="Mboum API - Market Data", url="")],
            confidence=answer_confidence,
            data_timestamp=context["timestamp"],
            context={
                "sources_used": ["market"],
                "classification_confidence": confidence,
                "symbols_requested": validated_symbols,
                "symbols_fetched": list(market_data.keys()),
                "data": context
            }
        )
    
    # ========================================================================
    # STEP 3: Entity Resolution (for data queries - supports multiple entities)
    # ========================================================================
    resolved_symbols = []
    entities_metadata = []
    
    if entities_list:
        print(f"🔍 Resolving {len(entities_list)} entity/entities: {entities_list}")
        
        for entity in entities_list:
            print(f"   Resolving: '{entity}'")
            entity_metadata = await resolve_entity_to_symbol(entity)
            
            if entity_metadata:
                resolved_symbol = entity_metadata['symbol']
                resolved_symbols.append(resolved_symbol)
                entities_metadata.append(entity_metadata)
                print(f"   ✅ '{entity}' → '{resolved_symbol}' ({entity_metadata.get('name', 'N/A')})")
            else:
                print(f"   ⚠️  Could not resolve: '{entity}'")
        
        if resolved_symbols:
            print(f"✅ Total resolved: {len(resolved_symbols)} symbols: {resolved_symbols}")
        else:
            print(f"❌ No entities could be resolved")
    else:
        print("ℹ️  No entities to resolve (market query or general)")
    
    # ========================================================================
    # STEP 4: Data Fetching (works for single or multiple entities)
    # ========================================================================
    # Simple approach: Fetch data for all entities, put in clean structure
    # LLM reads the query and figures out what to do (compare, analyze, etc.)
    
    if resolved_symbols:
        # We have entities - fetch data for each
        print(f"📊 Fetching data for {len(resolved_symbols)} entity/entities")
        
        entities_data = {}
        for idx, symbol in enumerate(resolved_symbols):
            print(f"   Fetching data for {symbol}...")
            entity_data = await fetch_data_by_classification(symbol, [query_type_enum], date_range)
            
            # Label with entity name for clarity
            entity_name = entities_list[idx] if idx < len(entities_list) else symbol
            entities_data[entity_name] = {
                "symbol": symbol,
                "data": entity_data,
                "metadata": entities_metadata[idx] if idx < len(entities_metadata) else None
            }
        
        # Build clean context with all entity data
        context = {
            "query": user_query,
            "entities": entities_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"✅ Fetched data for {len(entities_data)} entity/entities")
        
    else:
        # No entities (general or market query)
        context = await fetch_data_by_classification(user_query, [query_type_enum], date_range)
        print(f"📊 Data fetched: {list(context.keys())}")
    
    # ========================================================================
    # STEP 5: Check if we got data (error handling)
    # ========================================================================
    if context.get("entities"):
        # Check if we got data for any entity
        has_data = any(
            entity_info["data"].get("price") or 
            entity_info["data"].get("historical_data") or 
            entity_info["data"].get("fundamentals_data")
            for entity_info in context["entities"].values()
        )
    else:
        # No entities structure (market/general query)
        has_data = (
            context.get("price") is not None or 
            context.get("historical_data") is not None or
            context.get("fundamentals_data") is not None or
            context.get("market_data") is not None
        )
    
    if not has_data and entities_list:
        # No data found - let LLM explain the issue
        print("⚠️  No data found for entities")
        context['error'] = f"Could not find data for '{', '.join(entities_list)}'"
        if not entities_metadata:
            context['error'] = f"Could not find symbols for '{', '.join(entities_list)}'. Please check the tickers or company names."
    
    # ========================================================================
    # STEP 6: Generate Answer using LLM
    # ========================================================================
    llm_answer = generate_answer(context, user_query)
    
    # ========================================================================
    # STEP 7: Validate Response
    # ========================================================================
    validated_answer, answer_confidence = validate_response(llm_answer, context)
    
    # ========================================================================
    # STEP 8: Build and Return Response
    # ========================================================================
    response = QueryResponse(
        answer=validated_answer,
        citations=extract_citations(context),
        confidence=answer_confidence,
        data_timestamp=context.get("timestamp", datetime.utcnow().isoformat()),
        context={
            "sources_used": [query_type_enum.value],
            "classification_confidence": confidence,
            "entities": entities_list,
            "resolved_symbols": resolved_symbols,
            "data": context
        }
    )
    
    return response


async def fetch_data_by_classification(
    symbol_or_query: str,
    query_types: List[QueryType],
    date_range: Optional[dict] = None
) -> Dict:
    """
    Fetch data from appropriate sources based on query classification.
    
    Args:
        symbol_or_query: Either a resolved symbol (e.g., "BTC-USD", "AAPL") 
                        or the original query if no symbol was resolved
        query_types: List of QueryType enums indicating what data to fetch
        date_range: Optional dict with 'from' and 'to' keys for date-based queries
    
    Maps query types to data sources:
    - PRICE → Mboum API (real-time quote for stocks)
    - HISTORICAL → FMP API (historical-price-full)
    - FUNDAMENTALS → FMP API (income-statement)
    - NEWS → RAG (future)
    - MARKET → Mboum API (same endpoint, handles indexes like ^GSPC)
    - ANALYSIS → Multiple sources (price + fundamentals + historical)
    """
    print(f"📡 Fetching data for query types: {[qt.value for qt in query_types]}")
    if date_range:
        print(f"📅 Date range: {date_range.get('from')} to {date_range.get('to')}")

    # Determine if we have a symbol or need to extract one
    # If symbol_or_query looks like a ticker (short, uppercase, with possible -, ., ^)
    # use it directly, otherwise try to extract from query
    ticker = symbol_or_query
    if ' ' in symbol_or_query:
        # It's a query, not a symbol - try to extract ticker
        context = build_context(symbol_or_query)
        ticker = context.get("ticker")
    else:
        # It's likely a resolved symbol - use it directly
        context = {"ticker": ticker, "query": symbol_or_query}

    # Track which external sources were queried for citation building
    context["sources_queried"] = []

    price_fetcher = PriceFetcher()
    fmp_fetcher = FMPFetcher()

    tasks = []
    labels: List[str] = []

    def _has_ticker() -> bool:
        return bool(ticker) and ticker != "UNKNOWN"

    # PRICE → Mboum + FMP price-change (for context)
    if QueryType.PRICE in query_types and _has_ticker():
        tasks.append(price_fetcher.fetch_with_timeout(ticker))
        labels.append("price")
        context["sources_queried"].append("Mboum API - real-time quote")
        
        # Also fetch price change summary for richer context
        tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="price_change"))
        labels.append("price_change")
        context["sources_queried"].append("FMP Price Change API")

    # HISTORICAL → FMP historical-price-full + price-change (for comparisons)
    if QueryType.HISTORICAL in query_types and _has_ticker():
        # Pass date range if available
        fetch_kwargs = {"mode": "historical"}
        if date_range:
            fetch_kwargs["from_date"] = date_range.get("from")
            fetch_kwargs["to_date"] = date_range.get("to")
        tasks.append(fmp_fetcher.fetch_with_timeout(ticker, **fetch_kwargs))
        labels.append("historical")
        context["sources_queried"].append("FMP Historical API")
        
        # Also fetch price change summary for comparisons and context
        tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="price_change"))
        labels.append("price_change")
        context["sources_queried"].append("FMP Price Change API")

    # FUNDAMENTALS → FMP income-statement
    if QueryType.FUNDAMENTALS in query_types and _has_ticker():
        tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="fundamentals"))
        labels.append("fundamentals")
        context["sources_queried"].append("FMP Fundamentals API")

    # MARKET → Mboum (same endpoint as PRICE, handles indexes like ^GSPC)
    if QueryType.MARKET in query_types:
        market_symbol = ticker if _has_ticker() else "^GSPC"
        tasks.append(price_fetcher.fetch_with_timeout(market_symbol))
        labels.append("market")
        context["sources_queried"].append("Mboum API - market/index quote")

    # ANALYSIS → ensure we have as much structured data as possible
    if QueryType.ANALYSIS in query_types and _has_ticker():
        # If not already requested above, add missing core data sources.
        if "price" not in labels:
            tasks.append(price_fetcher.fetch_with_timeout(ticker))
            labels.append("price")
            context["sources_queried"].append("Mboum API - real-time quote")
        if "historical" not in labels:
            # Pass date range if available
            fetch_kwargs = {"mode": "historical"}
            if date_range:
                fetch_kwargs["from_date"] = date_range.get("from")
                fetch_kwargs["to_date"] = date_range.get("to")
            tasks.append(fmp_fetcher.fetch_with_timeout(ticker, **fetch_kwargs))
            labels.append("historical")
            context["sources_queried"].append("FMP Historical API")
        if "fundamentals" not in labels:
            tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="fundamentals"))
            labels.append("fundamentals")
            context["sources_queried"].append("FMP Fundamentals API")
        if "price_change" not in labels:
            tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="price_change"))
            labels.append("price_change")
            context["sources_queried"].append("FMP Price Change API")

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                # Swallow fetch errors into context for debugging,
                # but do not crash the whole orchestration flow.
                context.setdefault("fetch_errors", []).append(
                    {"source": label, "error": str(result)}
                )
                continue

            if not isinstance(result, dict):
                continue

            status = result.get("status")
            if status and status != "success":
                # Surface structured error responses but don't raise.
                context.setdefault("fetch_errors", []).append(
                    {"source": label, "error": result}
                )

            if label == "price" and status == "success":
                # Normalize into top-level price fields expected by validator & LLM
                context["ticker"] = result.get("ticker", ticker)
                if "price" in result:
                    context["price"] = result["price"]
                if "change_percent" in result and result["change_percent"] is not None:
                    context["change_percent"] = result["change_percent"]
                if "change" in result and result["change"] is not None:
                    context["change"] = result["change"]
                context.setdefault("price_data", result)
                context["timestamp"] = result.get(
                    "timestamp", context.get("timestamp", datetime.utcnow().isoformat())
                )

            elif label == "historical" and status == "success":
                context["historical_data"] = result

            elif label == "fundamentals" and status == "success":
                context["fundamentals_data"] = result

            elif label == "market" and status == "success":
                # Market data uses same structure as price data (from Mboum)
                context["market_data"] = result
                # Also normalize into top-level fields if it's an index
                if "price" in result:
                    context["market_price"] = result["price"]
                if "change_percent" in result and result["change_percent"] is not None:
                    context["market_change_percent"] = result["change_percent"]
            
            elif label == "price_change" and status == "success":
                # Price change summary data from FMP
                context["price_change_data"] = result

    # Ensure we always have a timestamp
    context.setdefault("timestamp", datetime.utcnow().isoformat())

    return context


def extract_citations(context: Dict) -> List[Citation]:
    """ 
    Extract citations from context data.
    
    For now: Returns empty list (no external sources yet)
    Future: Will extract from RAG documents, API sources
    """
    citations = []
    
    # TODO: When RAG is implemented, extract document sources
    # if "news_articles" in context:
    #     for article in context["news_articles"]:
    #         citations.append(Citation(
    #             source=article["title"],
    #             url=article["url"]
    #         ))
    
    # Add source attribution
    if "sources_queried" in context:
        for source in context["sources_queried"]:
            citations.append(Citation(
                source=source,
                url=""  # Will add URLs when APIs are integrated
            ))
    
    return citations


def classify_query(user_query: str) -> str:
    """
    DEPRECATED: Old classification function.
    Now uses LLM-based classification instead of rule-based.
    
    Kept for backward compatibility.
    """
    # Use new LLM-based classification (returns 6 values now)
    query_type_str, _, _, _, _, _ = llm_classify_query(user_query)
    return query_type_str
