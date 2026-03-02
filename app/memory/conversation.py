from typing import List, Optional

from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage

from app.config import settings


def get_chat_history(session_id: str) -> RedisChatMessageHistory:
    """
    Return a Redis-backed chat history for the given session.

    The session_id should be stable per user/conversation so that
    history can be retrieved across multiple requests.
    """
    return RedisChatMessageHistory(
        url=settings.redis_url,
        session_id=session_id,
    )


def load_messages(session_id: str) -> List[BaseMessage]:
    """
    Load all messages for a given session from Redis.
    """
    history = get_chat_history(session_id)
    return history.messages


def append_message(
    session_id: str,
    message: BaseMessage,
) -> None:
    """
    Append a single message to the Redis-backed history.
    """
    history = get_chat_history(session_id)
    history.add_message(message)


def clear_history(session_id: str) -> None:
    """
    Delete all messages for a given session.
    """
    history = get_chat_history(session_id)
    history.clear()

