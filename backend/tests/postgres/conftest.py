"""
Postgres-backed test fixtures.

The default `db_session` fixture in conftest.py uses SQLite in-memory for
speed during everyday development. This module provides a real-Postgres
equivalent, used to close a real gap: several bugs in this codebase
(the enum auto-creation issue in the Alembic migration, the naive-vs-aware
datetime handling in auth/booking) were specifically SQLite-vs-Postgres
behavioral differences that unit tests against SQLite alone could not
have caught. Running the same test modules against both backends is
the actual verification that "works on my SQLite tests" means "works
in production," not just "works in this test double."

Requires a real Postgres instance reachable via TEST_DATABASE_URL (see
.env / docker-compose). Skipped automatically if unreachable, so the
main suite (`pytest tests/`) still runs fine on a machine without
Postgres — this file's tests are opt-in via `pytest tests/postgres/`.
"""
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
import app.models_registry  # noqa: F401

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ticket_booking_test",
)


@pytest_asyncio.fixture
async def pg_session():
    engine = create_async_engine(TEST_DATABASE_URL)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        pytest.skip(f"Postgres not reachable at {TEST_DATABASE_URL}: {e}")

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()
