import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.llm.client import get_llm_client
from app.llm.budget import get_default_chat_history_token_budget
from app.llm.prompt_builder import (
    build_chat_history_section,
    build_prompt,
    format_labeled_section,
)
from app.llm.budget import PromptSection


def _chat_history_token_cap(effective_input_budget: int) -> int:
    """Reserve a bounded slice of the prompt budget for raw chat history."""

    return min(get_default_chat_history_token_budget(), effective_input_budget)


def _build_budgeted_prompt(
    *,
    llm,
    required_sections: List[PromptSection],
    chat_history: Optional[List[Dict[str, str]]] = None,
    chat_history_title: str = "Previous conversation",
) -> str:
    """Build a prompt within budget, with a compact fallback if needed."""

    budget = llm.default_budget
    sections = list(required_sections)

    if chat_history:
        sections.insert(
            1,
            build_chat_history_section(
                chat_history,
                priority=10,
                llm_client=llm,
                max_tokens=_chat_history_token_cap(budget.effective_input_budget),
                title=chat_history_title,
                required=True,
            ),
        )

    try:
        build_result = build_prompt(sections, budget=budget, llm_client=llm)
        return build_result.prompt
    except ValueError:
        fallback_sections = [
            section
            for section in required_sections
            if section.name != "data"
        ]

        data_section = next(
            (section for section in required_sections if section.name == "data"),
            None,
        )
        if data_section is not None:
            compact_data = _compact_labeled_json_section("Data", data_section.text)
            fallback_sections.insert(
                len(fallback_sections) - 2,
                PromptSection(
                    name="data",
                    text=compact_data,
                    priority=3,
                    required=True,
                ),
            )

        fallback_result = build_prompt(
            fallback_sections,
            budget=budget,
            llm_client=llm,
        )
        return fallback_result.prompt


def _compact_labeled_json_section(title: str, labeled_section_text: str) -> str:
    """Re-serialize a labeled JSON section in compact form when the prompt is too large."""

    prefix = f"{title}:\n"
    if not labeled_section_text.startswith(prefix):
        return labeled_section_text

    payload = labeled_section_text[len(prefix):].strip()
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return labeled_section_text

    return format_labeled_section(
        title,
        json.dumps(parsed, separators=(",", ":"), ensure_ascii=True),
    )


def generate_conversational_answer(
    user_query: str,
    chat_history: List[Dict[str, str]],
) -> str:
    """
    Answer a general/conversational question using only the chat history as context.

    Used when the user asks something about the conversation itself (e.g. "what
    did I just ask?") or any general question where the history IS the relevant
    data — not financial market data.
    """
    llm = get_llm_client()
    prompt = _build_budgeted_prompt(
        llm=llm,
        required_sections=[
            PromptSection(
                name="system_instructions",
                text=(
                    "You are RichTVBot, a knowledgeable financial assistant "
                    "with memory of the current conversation."
                ),
                priority=1,
                required=True,
            ),
            PromptSection(
                name="user_question",
                text=f"User Question: {user_query}",
                priority=2,
                required=True,
            ),
            PromptSection(
                name="answer_instruction",
                text="Answer using the conversation history above. Be concise and accurate.",
                priority=3,
                required=True,
            ),
        ],
        chat_history=chat_history,
    )
    response = llm.generate(
        prompt,
        temperature=0.3,
        max_output_tokens=llm.default_budget.reserved_output_tokens,
    )
    return response or "I couldn't generate a response."


