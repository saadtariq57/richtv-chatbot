# LangChain/LangGraph Migration Plan

**Project:** RichTV Chatbot  
**Duration:** 2-3 weeks  
**Status:** 🟡 Not Started

---

## Why Migrate

- RAG for news/documents
- Conversation history
- Scalability for complex workflows
- Migrate now while codebase is small

---

## Week 1: Core Migration

- [ ] Install LangChain, LangGraph, LangSmith
- [ ] Create `app/langgraph/` (state, nodes, graph, tools)
- [ ] Convert data fetchers → LangChain tools
- [ ] Build graph nodes (classification, entity resolution, data fetch, answer)
- [ ] Add conversation memory

---

## Week 2: RAG

- [ ] Set up vector store (Pinecone/Chroma)
- [ ] Document ingestion pipeline
- [ ] Retrieval chain
- [ ] Integrate RAG into graph

---

## Week 3: Polish

- [ ] LangSmith observability
- [ ] Error handling & testing
- [ ] Archive old orchestrator, update API routes
- [ ] Deploy

---

## Keep vs Replace

**Keep:** `data_fetchers/`, `ticker_resolver.py`, `validator.py`, `schemas.py`  
**Replace:** `orchestrator.py`, `generator.py`, `classifier/` → LangGraph

---

## Progress

| Week | Status |
|------|--------|
| 1 | 0% |
| 2 | 0% |
| 3 | 0% |

**Current:** Not Started

---

## Decisions to Make

- [ ] Vector store? (Pinecone vs Chroma)
- [ ] Memory backend? (PostgreSQL vs Redis)
- [ ] LLM provider? (OpenAI vs other)
