# RichTV Bot - Financial Assistant MVP

An AI-powered financial assistant microservice that provides verified answers to stock/financial questions using internal APA data sources.

## Architecture

```
Query → Orchestrator → Data Fetchers → Context Builder → LLM → Validator → Response
```

### Components

- **Query Orchestrator**: Classifies queries and coordinates data fetching
- **Data Fetchers**: Retrieve price, fundamentals, and news data (APA integration)
- **Context Builder**: Normalizes fetched data into structured JSON
- **LLM Generator**: Generates answers using Gemini API
- **Response Validator**: Ensures all numbers match source data and assigns confidence scores

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **LLM**: Google Gemini
- **Storage**: PostgreSQL (persistent), Redis (caching)
- **Container**: Docker

## Setup

### 1. Environment Configuration

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Application

**Development mode:**
```bash
uvicorn app.main:app --reload
```

**Docker:**
```bash
docker-compose up --build
```

## API Endpoints

### Query Endpoint
```http
POST /query
Content-Type: application/json

{
  "prompt": "What is the price of NVDA?"
}
```

**Response:**
```json
{
  "answer": "NVDA stock is trading at $875.23, down 3.8% today.",
  "citations": [],
  "confidence": 0.95,
  "data_timestamp": "2025-12-21T12:00:00"
}
```

### Health Check
```http
GET /health
```

## Testing

```bash
pytest tests/ -v
```

## Project Structure

```
richtv-chatbot/
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── routes.py           # API endpoints
│   │   └── schemas.py          # Pydantic models
│   ├── core/
│   │   ├── orchestrator.py     # Query orchestration
│   │   └── validator.py        # Response validation
│   ├── data_fetchers/
│   │   ├── base_fetcher.py     # Abstract base class
│   │   ├── price_fetcher.py    # Price data
│   │   ├── fundamentals_fetcher.py
│   │   └── news_fetcher.py
│   ├── llm/
│   │   └── generator.py        # LLM integration
│   └── context/
│       └── builder.py          # Context normalization
├── tests/                      # Test suite
├── docs/                       # Documentation
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Development Status

### ✅ Completed
- FastAPI microservice architecture
- Query orchestrator
- LLM integration (Gemini)
- Response validator with confidence scoring
- Docker containerization
- Basic test suite

### 🚧 In Progress
- Real APA data integration (currently using placeholders)
- Redis caching
- PostgreSQL storage

### 📋 Planned
- External API citations
- Advanced query classification
- Rate limiting
- Logging and monitoring

## Documentation

See `docs/` folder for detailed documentation:
- `MVP.md` - Project objectives and architecture
- `reliablility_bluprint.md` - System design and failure modes
- `response_validator.md` - Validation logic details

## License

Proprietary - RichTV Bot

