"""
Booking business logic.

The core correctness property this module must guarantee: two concurrent
requests for the same seat can never both succeed. See lock_seats() for
the mechanism and why it's safe without SELECT FOR UPDATE or an external
lock service.
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.booking.models import Booking, BookingPassenger
from app.booking.schemas import BookingCreate
from app.booking.exceptions import (
    SeatsUnavailableError,
    BookingNotFoundError,
    InvalidBookingStateError,
)
from app.operators.models import Schedule, Seat
from app.common.enums import SeatStatus, BookingStatus, PaymentStatus, ScheduleStatus
from app.config import settings


def _generate_booking_code() -> str:
    # Format: BK-XXXXXXXX (8 random alphanumeric chars). Collisions are
    # astronomically unlikely at MVP volume; the DB unique constraint is
    # the actual safety net if one ever occurs (caller should retry on
    # IntegrityError, though we don't expect to ever see this in practice).
    return "BK-" + secrets.token_hex(4).upper()


async def lock_seats(db: AsyncSession, seat_ids: list[int], booking_id: int) -> None:
    """
    Atomically transition the given seats from AVAILABLE to LOCKED, tied to
    this booking. Raises SeatsUnavailableError if ANY seat could not be
    locked (already taken by someone else), and — critically — the caller's
    surrounding transaction must then roll back so no partial lock survives.

    Why this is safe under concurrency without SELECT FOR UPDATE:
    each UPDATE's WHERE clause includes `status = AVAILABLE`. Postgres
    evaluates and applies UPDATE atomically per row — if two transactions
    race for the same seat, the database itself serializes them: exactly
    one UPDATE matches the row (rowcount=1), the other matches zero rows
    (rowcount=0), never both. We don't hold a lock in application code;
    we let the storage engine's row-level write semantics do it for us.
    """
    unavailable: list[int] = []

    for seat_id in seat_ids:
        result = await db.execute(
            update(Seat)
            .where(Seat.id == seat_id, Seat.status == SeatStatus.AVAILABLE)
            .values(
                status=SeatStatus.LOCKED,
                locked_at=datetime.now(timezone.utc),
                locked_by_booking_id=booking_id,
            )
        )
        if result.rowcount == 0:
            unavailable.append(seat_id)

    if unavailable:
        raise SeatsUnavailableError(unavailable)


async def create_booking(
    db: AsyncSession, user_id: int, data: BookingCreate
) -> Booking:
    """
    IMPORTANT CALLER CONTRACT: if seat locking fails, this function rolls
    back the session (see below). SQLAlchemy expires ALL objects attached
    to the session on rollback — regardless of expire_on_commit — so any
    ORM object the caller obtained from this same session *before* calling
    create_booking() will raise MissingGreenlet on next attribute access
    after a conflict, because the expired attribute needs an async refetch
    that only works inside an active await context.

    Practical implications:
      - Route handlers should treat `db` as potentially "reset" after this
        call returns (or raises) and re-query rather than reuse pre-existing
        ORM object references.
      - This is exactly why get_booking_by_id() always re-queries by ID
        instead of returning a possibly-stale object reference.

    (Discovered via a failing test that held a Seat reference across a
    conflicting second booking call — see
    tests/unit/test_booking_service.py::test_create_booking_partial_conflict_rolls_back_entirely
    and its comments for the full reproduction.)
    """
    schedule_result = await db.execute(
        select(Schedule).where(Schedule.id == data.schedule_id)
    )
    schedule = schedule_result.scalar_one_or_none()

    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.status != ScheduleStatus.SCHEDULED:
        raise HTTPException(
            status_code=400, detail="This schedule is no longer available for booking"
        )

    seat_ids = [p.seat_id for p in data.passengers]

    # Fetch seats to validate they belong to this schedule and to compute price.
    seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids)))
    seats_by_id = {s.id: s for s in seats_result.scalars().all()}

    missing = set(seat_ids) - set(seats_by_id.keys())
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Seats not found: {sorted(missing)}"
        )

    wrong_schedule = [
        sid for sid, s in seats_by_id.items() if s.schedule_id != data.schedule_id
    ]
    if wrong_schedule:
        raise HTTPException(
            status_code=400,
            detail=f"Seats do not belong to the specified schedule: {sorted(wrong_schedule)}",
        )

    total_amount = sum(seats_by_id[sid].price for sid in seat_ids)
    booking_code = _generate_booking_code()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.BOOKING_EXPIRATION_MINUTES
    )

    booking = Booking(
        booking_code=booking_code,
        user_id=user_id,
        schedule_id=data.schedule_id,
        number_of_passengers=len(data.passengers),
        total_amount=total_amount,
        status=BookingStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        expires_at=expires_at,
    )
    db.add(booking)
    await db.flush()  # assigns booking.id, needed to tag locked seats

    try:
        await lock_seats(db, seat_ids, booking.id)
    except SeatsUnavailableError as e:
        # Rolling back here undoes the Booking insert AND any seats that
        # *did* lock before the failing one — this is the transactional
        # guarantee that makes "all or nothing" true without manual cleanup.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The following seats were just taken by another booking: {e.unavailable_seat_ids}. "
            f"Please choose different seats.",
        )

    for p in data.passengers:
        seat = seats_by_id[p.seat_id]
        db.add(
            BookingPassenger(
                booking_id=booking.id,
                seat_id=p.seat_id,
                first_name=p.first_name,
                last_name=p.last_name,
                date_of_birth=p.date_of_birth,
                id_type=p.id_type,
                id_number=p.id_number,
                seat_number=seat.seat_number,
            )
        )

    # Maintain the denormalized counter used by search for fast availability
    # filtering (see app.search.service) — kept in sync here rather than
    # computed live from Seat rows on every search query.
    schedule.available_seats -= len(seat_ids)

    await db.commit()

    return await get_booking_by_id(db, booking.id, user_id=user_id)


async def get_booking_by_id(
    db: AsyncSession, booking_id: int, user_id: int | None = None
) -> Booking:
    stmt = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.passengers))
    )
    if user_id is not None:
        stmt = stmt.where(Booking.user_id == user_id)

    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    if booking is None:
        raise BookingNotFoundError(f"Booking {booking_id} not found")
    return booking


async def list_user_bookings(db: AsyncSession, user_id: int) -> list[Booking]:
    stmt = (
        select(Booking)
        .where(Booking.user_id == user_id)
        .options(selectinload(Booking.passengers))
        .order_by(Booking.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def cancel_booking(
    db: AsyncSession, booking_id: int, user_id: int, reason: str | None
) -> Booking:
    booking = await get_booking_by_id(db, booking_id, user_id=user_id)

    if booking.status in (BookingStatus.CANCELLED, BookingStatus.EXPIRED):
        raise InvalidBookingStateError("Booking is already cancelled or expired")

    seat_ids_result = await db.execute(
        select(BookingPassenger.seat_id).where(
            BookingPassenger.booking_id == booking.id
        )
    )
    seat_ids = list(seat_ids_result.scalars().all())

    # Release seats back to AVAILABLE regardless of whether they were
    # LOCKED (unpaid) or BOOKED (paid) — cancellation always frees inventory.
    await db.execute(
        update(Seat)
        .where(Seat.id.in_(seat_ids))
        .values(status=SeatStatus.AVAILABLE, locked_at=None, locked_by_booking_id=None)
    )

    schedule_result = await db.execute(
        select(Schedule).where(Schedule.id == booking.schedule_id)
    )
    schedule = schedule_result.scalar_one()
    schedule.available_seats += len(seat_ids)

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    booking.cancellation_reason = reason

    await db.commit()
    await db.refresh(booking)
    return booking


async def expire_stale_bookings(db: AsyncSession) -> int:
    """
    Release seats and mark bookings EXPIRED for any PENDING booking whose
    payment window has elapsed. Intended to be called periodically (e.g. a
    scheduled task or triggered opportunistically on booking reads) rather
    than relying on a dedicated worker process, which is out of scope for
    the MVP (flagged as a follow-up: a proper background scheduler such as
    APScheduler or a cron-triggered endpoint, rather than best-effort calls
    from request handlers).
    """
    now = datetime.now(timezone.utc)
    stmt = select(Booking).where(
        Booking.status == BookingStatus.PENDING,
        Booking.expires_at < now,
    )
    result = await db.execute(stmt)
    stale_bookings = list(result.scalars().all())

    for booking in stale_bookings:
        seat_ids_result = await db.execute(
            select(BookingPassenger.seat_id).where(
                BookingPassenger.booking_id == booking.id
            )
        )
        seat_ids = list(seat_ids_result.scalars().all())

        await db.execute(
            update(Seat)
            .where(Seat.id.in_(seat_ids))
            .values(
                status=SeatStatus.AVAILABLE, locked_at=None, locked_by_booking_id=None
            )
        )

        schedule_result = await db.execute(
            select(Schedule).where(Schedule.id == booking.schedule_id)
        )
        schedule = schedule_result.scalar_one()
        schedule.available_seats += len(seat_ids)

        booking.status = BookingStatus.EXPIRED

    await db.commit()
    return len(stale_bookings)
