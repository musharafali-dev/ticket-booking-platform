"""
Auth business logic, kept separate from the FastAPI route layer.

Rationale: routes should only handle HTTP concerns (status codes, request
parsing). Business rules (uniqueness checks, token lifecycle) belong here
so they're testable without spinning up a FastAPI app, and reusable if we
ever add a second entry point (e.g. an admin CLI or gRPC service).
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, EmailVerificationToken, RefreshToken
from app.auth.schemas import UserRegister
from app.common.enums import UserRole
from app.common.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token_value,
    hash_token,
    verify_token_hash,
    generate_verification_token,
)
from app.common.email import send_verification_email
from app.common.datetime_utils import is_expired
from app.config import settings


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        # Deliberately vague message — confirming "email already exists" to an
        # unauthenticated caller is a minor account-enumeration leak. We accept
        # the UX trade-off (user must try "forgot password" if they forget they
        # registered) in exchange for not leaking which emails are registered.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to register with the provided details. If you already have an account, try logging in.",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone_number=data.phone_number,
        role=UserRole.CUSTOMER,
        is_email_verified=False,
    )
    db.add(user)
    await db.flush()  # assigns user.id without committing

    await _issue_verification_token(db, user)

    await db.commit()
    await db.refresh(user)
    return user


async def _issue_verification_token(db: AsyncSession, user: User) -> None:
    token_value = generate_verification_token()
    token_row = EmailVerificationToken(
        user_id=user.id,
        token=token_value,
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
    )
    db.add(token_row)
    await db.flush()
    await send_verification_email(user.email, token_value)


async def verify_email(db: AsyncSession, token: str) -> User:
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    )
    token_row = result.scalar_one_or_none()

    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token"
        )
    if token_row.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used"
        )
    if is_expired(token_row.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired",
        )

    user_result = await db.execute(select(User).where(User.id == token_row.user_id))
    user = user_result.scalar_one()

    user.is_email_verified = True
    token_row.used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Same error for "no such user" and "wrong password" — distinguishing them
    # tells an attacker which emails are registered (account enumeration).
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
    )

    if not user or not verify_password(password, user.password_hash):
        raise invalid_credentials
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    return user


async def issue_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    refresh_value = create_refresh_token_value()

    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_value),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_row)
    await db.commit()

    return access_token, refresh_value


async def rotate_refresh_token(db: AsyncSession, refresh_value: str) -> tuple[str, str]:
    """
    Validate a refresh token and issue a new access+refresh pair.

    We revoke the old refresh token on use (rotation) rather than allowing
    indefinite reuse — this limits the damage window if a refresh token is
    ever stolen, since it becomes single-use.

    KNOWN LIMITATION (acceptable for MVP, not for scale): we can't index-lookup
    a bcrypt hash directly, so this scans all non-revoked tokens and verifies
    against each one — O(n) in active sessions. Fine at MVP scale (dozens to
    low hundreds of concurrent sessions). Before this becomes a bottleneck,
    switch to storing a fast lookup hash (e.g. SHA-256, not bcrypt) alongside
    an indexed column, and use bcrypt only for the password itself where the
    slowness is the point.
    """
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.revoked_at.is_(None))
    )
    candidates = result.scalars().all()

    matched: RefreshToken | None = None
    for candidate in candidates:
        if verify_token_hash(refresh_value, candidate.token_hash):
            matched = candidate
            break

    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    if not matched:
        raise invalid
    if is_expired(matched.expires_at):
        raise invalid

    user_result = await db.execute(select(User).where(User.id == matched.user_id))
    user = user_result.scalar_one()

    matched.revoked_at = datetime.now(timezone.utc)
    await db.flush()

    return await issue_tokens(db, user)
