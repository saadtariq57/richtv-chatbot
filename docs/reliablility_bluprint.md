

# **1. Directory Structure + Code Skeleton**

This is **FastAPI microservice**, modularized, production-ready MVP style.

```
perplexity-finance/
├── app/
│   ├── main.py               # FastAPI entrypoint
│   ├── api/
│   │   ├── routes.py         # /query endpoint
│   │   └── schemas.py        # request & response schemas (Pydantic)
│   ├── core/
│   │   ├── orchestrator.py   # Query orchestrator
│   │   └── validator.py      # Response validator
│   ├── data_fetchers/
│   │   ├── price_fetcher.py
│   │   ├── fundamentals_fetcher.py
│   │   └── news_fetcher.py
│   ├── llm/
│   │   └── generator.py      # LLM answer generator
│   └── context/
│       └── builder.py        # Context builder
├── tests/                    # Unit & integration tests
├── requirements.txt
└── Dockerfile

```

---

### **main.py**

```python
from fastapi import FastAPI
from app.api import routes

app = FastAPI(title="Perplexity Finance MVP")

app.include_router(routes.router)

```

### **schemas.py**

```python
from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str

class Citation(BaseModel):
    source: str
    url: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float
    data_timestamp: str

```

### **routes.py**

```python
from fastapi import APIRouter
from app.api.schemas import QueryRequest, QueryResponse
from app.core.orchestrator import orchestrate_query

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    response = await orchestrate_query(request.query)
    return response

```

---

# **2. LLM Prompt Contracts**

You **must separate prompt types and context injection**, or you’ll get hallucinations.

### **Prompt pattern**

```
User Query: {user_query}
Context:
{structured_context_json}

Instructions:
- Base all numbers and statements only on the context.
- Include citations where applicable.
- If context lacks information, respond: "Insufficient data."

```

- Keep prompts < 4k tokens for cost and latency.
- Each query has **LLM input + structured JSON**.
- LLM output = `{answer, citations}` only.

---

# **3. Failure Modes & Edge Cases**

| Issue | Mitigation |
| --- | --- |
| **No data found** | Abort query, return `"Insufficient data"` |
| **Multiple sources conflict** | Show all, mark confidence < 0.5 |
| **LLM hallucination** | Validator checks: all numbers must match context |
| **Rate limit from external API** | Retry with exponential backoff, fallback to cached data |
| **Slow API** | Timeout 2–3s per fetcher, async calls |
| **Malformed user query** | LLM classifies type; if unrecognizable → ask for clarification |

**Edge-case rules:**

- Never generate prices.
- Always attach citations.
- Always return structured JSON.

---

# **4. Benchmarking & Comparison Plan**

**Goal:** See if your MVP is even useful vs Bloomberg / TradingView.

- Metrics:
    - Accuracy vs official data (prices, fundamentals)
    - Response latency (target < 2s for cached queries, <5s for live fetch)
    - Hallucination rate (<1% for numeric claims)
    - Citation coverage (all numeric/factual claims cited)

**Testing Approach:**

1. Take 50 random queries from finance news
2. Run MVP → record LLM output
3. Compare against official filings, Yahoo Finance, Reuters
4. Log:
    - Correct answer %
    - Citation accuracy %
    - Time per query

**Benchmark Notes:**

- Don’t try to “beat Bloomberg” on day 1 — just prove **MVP correctness** and **reliability**.
- Bloomberg/Refinitiv have **sub-second latency + real-time streams**. Your goal is **data accuracy + AI synthesis**, not microseconds.

---

# ✅ Summary

- FastAPI + microservice
- Modularized: orchestrator → fetchers → context → LLM → validator
- Strict prompt + schema contract → no hallucinations
- Failure modes mapped
- Benchmarking plan ready

---

![image.png](attachment:b823130a-4947-4a2c-808b-5fae518d06c7:image.png)