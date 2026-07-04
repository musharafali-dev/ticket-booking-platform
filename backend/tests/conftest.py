"""
Shared pytest fixtures.

We use SQLite in-memory for unit/integration tests rather than spinning up
a real Postgres — this keeps tests fast and dependency-free. The trade-off
is explicit: Postgres-specific behavior (native ENUM constraints, certain
JSON operators) isn't exercised here. That's acceptable for testing business
logic; anything relying on Postgres-specific semantics should be tested
separately against a real Postgres instance (flagged as a follow-up, not
covered by this test suite yet).
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
import app.models_registry  # noqa: F401


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()
