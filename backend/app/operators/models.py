"""Operator, fleet, route, and schedule ORM models."""

from datetime import datetime, date, time
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    Time,
    Enum as SAEnum,
    ForeignKey,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.common.enums import TransportType, ScheduleStatus, SeatCategory, SeatStatus

if TYPE_CHECKING:
    from app.auth.models import User


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )

    operator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    operator_type: Mapped[TransportType] = mapped_column(
        SAEnum(TransportType, name="transport_type"), index=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="operator_profile")
    vehicles: Mapped[List["Vehicle"]] = relationship(
        back_populates="operator", cascade="all, delete-orphan"
    )
    routes: Mapped[List["Route"]] = relationship(
        back_populates="operator", cascade="all, delete-orphan"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    operator_id: Mapped[int] = mapped_column(
        ForeignKey("operators.id", ondelete="CASCADE"), index=True
    )

    vehicle_type: Mapped[TransportType] = mapped_column(
        SAEnum(TransportType, name="vehicle_type")
    )
    registration_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    # e.g. {"ECONOMY": 100, "BUSINESS": 20}
    seat_configuration: Mapped[dict] = mapped_column(JSON, default=dict)
    amenities: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    operator: Mapped["Operator"] = relationship(back_populates="vehicles")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="vehicle")


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    operator_id: Mapped[int] = mapped_column(
        ForeignKey("operators.id", ondelete="CASCADE"), index=True
    )

    route_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    departure_city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    arrival_city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    operator: Mapped["Operator"] = relationship(back_populates="routes")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="route")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    operator_id: Mapped[int] = mapped_column(
        ForeignKey("operators.id", ondelete="CASCADE"), index=True
    )
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"), index=True
    )
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"), index=True
    )

    departure_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_time: Mapped[time] = mapped_column(Time, nullable=False)

    base_fare: Mapped[float] = mapped_column(Float, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[ScheduleStatus] = mapped_column(
        SAEnum(ScheduleStatus, name="schedule_status"),
        default=ScheduleStatus.SCHEDULED,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    operator: Mapped["Operator"] = relationship()
    route: Mapped["Route"] = relationship(back_populates="schedules")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="schedules")
    seats: Mapped[List["Seat"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "vehicle_id",
            "departure_date",
            "departure_time",
            name="uq_vehicle_departure",
        ),
    )


class Seat(Base):
    """
    Individual seat inventory per schedule.

    We materialize one row per seat per schedule (rather than just tracking
    a counter on Schedule) because we need to know *which* seat a passenger
    holds, support seat-map UI, and use row-level locking (SELECT FOR UPDATE)
    to prevent two users double-booking the same seat under concurrent load.
    """

    __tablename__ = "seats"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"), index=True
    )

    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)
    seat_category: Mapped[SeatCategory] = mapped_column(
        SAEnum(SeatCategory, name="seat_category")
    )
    status: Mapped[SeatStatus] = mapped_column(
        SAEnum(SeatStatus, name="seat_status"), default=SeatStatus.AVAILABLE, index=True
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)

    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locked_by_booking_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )

    schedule: Mapped["Schedule"] = relationship(back_populates="seats")

    __table_args__ = (
        UniqueConstraint("schedule_id", "seat_number", name="uq_schedule_seat"),
    )
