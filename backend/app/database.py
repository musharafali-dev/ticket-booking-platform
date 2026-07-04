"""
Database engine and session factory.

We use async SQLAlchemy throughout since FastAPI is async-native — mixing
sync DB calls into async request handlers would block the event loop under
load, which defeats the point of using FastAPI in the first place.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,  # avoids using dead connections after DB restarts
    pool_size=10,
    max_overflow=5,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a DB session and guarantees cleanup.

    Rollback-on-exception is critical here: without it, a failed request
    can leave a broken transaction on the session, silently corrupting
    the next query on connection reuse.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
