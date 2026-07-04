"""Booking and passenger ORM models."""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    Date,
    Text,
    Enum as SAEnum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.common.enums import BookingStatus, PaymentStatus

if TYPE_CHECKING:
    # Same cycle guard as auth/models.py — see that file's comment for the
    # full explanation of why this is safe at runtime despite the apparent cycle.
    from app.auth.models import User
    from app.operators.models import Schedule
    from app.payment.models import Payment


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedules.id", ondelete="RESTRICT"), index=True
    )

    number_of_passengers: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        index=True,
    )

    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    schedule: Mapped["Schedule"] = relationship()
    passengers: Mapped[List["BookingPassenger"]] = relationship(
        back_populates="booking", cascade="all, delete-orphan"
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        back_populates="booking", uselist=False
    )


class BookingPassenger(Base):
    __tablename__ = "booking_passengers"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="RESTRICT"))

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    id_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # CNIC, PASSPORT
    id_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="passengers")

    __table_args__ = (
        UniqueConstraint("booking_id", "seat_id", name="uq_booking_seat"),
    )
