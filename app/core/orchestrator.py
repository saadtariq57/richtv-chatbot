"""
Query Orchestrator - Coordinates the flow from query to response

Now with intelligent query classification and multi-source routing,
backed by real Mboum & FMP API integrations.
"""

from datetime import datetime
from typing import Dict, List
import asyncio

from app.api.schemas import QueryResponse, Citation
from app.core.classifier import get_classifier, QueryType
from app.context.builder import build_context, is_valid_ticker
from app.llm.generator import generate_answer, llm_quick_check, llm_extract_company_name
from app.core.validator import validate_response
from app.data_fetchers.price_fetcher import PriceFetcher
from app.data_fetchers.fmp_fetcher import FMPFetcher
from app.utils.ticker_resolver import resolve_ticker, extract_company_name_from_query


async def orchestrate_query(user_query: str) -> QueryResponse:
    """
    Main orchestration flow with intelligent classification-based routing.
    
    Flow:
    1. Classify query → determine data sources needed
    2. Fetch data from appropriate sources
    3. Generate LLM answer
    4. Validate response
    5. Return structured response
    
    Args:
        user_query: User's financial question
        
    Returns:
        QueryResponse with validated answer and metadata
    """
    # Step 1: Classify the query
    classifier = get_classifier()
    classification = classifier.classify(user_query)
    
    print(f"Query classified as: {[qt.value for qt in classification.query_types]}")
    print(f"   Confidence: {classification.confidence}")
    print(f"   Matched patterns: {classification.matched_patterns}")
    
    # Step 1.5: LLM Quick Check for low/medium confidence (Tier 2 assistance)
    # Helps catch queries that rule-based patterns miss or misclassify
    if classification.confidence in ["low", "medium"] and not classification.llm_answer:
        print(f"Low/medium confidence detected - using LLM quick check")
        intent, llm_ticker = llm_quick_check(user_query)
        print(f"   LLM quick check result: intent={intent}, ticker={llm_ticker}")
        
        if intent == "needs_data" and llm_ticker:
            # LLM identified a specific stock query with ticker
            # Override classification to PRICE with extracted ticker
            classification.query_types = [QueryType.PRICE]
            classification.llm_ticker = llm_ticker
            classification.confidence = "medium"  # LLM-assisted
            print(f"   Reclassified as PRICE with ticker: {llm_ticker}")
            
        elif intent == "general":
            # LLM identified this as a conceptual question
            # We need to make another call to get the answer
            from app.llm.generator import classify_and_answer_if_general
            _, answer, _ = classify_and_answer_if_general(user_query)
            if answer:
                classification.query_types = [QueryType.GENERAL]
                classification.llm_answer = answer
                classification.confidence = "medium"
                print(f"   Reclassified as GENERAL with LLM answer")
        
        # If intent is "unclear", keep original classification (might fail gracefully)
    
    # Step 1.6: Additional check for invalid tickers (even if confidence is high)
    # This catches cases like "Apple" being extracted as "APPLE" instead of "AAPL"
    if not classification.llm_ticker and not classification.llm_answer:
        # Build a temporary context to check the ticker
        temp_context = build_context(user_query)
        extracted_ticker = temp_context.get("ticker")
        
        # If ticker looks invalid, try multiple resolution strategies
        if not is_valid_ticker(extracted_ticker):
            print(f"Invalid ticker detected: '{extracted_ticker}' - attempting resolution")
            
            # Strategy 1: Try Mboum search (best for new IPOs and comprehensive coverage)
            company_name = extract_company_name_from_query(user_query)
            if company_name:
                print(f"   Trying Mboum search for: '{company_name}'")
                mboum_ticker = await resolve_ticker(company_name)
                if mboum_ticker:
                    classification.llm_ticker = mboum_ticker
                    print(f"   Mboum resolved ticker: {mboum_ticker}")
                else:
                    # Strategy 2: Fallback to LLM (for well-known companies in training data)
                    print(f"   Mboum search failed, trying LLM fallback")
                    intent, llm_ticker = llm_quick_check(user_query)
                    print(f"   LLM quick check result: intent={intent}, ticker={llm_ticker}")
                    
                    if intent == "needs_data" and llm_ticker:
                        classification.llm_ticker = llm_ticker
                        print(f"   Using LLM-extracted ticker: {llm_ticker}")
                    elif intent == "general":
                        # Actually a general question, not a ticker query
                        from app.llm.generator import classify_and_answer_if_general
                        _, answer, _ = classify_and_answer_if_general(user_query)
                        if answer:
                            classification.query_types = [QueryType.GENERAL]
                            classification.llm_answer = answer
                            print(f"   Reclassified as GENERAL")
    
    # Handle GENERAL queries (answered by LLM without data fetching)
    if QueryType.GENERAL in classification.query_types and classification.llm_answer:
        print("GENERAL query detected with pre-generated answer")
        context = build_context(user_query)
        context["timestamp"] = datetime.utcnow().isoformat()
        
        return QueryResponse(
            answer=classification.llm_answer,
            citations=[Citation(source="LLM Knowledge", url="")],
            confidence=0.80,  # Medium-high for general conceptual answers
            data_timestamp=context["timestamp"],
            context={
                "sources_used": ["general"],
                "classification_confidence": classification.confidence,
                "data": context
            }
        )
    
    # Step 2: Route to appropriate data sources based on classification
    # If LLM extracted a ticker, inject it into the query for better context building
    query_for_fetch = user_query
    if classification.llm_ticker:
        print(f"LLM extracted ticker: {classification.llm_ticker}")
        query_for_fetch = f"{classification.llm_ticker} {user_query}"
    
    context = await fetch_data_by_classification(query_for_fetch, classification.query_types)
    
    print(f"Sample Context: {context}")
    
    # Step 3: Generate answer using LLM
    llm_answer = generate_answer(context, user_query)
    
    # Step 4: Validate response against context
    validated_answer, confidence = validate_response(llm_answer, context)
    
    # Step 5: Build response
    response = QueryResponse(
        answer=validated_answer,
        citations=extract_citations(context),
        confidence=confidence,
        data_timestamp=context.get("timestamp", datetime.utcnow().isoformat()),
        context={
            "sources_used": [qt.value for qt in classification.query_types],
            "classification_confidence": classification.confidence,
            "data": context
        }
    )
    
    # Step 6: Post-Failure LLM Rescue (Option A)
    # If we got "insufficient data", try one more time with LLM-extracted company name
    if "insufficient data" in response.answer.lower() and confidence < 0.5:
        print("Insufficient data detected - attempting LLM rescue")
        
        # Use LLM to extract company/asset name
        llm_company_name = await llm_extract_company_name(user_query)
        
        if llm_company_name:
            print(f"   LLM extracted company name: '{llm_company_name}'")
            
            # Try to resolve ticker via Mboum search
            rescue_ticker = await resolve_ticker(llm_company_name)
            
            if rescue_ticker:
                print(f"   Resolved to ticker: {rescue_ticker}")
                
                # Rebuild the query with the correct ticker
                rescue_query = f"{rescue_ticker} {user_query}"
                
                # Re-fetch data with the correct ticker
                rescue_context = await fetch_data_by_classification(
                    rescue_query,
                    classification.query_types
                )
                
                # Check if we actually got data this time
                if rescue_context.get("price") or rescue_context.get("historical_data"):
                    print("   Rescue successful! Re-generating answer with new data")
                    
                    # Re-generate answer with new context
                    rescue_answer = generate_answer(rescue_context, user_query)
                    rescue_validated, rescue_confidence = validate_response(
                        rescue_answer, rescue_context
                    )
                    
                    # Build new response with rescued data
                    response = QueryResponse(
                        answer=rescue_validated,
                        citations=extract_citations(rescue_context),
                        confidence=rescue_confidence,
                        data_timestamp=rescue_context.get(
                            "timestamp", datetime.utcnow().isoformat()
                        ),
                        context={
                            "sources_used": [qt.value for qt in classification.query_types],
                            "classification_confidence": classification.confidence,
                            "data": rescue_context,
                            "rescue_applied": True,
                            "llm_extracted_name": llm_company_name
                        }
                    )
                    print(f"   Final rescue confidence: {rescue_confidence:.2f}")
                else:
                    print("   Rescue failed - still no data available")
            else:
                print("   Could not resolve company name to ticker")
        else:
            print("   LLM could not extract company name")
    
    return response


