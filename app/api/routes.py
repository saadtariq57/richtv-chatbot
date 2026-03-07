from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PromptRequest, QueryResponse
from app.db import get_session
from app.langgraph.graph import run_query

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: PromptRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    POST endpoint for querying the financial assistant.

    Request body:
    {
        "prompt": "What's the AAPL price?",
        "user_id": "optional-user-id",
        "conversation_id": "optional-uuid-to-resume"
    }
    When user_id is provided, conversation is stored and conversation_id is returned.
    """
    response = await run_query(
        request.prompt,
        session=session,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
    )
    return response


@router.get("/query", response_model=QueryResponse)
async def query_endpoint_get(
    prompt: str = Query(..., description="The financial query to process"),
    user_id: Optional[str] = Query(None, description="User id for conversation"),
    conversation_id: Optional[str] = Query(None, description="Conversation id to resume"),
    session: AsyncSession = Depends(get_session),
):
    """
    GET endpoint for querying the financial assistant.

    Example:
    GET /query?prompt=What's%20the%20AAPL%20price
    GET /query?prompt=And+NVDA?&user_id=u1&conversation_id=<uuid>
    """
    response = await run_query(
        prompt,
        session=session,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    return response

