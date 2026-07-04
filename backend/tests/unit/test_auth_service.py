"""
Tests for app.auth.service.

Covers the behaviors that matter most for a booking platform's auth:
duplicate registration, verification token lifecycle, credential checks,
and refresh token rotation/single-use.
"""

import pytest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.auth import service
from app.auth.models import User, EmailVerificationToken
from app.auth.schemas import UserRegister
from app.common.enums import UserRole


def valid_registration(**overrides) -> UserRegister:
    defaults = dict(
        email="test@example.com",
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )
    defaults.update(overrides)
    return UserRegister(**defaults)


@pytest.mark.asyncio
async def test_register_user_creates_unverified_user(db_session):
    user = await service.register_user(db_session, valid_registration())

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_email_verified is False
    assert user.role == UserRole.CUSTOMER
    # Password must never be stored in plaintext.
    assert user.password_hash != "StrongPass123!"


@pytest.mark.asyncio
async def test_register_user_issues_verification_token(db_session):
    user = await service.register_user(db_session, valid_registration())

    result = await db_session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    )
    token_row = result.scalar_one()
    assert token_row.used_at is None
    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(db_session):
    await service.register_user(db_session, valid_registration())

    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(db_session, valid_registration())

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_with_valid_token(db_session):
    user = await service.register_user(db_session, valid_registration())
    result = await db_session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    )
    token_row = result.scalar_one()

    verified_user = await service.verify_email(db_session, token_row.token)

    assert verified_user.is_email_verified is True


@pytest.mark.asyncio
async def test_verify_email_with_invalid_token_raises(db_session):
    with pytest.raises(HTTPException) as exc_info:
        await service.verify_email(db_session, "nonexistent-token")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_token_cannot_be_reused(db_session):
    user = await service.register_user(db_session, valid_registration())
    result = await db_session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    )
    token_row = result.scalar_one()

    await service.verify_email(db_session, token_row.token)

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_email(db_session, token_row.token)
    assert exc_info.value.status_code == 400
    assert "already used" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_verify_email_expired_token_rejected(db_session):
    user = await service.register_user(db_session, valid_registration())
    result = await db_session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    )
    token_row = result.scalar_one()

    # Simulate an expired token.
    token_row.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_email(db_session, token_row.token)
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session):
    await service.register_user(db_session, valid_registration())

    user = await service.authenticate_user(
        db_session, "test@example.com", "StrongPass123!"
    )
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password_rejected(db_session):
    await service.register_user(db_session, valid_registration())

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user(
            db_session, "test@example.com", "WrongPassword123!"
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_nonexistent_user_same_error_as_wrong_password(db_session):
    """
    Regression guard for account enumeration: both cases must return the
    identical status code and message, so a caller can't distinguish
    "no such user" from "wrong password" by inspecting the response.
    """
    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user(db_session, "ghost@example.com", "whatever123!")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect email or password"


@pytest.mark.asyncio
async def test_issue_tokens_returns_access_and_refresh(db_session):
    user = await service.register_user(db_session, valid_registration())
    access_token, refresh_token = await service.issue_tokens(db_session, user)

    assert access_token
    assert refresh_token
    assert access_token != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_rotation_issues_new_pair(db_session):
    user = await service.register_user(db_session, valid_registration())
    _, refresh_token = await service.issue_tokens(db_session, user)

    new_access, new_refresh = await service.rotate_refresh_token(
        db_session, refresh_token
    )

    assert new_access
    assert new_refresh
    assert new_refresh != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_is_single_use(db_session):
    """
    Critical security property: once rotated, the old refresh token must
    not work again. Without this, a stolen-but-unused-yet token could be
    replayed indefinitely alongside the legitimate user's new one.
    """
    user = await service.register_user(db_session, valid_registration())
    _, refresh_token = await service.issue_tokens(db_session, user)

    await service.rotate_refresh_token(db_session, refresh_token)

    with pytest.raises(HTTPException) as exc_info:
        await service.rotate_refresh_token(db_session, refresh_token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_garbage_token_rejected(db_session):
    with pytest.raises(HTTPException) as exc_info:
        await service.rotate_refresh_token(db_session, "not-a-real-token")
    assert exc_info.value.status_code == 401