async def fetch_data_by_classification(
    user_query: str,
    query_types: List[QueryType]
) -> Dict:
    """
    Fetch data from appropriate sources based on query classification.
    
    Maps query types to data sources:
    - PRICE → Mboum API (real-time quote for stocks)
    - HISTORICAL → FMP API (historical-price-full)
    - FUNDAMENTALS → FMP API (income-statement)
    - NEWS → RAG (future)
    - MARKET → Mboum API (same endpoint, handles indexes like ^GSPC)
    - ANALYSIS → Multiple sources (price + fundamentals + historical)
    """
    print(f"Fetching data for query types: {[qt.value for qt in query_types]}")

    # Start with base context (ticker + raw query)
    context = build_context(user_query)
    ticker = context.get("ticker")

    # Track which external sources were queried for citation building
    context["sources_queried"] = []

    price_fetcher = PriceFetcher()
    fmp_fetcher = FMPFetcher()

    tasks = []
    labels: List[str] = []

    def _has_ticker() -> bool:
        return bool(ticker) and ticker != "UNKNOWN"

    # PRICE → Mboum
    if QueryType.PRICE in query_types and _has_ticker():
        tasks.append(price_fetcher.fetch_with_timeout(ticker))
        labels.append("price")
        context["sources_queried"].append("Mboum API - real-time quote")

    # HISTORICAL → FMP historical-price-full
    if QueryType.HISTORICAL in query_types and _has_ticker():
        tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="historical"))
        labels.append("historical")
        context["sources_queried"].append("FMP Historical API")

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
            tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="historical"))
            labels.append("historical")
            context["sources_queried"].append("FMP Historical API")
        if "fundamentals" not in labels:
            tasks.append(fmp_fetcher.fetch_with_timeout(ticker, mode="fundamentals"))
            labels.append("fundamentals")
            context["sources_queried"].append("FMP Fundamentals API")

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
    Use query_classifier.py instead.
    
    Kept for backward compatibility.
    """
    classifier = get_classifier()
    result = classifier.classify(user_query)
    
    if result.query_types:
        return result.query_types[0].value
    return 'general'
