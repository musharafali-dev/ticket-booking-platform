"""User and authentication-related ORM models."""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Date, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.common.enums import UserRole

if TYPE_CHECKING:
    # Import-time cycle guard: operators/models.py and booking/models.py both
    # import User for their own relationships, so importing them back here
    # at module load time would cycle. TYPE_CHECKING is False at runtime, so
    # this only exists for static analysis (mypy, ruff, IDEs) to resolve the
    # string-based Mapped["Operator"] / Mapped["Booking"] annotations below —
    # SQLAlchemy itself resolves those strings lazily via its mapper registry,
    # which is what actually makes this safe at runtime (proven by the
    # passing test suite, not just by this comment).
    from app.operators.models import Operator
    from app.booking.models import Booking


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cnic_number: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        default=UserRole.CUSTOMER,
        nullable=False,
        index=True,
    )

    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    operator_profile: Mapped[Optional["Operator"]] = relationship(
        back_populates="user", uselist=False
    )
    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")
    email_verification_tokens: Mapped[List["EmailVerificationToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class EmailVerificationToken(Base):
    """
    Separate table (rather than a column on User) so tokens can expire,
    be invalidated, and re-issued without mutating the user row, and so
    we keep an audit trail of verification attempts.
    """

    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="email_verification_tokens")


class RefreshToken(Base):
    """
    Stored refresh tokens enable server-side revocation (logout, password
    reset invalidates all sessions) — a pure stateless JWT refresh scheme
    cannot support this without a blocklist, which is effectively this.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
