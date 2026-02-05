## **1. Project Objective**

The goal of this MVP is to develop **RichTV Bot**, an AI-powered financial assistant capable of:

- Receiving user queries in text form
- Fetching relevant financial data (prices, fundamentals, news) from internal APA resources
- Generating verified answers using an LLM
- Returning structured JSON responses for API or front-end consumption

The system is designed as a **microservice**, ensuring modularity and future scalability.

---

## **2. Technology Stack**

- **Backend:** FastAPI (Python) — high-performance async API endpoints
- **LLM:** OpenAI APIs
- **Data Storage:**
    - **Postgres:** Persistent storage for user queries, responses, confidence scores, and session context
    - **Redis:** Temporary caching for recent tickers, queries, and session data to reduce latency
- **Containerization:** Docker — ensures consistent development and deployment environment

---

## **3. Core Microservice Architecture**

### **3.1 High-Level Flow**

1. **Client → API Gateway**: Sends user query (string)
2. **Query Orchestrator**: Classifies query type (price, fundamentals, news)
3. **Data Fetchers** (async):
    - **PriceFetcher** → retrieves stock prices from APA data
    - **FundamentalsFetcher** → retrieves financial statements
    - **NewsFetcher** → retrieves internal financial news
4. **Context Builder**: Normalizes fetched data into structured JSON
5. **LLM Answer Generator**: Generates text answers based on structured context
6. **Response Validator**: Ensures data consistency and sets confidence score
7. **API Response → Client**: Returns structured JSON

---

### **3.2 Data Storage Strategy**

| Component | Data Stored | Purpose |
| --- | --- | --- |
| Postgres | User queries, generated answers, confidence, timestamps | Durable, auditable storage; context for follow-up queries |
| Redis | Recent tickers, temporary session context, cached query results | Fast retrieval; reduces API call frequency |

---

## **4. Design Principles**

- **Separation of Concerns:** Each component has a single responsibility
- **Reliability:** Persistent storage ensures auditable and traceable responses
- **Accuracy:** Validator enforces context-based correctness
- **Minimal MVP Focus:** No external citations yet; all answers rely on internal API data

---

## **5. Failure Modes & Mitigations**

| Issue | Mitigation |
| --- | --- |
| Missing data | LLM returns “Insufficient data” |
| Conflicting data | Show all available numbers, adjust confidence |
| API slow/unavailable | Async timeout + fallback to cache |
| LLM hallucinations | Validator ensures only context-backed numbers are returned |

---

## **6. Next Steps / Roadmap**

1. Implement FastAPI skeleton with `/query` endpoint
2. Build orchestrator for query classification
3. Develop first fetcher (PriceFetcher) and context builder
4. Integrate LLM answer generation and validator
5. End-to-end testing with multiple queries
6. Expand fetchers (News, Fundamentals) and implement Redis caching
7. Phase 2: integrate external APIs and citations