def generate_answer(
    context: dict,
    user_query: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Generate an answer using LLM based on structured context.

    Args:
        context: Structured financial data from fetchers
        user_query: User's question
        chat_history: Optional list of {"role": "user"|"assistant", "content": "..."} for context

    Returns:
        Generated answer text
    """
    # Get current date for temporal context
    current_date = datetime.utcnow().strftime("%B %d, %Y")  # e.g., "February 20, 2026"
    current_date_iso = datetime.utcnow().strftime("%Y-%m-%d")  # e.g., "2026-02-20"

    llm = get_llm_client()
    prompt = _build_budgeted_prompt(
        llm=llm,
        required_sections=[
            PromptSection(
                name="system_instructions",
                text=f"""You are RichTVBot, a knowledgeable financial assistant. Answer the user's question using ONLY the provided data.

CURRENT DATE: {current_date} (ISO: {current_date_iso})

When the user asks about "today", "now", "current", or relative dates, use this as your reference point.

CRITICAL RULES:
1. NEVER invent, estimate, or fabricate numbers
2. Use ONLY the exact data provided below
3. If data is insufficient, say "I don't have enough data to answer that"
4. DO NOT repeat the same information multiple times in your response
5. Think step by step: state your reasoning before your conclusion. Ensure your conclusion follows from the data.

RESPONSE STYLE:
- Start with a clear summary that reflects the data. Do not state a conclusion until you have compared or verified the numbers.
- Provide context and narrative, not just raw numbers
- Group related information logically
- Highlight notable trends or outliers
- Use natural, engaging language while staying professional
- For market overviews: organize by sector/category, identify top movers
- For price queries: include relevant context like day's range, volume if available
- For comparisons: highlight key differences and similarities
- Add timestamp context when relevant (e.g., "as of today", "current prices")

FORMATTING:
- Use clear, readable structure
- Bold key stock symbols for emphasis (e.g., **NVDA**)
- Use bullet points or natural paragraphs as appropriate
- Include percentage changes in context, not just isolated numbers""",
                priority=1,
                required=True,
            ),
            PromptSection(
                name="data",
                text=format_labeled_section("Data", json.dumps(context, indent=2)),
                priority=3,
                required=True,
            ),
            PromptSection(
                name="user_question",
                text=f"User Question: {user_query}",
                priority=4,
                required=True,
            ),
            PromptSection(
                name="answer_instruction",
                text="Answer:",
                priority=5,
                required=True,
            ),
        ],
        chat_history=chat_history,
        chat_history_title="Previous conversation (for context)",
    )

    # Use LLM client with lower temperature for more consistent reasoning
    response = llm.generate(
        prompt,
        temperature=0.4,
        max_output_tokens=llm.default_budget.reserved_output_tokens,
    )
    
    if response:
        return response
    else:
        return "I have insufficient data to answer this question."


def classify_and_answer_if_general(user_query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Combined LLM call to classify intent and answer if it's a general question.
    
    This is used when rule-based patterns don't match, to determine:
    1. Is this a general financial question? → Answer it directly
    2. Is this about a specific stock? → Extract ticker for data fetching
    3. Is it unclear/off-topic? → Reject it
    
    Args:
        user_query: User's question
        
    Returns:
        Tuple of (classification, answer, ticker):
        - ("general", "Answer text", None) if general question
        - ("specific", None, "NVDA") if specific stock query
        - ("unclear", None, None) if off-topic/unclear
    """
    prompt = f"""
You are a financial query analyzer. Analyze this user query and respond in ONE of these formats:

1. If it's a GENERAL financial/investing question (concepts, definitions, how things work):
   → Provide a clear, concise answer
   → Format: ANSWER: [your answer here]

2. If it's about a SPECIFIC stock, company, or ticker:
   → Extract the ticker symbol (or best guess if company name given)
   → Format: NEEDS_DATA: [TICKER]

3. If it's unclear, off-topic, or not about finance/investing:
   → Format: CANNOT_ANSWER

Examples:
- "What is a dividend?" → ANSWER: A dividend is a payment made by a corporation to its shareholders...
- "How much is Apple trading at?" → NEEDS_DATA: AAPL
- "What's NVDA price?" → NEEDS_DATA: NVDA
- "Tell me about Tesla stock" → NEEDS_DATA: TSLA
- "What's the weather?" → CANNOT_ANSWER

User Query: "{user_query}"

Your Response:"""
    
    # Use LLM client
    llm = get_llm_client()
    response = llm.generate(prompt, temperature=0.3)
    
    if not response:
        return ("unclear", None, None)
    
    # Parse the response
    if response.startswith("ANSWER:"):
        # It's a general question with an answer
        clean_answer = response.replace("ANSWER:", "").strip()
        return ("general", clean_answer, None)
        
    elif response.startswith("NEEDS_DATA:"):
        # It's a specific stock query
        ticker = response.replace("NEEDS_DATA:", "").strip()
        return ("specific", None, ticker)
        
    else:  # CANNOT_ANSWER or unexpected format
        return ("unclear", None, None)


def llm_quick_check(user_query: str) -> Tuple[str, Optional[str]]:
    """
    Lightweight LLM check for queries with low/medium confidence.
    
    Used when rule-based classification is uncertain.
    Much cheaper and faster than full classification+answer.
    
    Args:
        user_query: User's question
        
    Returns:
        Tuple of (intent, ticker):
        - ("needs_data", "NVDA") if about specific stock
        - ("general", None) if conceptual question
        - ("unclear", None) if off-topic
    """
    prompt = f"""
Quick intent check for: "{user_query}"

Respond with ONE line only:
- DATA:<TICKER> (if asking about a specific stock/company, provide ticker symbol)
- GENERAL (if asking a conceptual/educational financial question)
- UNCLEAR (if off-topic or can't determine)

Examples:
- "Should I invest in tech stocks?" → GENERAL
- "Tell me about Apple stock" → DATA:AAPL
- "What's NVDA trading at?" → DATA:NVDA
- "How does compound interest work?" → GENERAL
- "What's the weather?" → UNCLEAR

Response:"""
    
    # Use LLM client
    llm = get_llm_client()
    response = llm.generate(prompt, temperature=0.2)
    
    if not response:
        return ("unclear", None)
    
    # Parse response
    if response.startswith("DATA:"):
        ticker = response.replace("DATA:", "").strip()
        return ("needs_data", ticker)
    elif response.startswith("GENERAL"):
        return ("general", None)
    else:
        return ("unclear", None)


async def llm_extract_company_name(user_query: str) -> Optional[str]:
    """
    Use LLM to extract company/asset name from query.
    
    This is a fallback when regex-based extraction fails.
    Used in post-failure rescue when initial query returns insufficient data.
    
    Args:
        user_query: User's original question
        
    Returns:
        Extracted company/asset name or None
    """
    llm = get_llm_client()
    
    prompt = f"""
Extract ONLY the company or asset name from this query. Return just the name, nothing else.

Examples:
- "What's Figma trading at?" → Figma
- "Tell me Nvidia's price" → Nvidia
- "How much for Tesla?" → Tesla
- "Show me Apple stock" → Apple
- "Bitcoin value?" → Bitcoin
- "Price of Coinbase?" → Coinbase
- "What is SAP worth?" → SAP

Query: "{user_query}"

Answer (company/asset name only):"""
    
    response = await llm.generate_async(prompt, temperature=0.1)
    
    if response:
        # Clean up the response
        cleaned = response.strip().strip('"\'.,!?')
        return cleaned if cleaned else None
    
    return None


def llm_classify_query(user_query: str) -> Tuple[str, str, Optional[List[str]], Optional[str], Optional[List[str]], Optional[dict]]:
    """
    Use LLM to classify query intent and extract entities/symbols/dates.
    
    OPTIMIZED: Answers general queries immediately in one call!
    SMART: For market queries, LLM determines which symbols to fetch!
    MULTI-ENTITY: Supports comparison queries with multiple companies!
    DATE-AWARE: Extracts date ranges for historical queries!
    
    This replaces the rule-based classification system with a more flexible
    LLM-based approach that understands informal language and context.
    
    Args:
        user_query: User's question
        
    Returns:
        Tuple of (query_type, confidence, entities_list, answer, symbols_list, date_range):
        - query_type: "price", "historical", "fundamentals", "analysis", "market", or "general"
        - confidence: "high", "medium", or "low"
        - entities_list: List of entities (company names, tickers) or None
        - answer: Complete answer if general query, None if needs data fetching
        - symbols_list: List of symbols to fetch (only for MARKET queries)
        - date_range: Dict with "from" and "to" keys in YYYY-MM-DD format, or None
    """
    # Get current date for temporal context
    current_date = datetime.utcnow()
    current_date_str = current_date.strftime("%Y-%m-%d")  # e.g., "2026-02-20"
    
    # Calculate common relative dates for the LLM's reference
    seven_days_ago = (current_date - timedelta(days=7)).strftime("%Y-%m-%d")
    one_month_ago = (current_date - timedelta(days=30)).strftime("%Y-%m-%d")
    three_months_ago = (current_date - timedelta(days=90)).strftime("%Y-%m-%d")
    six_months_ago = (current_date - timedelta(days=180)).strftime("%Y-%m-%d")
    one_year_ago = (current_date - timedelta(days=365)).strftime("%Y-%m-%d")
    two_years_ago = (current_date - timedelta(days=730)).strftime("%Y-%m-%d")
    
    prompt = f"""
You are a financial query classifier and data planner.

CURRENT DATE: {current_date_str}

Use this date when interpreting relative time references:
- "today" / "now" = {current_date_str}
- "last 7 days" / "last week" = from {seven_days_ago} to {current_date_str}
- "last month" / "last 30 days" = from {one_month_ago} to {current_date_str}
- "last 3 months" / "last quarter" = from {three_months_ago} to {current_date_str}
- "last 6 months" = from {six_months_ago} to {current_date_str}
- "last year" / "last 12 months" = from {one_year_ago} to {current_date_str}
- "last 2 years" = from {two_years_ago} to {current_date_str}
- "2 years ago" (as starting point) = {two_years_ago}

IMPORTANT: 
1. If the query is a GENERAL conceptual question, provide a complete answer immediately.
2. If the query is a MARKET overview request, provide a LIST of symbols to fetch.
3. For other data queries, just extract the entity.
4. For HISTORICAL queries with date ranges, extract dates in YYYY-MM-DD format.
5. When user asks about COVID crash, use date range: from=2020-02-20, to=2020-03-23
6. For broad market questions WITHOUT specific entity (e.g., "Performance during COVID"), extract market indices as entities (S&P 500, Dow, Nasdaq)

Query Types:
1. PRICE - Single asset price
   → Extract entity, NO answer, NO dates
   
2. HISTORICAL - Single asset history
   → Extract entity, NO answer
   → If specific date range mentioned, extract FROM and TO dates
   → Convert dates to YYYY-MM-DD format (e.g., "1 Jan 2020" → "2020-01-01")
   
3. FUNDAMENTALS - Single asset financials
   → Extract entity, NO answer, NO dates
   
4. ANALYSIS - Single asset analysis
   → Extract entity, NO answer, NO dates
   
5. MARKET - Market overview (REQUIRES MULTIPLE SYMBOLS!)
   → Provide symbol list based on context
   → Include: Major indices, top stocks, crypto, commodities
   → Adapt based on query focus (tech, crypto, general, etc.)
   
6. GENERAL - Conceptual questions
   → Provide COMPLETE answer immediately

MARKET Query Guidelines:
- General market: Include indices (^GSPC, ^DJI, ^IXIC), top stocks (AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA), crypto (BTC-USD, ETH-USD), commodities (GC=F, CL=F)
- Tech focus: Nasdaq (^IXIC), tech giants (AAPL, MSFT, NVDA, GOOGL, META, AMZN, TSLA)
- AI stocks focus: Nasdaq (^IXIC), AI leaders (NVDA, MSFT, GOOGL, META, AAPL, AMD, TSLA, AMZN, SMCI, PLTR)
- Crypto focus: Major cryptos (BTC-USD, ETH-USD, SOL-USD, BNB-USD, XRP-USD, ADA-USD)
- Commodities focus: Gold (GC=F), Silver (SI=F), Oil (CL=F), Natural Gas (NG=F)
- MAX 20 symbols total
- Include ONE relevant index for context, avoid duplicating it in response

Response Format:

For MARKET queries:
TYPE: market
CONFIDENCE: [high/medium/low]
ENTITIES: NONE
SYMBOLS: ^GSPC, ^DJI, ^IXIC, AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA, BTC-USD, ETH-USD, GC=F, CL=F
DATE_RANGE: NONE
ANSWER: NONE

For HISTORICAL queries WITH date range:
TYPE: historical
CONFIDENCE: [high/medium/low]
ENTITIES: [company/ticker]
SYMBOLS: NONE
DATE_RANGE: from=YYYY-MM-DD, to=YYYY-MM-DD
ANSWER: NONE

For HISTORICAL queries WITHOUT specific date range:
TYPE: historical
CONFIDENCE: [high/medium/low]
ENTITIES: [company/ticker]
SYMBOLS: NONE
DATE_RANGE: NONE
ANSWER: NONE

For PRICE/FUNDAMENTALS/ANALYSIS queries:
TYPE: [price/fundamentals/analysis]
CONFIDENCE: [high/medium/low]
ENTITIES: [comma-separated list of companies/tickers, e.g., "Apple, NVIDIA" for comparisons]
SYMBOLS: NONE
DATE_RANGE: NONE
ANSWER: NONE

For GENERAL queries:
TYPE: general
CONFIDENCE: [high/medium/low]
ENTITIES: NONE
SYMBOLS: NONE
DATE_RANGE: NONE
ANSWER: [complete answer]

Examples:

Query: "Give me market update"
TYPE: market
CONFIDENCE: high
ENTITIES: NONE
SYMBOLS: ^GSPC, ^DJI, ^IXIC, AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA, BTC-USD, ETH-USD, GC=F, CL=F
DATE_RANGE: NONE
ANSWER: NONE

Query: "How's tech doing?"
TYPE: market
CONFIDENCE: high
ENTITIES: NONE
SYMBOLS: ^IXIC, AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA, META
DATE_RANGE: NONE
ANSWER: NONE

Query: "What's happening with AI stocks?"
TYPE: market
CONFIDENCE: high
ENTITIES: NONE
SYMBOLS: ^IXIC, NVDA, MSFT, GOOGL, META, AAPL, AMD, TSLA, AMZN, SMCI, PLTR
DATE_RANGE: NONE
ANSWER: NONE

Query: "What's Apple price?"
TYPE: price
CONFIDENCE: high
ENTITIES: Apple
SYMBOLS: NONE
DATE_RANGE: NONE
ANSWER: NONE

Query: "Show Apple performance from 1 Jan 2020 to 15 March 2020"
TYPE: historical
CONFIDENCE: high
ENTITIES: Apple
SYMBOLS: NONE
DATE_RANGE: from=2020-01-01, to=2020-03-15
ANSWER: NONE

Query: "Compare Apple and NVIDIA performance last month"
TYPE: historical
CONFIDENCE: high
ENTITIES: Apple, NVIDIA
SYMBOLS: NONE
DATE_RANGE: from={one_month_ago}, to={current_date_str}
ANSWER: NONE

Query: "Performance during COVID crash"
TYPE: historical
CONFIDENCE: high
ENTITIES: S&P 500, Dow Jones, Nasdaq
SYMBOLS: NONE
DATE_RANGE: from=2020-02-20, to=2020-03-23
ANSWER: NONE

Query: "What is a dividend?"
TYPE: general
CONFIDENCE: high
ENTITIES: NONE
SYMBOLS: NONE
DATE_RANGE: NONE
ANSWER: A dividend is a payment made by a corporation to its shareholders, usually as a distribution of profits. Companies pay dividends on a per-share basis, typically quarterly.

User Query: "{user_query}"

Your Response:"""
    
    llm = get_llm_client()
    response = llm.generate(prompt, temperature=0.3)
    
    if not response:
        return ("general", "low", None, None, None, None)
    
    # Parse the response
    query_type = "general"
    confidence = "low"
    entities_list = None
    answer = None
    symbols_list = None
    date_range = None
    
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith("TYPE:"):
            query_type = line.replace("TYPE:", "").strip().lower()
        elif line.startswith("CONFIDENCE:"):
            confidence = line.replace("CONFIDENCE:", "").strip().lower()
        elif line.startswith("ENTITIES:"):
            entities_val = line.replace("ENTITIES:", "").strip()
            if entities_val and entities_val.upper() != "NONE":
                # Parse comma-separated entities
                entities_list = [e.strip() for e in entities_val.split(",") if e.strip()]
        elif line.startswith("SYMBOLS:"):
            symbols_val = line.replace("SYMBOLS:", "").strip()
            if symbols_val and symbols_val.upper() != "NONE":
                # Parse comma-separated symbols
                symbols_list = [s.strip() for s in symbols_val.split(",") if s.strip()]
        elif line.startswith("DATE_RANGE:"):
            date_val = line.replace("DATE_RANGE:", "").strip()
            if date_val and date_val.upper() != "NONE":
                # Parse date range: "from=2020-01-01, to=2020-03-15"
                date_range = {}
                for part in date_val.split(","):
                    part = part.strip()
                    if "=" in part:
                        key, val = part.split("=", 1)
                        date_range[key.strip()] = val.strip()
        elif line.startswith("ANSWER:"):
            answer_val = line.replace("ANSWER:", "").strip()
            if answer_val and answer_val.upper() != "NONE":
                # Collect all remaining lines as the answer
                answer_start = response.find("ANSWER:")
                answer = response[answer_start + 7:].strip()
                if answer.upper() == "NONE":
                    answer = None
                break
    
    return (query_type, confidence, entities_list, answer, symbols_list, date_range)

