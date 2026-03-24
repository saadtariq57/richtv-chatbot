"""Conversation service: get/create conversation, load recent messages, save turn."""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.budget import get_default_chat_history_token_budget
from app.llm.client import get_llm_client
from app.llm.prompt_builder import format_chat_message
from app.models.conversation import Conversation, Message


async def get_or_create_conversation(
    session: AsyncSession,
    user_id: str,
    conversation_id: Optional[uuid.UUID] = None,
) -> uuid.UUID:
    """
    Return conversation_id for this user. Create a new conversation if
    conversation_id is not provided or does not exist / belong to user.
    """
    if conversation_id:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalars().first()
        if conv is not None:
            return conv.id
    # Create new conversation
    conv = Conversation(user_id=user_id)
    session.add(conv)
    await session.commit()
    await session.refresh(conv)
    return conv.id


async def load_recent_messages(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    limit: int = 20,
) -> List[Dict[str, str]]:
    """
    Load the last `limit` messages for the conversation in chronological order.
    Returns list of {"role": "user"|"assistant", "content": "..."}.
    """
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()
    return [{"role": m.role, "content": m.content} for m in messages]


async def load_recent_messages_by_budget(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    token_budget: Optional[int] = None,
    max_messages: int = 50,
) -> List[Dict[str, str]]:
    """
    Load the newest messages that fit within a token budget.

    Messages are returned in chronological order, but selected from newest to
    oldest so recent context is preferred.
    """

    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(max_messages)
    )
    messages = list(result.scalars().all())
    if not messages:
        return []

    llm = get_llm_client()
    remaining_tokens = (
        token_budget
        if token_budget is not None
        else get_default_chat_history_token_budget()
    )

    selected_messages: List[Dict[str, str]] = []
    for message in messages:
        prompt_message = {"role": message.role, "content": message.content}
        rendered = format_chat_message(prompt_message)
        if not rendered:
            continue

        estimated_tokens = llm.estimate_tokens(rendered)
        if estimated_tokens > remaining_tokens and selected_messages:
            break
        if estimated_tokens > remaining_tokens:
            continue

        selected_messages.append(prompt_message)
        remaining_tokens -= estimated_tokens

    selected_messages.reverse()
    return selected_messages


async def save_turn(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    user_message: str,
    assistant_response: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Append user message and assistant message to the conversation."""
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_message,
    )
    session.add(user_msg)
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_response,
        message_metadata=metadata,
    )
    session.add(assistant_msg)
    await session.commit()
