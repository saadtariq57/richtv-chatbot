from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ConversationSummary,
    MessageDTO,
    PromptRequest,
    QueryResponse,
)
from app.db import get_session
from app.langgraph.graph import run_query
from app.models.conversation import Conversation, Message

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


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    user_id: str = Query(..., description="User id whose conversations to list"),
    session: AsyncSession = Depends(get_session),
):
    """
    Return all conversations for a user, newest first.
    """
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.updated_at))
    )
    result = await session.execute(stmt)
    conversations = result.scalars().all()
    return [
        ConversationSummary(
            id=str(c.id),
            user_id=c.user_id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in conversations
    ]


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageDTO],
)
async def list_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """
    Return messages for a conversation, oldest first.
    """
    # Verify conversation exists (minimal 404 protection)
    conv_stmt = select(Conversation.id).where(Conversation.id == conversation_id)
    conv_result = await session.execute(conv_stmt)
    if conv_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(asc(Message.created_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()
    return [
        MessageDTO(
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]

