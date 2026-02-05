from fastapi import APIRouter, Query
from app.api.schemas import PromptRequest, QueryResponse
from app.core.orchestrator import orchestrate_query

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: PromptRequest):
    """
    POST endpoint for querying the financial assistant.
    
    Request body:
    {
        "prompt": "What's the AAPL price?"
    }
    """
    response = await orchestrate_query(request.prompt)
    return response

@router.get("/query", response_model=QueryResponse)
async def query_endpoint_get(prompt: str = Query(..., description="The financial query to process")):
    """
    GET endpoint for querying the financial assistant.
    
    Usage:
    GET /query?prompt=What's%20the%20AAPL%20price
    
    Example:
    http://localhost:8000/query?prompt=What's%20the%20AAPL%20price
    """
    response = await orchestrate_query(prompt)
    return response

