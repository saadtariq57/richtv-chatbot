from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def _build_database_url() -> str:
    """
    Build the async PostgreSQL URL.

    Uses DATABASE_URL if provided; otherwise falls back to a sensible default
    that matches the docker-compose Postgres service.
    """
    if hasattr(settings, "database_url") and settings.database_url:
        return settings.database_url
    # Default for local docker-compose
    return "postgresql+asyncpg://richtv:richtv_password@postgres:5432/richtv_bot"


DATABASE_URL = _build_database_url()

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an AsyncSession.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """
    Initialize database schema (create tables) on startup.

    This is intentionally simple for the MVP. If the schema grows or
    requires versioned migrations, Alembic can be introduced later.
    """
    from app.models.conversation import Base as ModelsBase  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)

