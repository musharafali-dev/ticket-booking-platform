"""
Tests for app.booking.service.

The most important test here is test_concurrent_booking_same_seat_only_one_wins —
it exercises the exact race condition this module exists to prevent. Everything
else is supporting coverage for the booking lifecycle.
"""

import asyncio
import secrets
from datetime import date, time, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
import app.models_registry  # noqa: F401
from app.auth.models import User
from app.operators.models import Operator, Vehicle, Route, Schedule, Seat
from app.booking.models import Booking, BookingPassenger
from app.booking.schemas import BookingCreate, PassengerInput
from app.booking.exceptions import (
    SeatsUnavailableError,
    BookingNotFoundError,
    InvalidBookingStateError,
)
from app.common.enums import (
    UserRole,
    TransportType,
    ScheduleStatus,
    SeatCategory,
    SeatStatus,
    BookingStatus,
)
from app.booking import service


async def _seed_bookable_schedule(db, num_seats=5, price=2000.0, suffix=None):
    suffix = suffix or secrets.token_hex(4)
    customer = User(
        email=f"rider_{suffix}@test.com",
        password_hash="x",
        first_name="R",
        last_name="Rider",
        role=UserRole.CUSTOMER,
    )
    db.add(customer)
    op_user = User(
        email=f"op_{suffix}@test.com",
        password_hash="x",
        first_name="O",
        last_name="Op",
        role=UserRole.OPERATOR,
    )
    db.add(op_user)
    await db.flush()

    operator = Operator(
        user_id=op_user.id,
        operator_name="Test Bus Co",
        operator_type=TransportType.BUS,
        is_verified=True,
    )
    db.add(operator)
    await db.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        vehicle_type=TransportType.BUS,
        registration_number=f"BUS-{suffix}",
        total_seats=num_seats,
        seat_configuration={"ECONOMY": num_seats},
    )
    db.add(vehicle)
    await db.flush()

    route = Route(
        operator_id=operator.id,
        route_code=f"RT-{suffix}",
        departure_city="Karachi",
        arrival_city="Lahore",
    )
    db.add(route)
    await db.flush()

    schedule = Schedule(
        operator_id=operator.id,
        route_id=route.id,
        vehicle_id=vehicle.id,
        departure_date=date.today() + timedelta(days=1),
        departure_time=time(8, 0),
        arrival_time=time(14, 0),
        base_fare=price,
        total_seats=num_seats,
        available_seats=num_seats,
        status=ScheduleStatus.SCHEDULED,
    )
    db.add(schedule)
    await db.flush()

    seats = []
    for i in range(num_seats):
        seat = Seat(
            schedule_id=schedule.id,
            seat_number=f"{i+1}A",
            seat_category=SeatCategory.ECONOMY,
            status=SeatStatus.AVAILABLE,
            price=price,
        )
        db.add(seat)
        seats.append(seat)

    await db.commit()
    for s in seats:
        await db.refresh(s)
    await db.refresh(customer)
    await db.refresh(schedule)

    return customer, schedule, seats


def _booking_payload(schedule_id, seat_ids, email="passenger@test.com"):
    return BookingCreate(
        schedule_id=schedule_id,
        passengers=[
            PassengerInput(seat_id=sid, first_name="John", last_name="Doe")
            for sid in seat_ids
        ],
        contact_email=email,
    )


@pytest.mark.asyncio
async def test_create_booking_locks_seats_and_computes_total(db_session):
    customer, schedule, seats = await _seed_bookable_schedule(
        db_session, num_seats=5, price=2000.0
    )
    payload = _booking_payload(schedule.id, [seats[0].id, seats[1].id])

    booking = await service.create_booking(db_session, customer.id, payload)

    assert booking.total_amount == 4000.0
    assert booking.number_of_passengers == 2
    assert booking.status == BookingStatus.PENDING
    assert len(booking.passengers) == 2

    for seat_id in [seats[0].id, seats[1].id]:
        result = await db_session.execute(select(Seat).where(Seat.id == seat_id))
        seat = result.scalar_one()
        assert seat.status == SeatStatus.LOCKED
        assert seat.locked_by_booking_id == booking.id


@pytest.mark.asyncio
async def test_create_booking_decrements_available_seats_counter(db_session):
    customer, schedule, seats = await _seed_bookable_schedule(db_session, num_seats=5)
    payload = _booking_payload(schedule.id, [seats[0].id, seats[1].id, seats[2].id])

    await service.create_booking(db_session, customer.id, payload)

    result = await db_session.execute(
        select(Schedule).where(Schedule.id == schedule.id)
    )
    refreshed = result.scalar_one()
    assert refreshed.available_seats == 2


@pytest.mark.asyncio
async def test_create_booking_rejects_already_locked_seat(db_session):
    customer, schedule, seats = await _seed_bookable_schedule(db_session, num_seats=5)
    await service.create_booking(
        db_session, customer.id, _booking_payload(schedule.id, [seats[0].id])
    )

    with pytest.raises(Exception) as exc_info:
        await service.create_booking(
            db_session, customer.id, _booking_payload(schedule.id, [seats[0].id])
        )

    # HTTPException with 409, raised after the seat lock attempt failed
    assert getattr(exc_info.value, "status_code", None) == 409


@pytest.mark.asyncio
async def test_create_booking_partial_conflict_rolls_back_entirely(db_session):
    """
    Books seats [0] successfully first. Then attempts to book [0, 1] together
    (seat 0 is taken, seat 1 is free). The whole second booking must fail,
    and seat 1 must NOT be left LOCKED with no valid booking — this is the
    "all or nothing" guarantee the transaction boundary provides.

    Note: we capture seat IDs (plain ints) before the conflicting call and
    re-query fresh ORM objects afterward, rather than reusing the original
    `seats` list objects. This isn't just test hygiene — it reflects a real
    constraint documented on create_booking(): a rollback inside that call
    expires every object attached to the session, so any pre-existing ORM
    reference becomes unsafe to touch afterward. This was discovered because
    the naive version of this test (reusing `seats[1]` directly) failed with
    MissingGreenlet, which is what led to documenting the caller contract.
    """
    customer, schedule, seats = await _seed_bookable_schedule(db_session, num_seats=5)
    seat0_id, seat1_id = seats[0].id, seats[1].id

    await service.create_booking(
        db_session, customer.id, _booking_payload(schedule.id, [seat0_id])
    )

    with pytest.raises(Exception) as exc_info:
        await service.create_booking(
            db_session, customer.id, _booking_payload(schedule.id, [seat0_id, seat1_id])
        )
    assert getattr(exc_info.value, "status_code", None) == 409

    # Re-query fresh — do not reuse `seats[1]` from before the conflicting call.
    result = await db_session.execute(select(Seat).where(Seat.id == seat1_id))
    seat1 = result.scalar_one()
    assert seat1.status == SeatStatus.AVAILABLE
    assert seat1.locked_by_booking_id is None


@pytest.mark.asyncio
async def test_create_booking_duplicate_seat_ids_rejected_at_schema_level():
    with pytest.raises(ValueError):
        BookingCreate(
            schedule_id=1,
            passengers=[
                PassengerInput(seat_id=1, first_name="A", last_name="B"),
                PassengerInput(seat_id=1, first_name="C", last_name="D"),
            ],
            contact_email="test@example.com",
        )


@pytest.mark.asyncio
async def test_create_booking_seat_from_wrong_schedule_rejected(db_session):
    customer, schedule, seats = await _seed_bookable_schedule(
        db_session, num_seats=2, suffix="a"
    )
    # Create a second, unrelated schedule with its own seat — must use a
    # distinct suffix so the fixture's users/vehicle/route don't collide
    # with the first call's unique constraints.
    _, other_schedule, other_seats = await _seed_bookable_schedule(
        db_session, num_seats=1, suffix="b"
    )

    payload = _booking_payload(schedule.id, [other_seats[0].id])

    with pytest.raises(Exception) as exc_info:
        await service.create_booking(db_session, customer.id, payload)
    assert getattr(exc_info.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_cancel_booking_releases_seats(db_session):
    customer, schedule, seats = await _seed_bookable_schedule(db_session, num_seats=5)
    booking = await service.create_booking(
        db_session, customer.id, _booking_payload(schedule.id, [seats[0].id])
    )

    cancelled = await service.cancel_booking(
        db_session, booking.id, customer.id, reason="Changed plans"
    )

    assert cancelled.status == BookingStatus.CANCELLED

    result = await db_session.execute(select(Seat).where(Seat.id == seats[0].id))
    seat = result.scalar_one()
    assert seat.status == SeatStatus.AVAILABLE
    assert seat.locked_by_booking_id is None

    result = await db_session.execute(
        select(Schedule).where(Schedule.id == schedule.id)
    )
    refreshed_schedule = result.scalar_one()
    assert refreshed_schedule.available_seats == 5  # back to full


@pytest.mark.asyncio
async def test_cancel_already_cancelled_booking_rejected(db_session):
    customer, schedule, seats = await _seed_bookable_schedule(db_session, num_seats=5)
    booking = await service.create_booking(
        db_session, customer.id, _booking_payload(schedule.id, [seats[0].id])
    )
    await service.cancel_booking(db_session, booking.id, customer.id, None)

    with pytest.raises(InvalidBookingStateError):
        await service.cancel_booking(db_session, booking.id, customer.id, None)


@pytest.mark.asyncio
async def test_get_booking_scoped_to_owning_user(db_session):
    customer, schedule, seats = await _seed_bookable_schedule(db_session, num_seats=5)
    booking = await service.create_booking(
        db_session, customer.id, _booking_payload(schedule.id, [seats[0].id])
    )

    other_user = User(
        email="other@test.com",
        password_hash="x",
        first_name="O",
        last_name="U",
        role=UserRole.CUSTOMER,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    with pytest.raises(BookingNotFoundError):
        await service.get_booking_by_id(db_session, booking.id, user_id=other_user.id)


@pytest.mark.asyncio
async def test_expire_stale_bookings_releases_seats(db_session):
    from datetime import datetime, timezone

    customer, schedule, seats = await _seed_bookable_schedule(db_session, num_seats=5)
    booking = await service.create_booking(
        db_session, customer.id, _booking_payload(schedule.id, [seats[0].id])
    )

    # Force expiry into the past.
    result = await db_session.execute(select(Booking).where(Booking.id == booking.id))
    b = result.scalar_one()
    b.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    expired_count = await service.expire_stale_bookings(db_session)

    assert expired_count == 1
    result = await db_session.execute(select(Seat).where(Seat.id == seats[0].id))
    seat = result.scalar_one()
    assert seat.status == SeatStatus.AVAILABLE


@pytest.mark.asyncio
async def test_concurrent_booking_same_seat_only_one_wins():
    """
    THE critical regression test for this module.

    Simulates two users racing to book the same single seat using separate
    DB sessions against a shared SQLite file (in-memory DBs can't be shared
    across connections, so we use a temp file to get genuine concurrent
    connections, matching how two separate web requests would each get
    their own session against the same Postgres database in production).

    Expected outcome: exactly one booking succeeds, exactly one fails with
    a 409, and the seat ends up LOCKED by the winning booking only.
    """
    import tempfile
    import os

    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "concurrency_test.db")
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(db_url)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed using one session, then close it fully before concurrent access.
    async with session_factory() as setup_session:
        customer, schedule, seats = await _seed_bookable_schedule(
            setup_session, num_seats=1
        )
        customer_id = customer.id
        schedule_id = schedule.id
        seat_id = seats[0].id

    async def attempt_booking():
        async with session_factory() as session:
            try:
                payload = _booking_payload(schedule_id, [seat_id])
                booking = await service.create_booking(session, customer_id, payload)
                return ("success", booking.id)
            except Exception as e:
                return ("failure", getattr(e, "status_code", str(e)))

    results = await asyncio.gather(
        attempt_booking(), attempt_booking(), return_exceptions=False
    )

    outcomes = [r[0] for r in results]
    assert outcomes.count("success") == 1, f"Expected exactly 1 success, got: {results}"
    assert outcomes.count("failure") == 1, f"Expected exactly 1 failure, got: {results}"

    failure_result = next(r for r in results if r[0] == "failure")
    assert failure_result[1] == 409, f"Expected 409 conflict, got {failure_result[1]}"

    # Verify final DB state: seat locked by exactly the winning booking.
    async with session_factory() as verify_session:
        result = await verify_session.execute(select(Seat).where(Seat.id == seat_id))
        final_seat = result.scalar_one()
        assert final_seat.status == SeatStatus.LOCKED

        winning_booking_id = next(r[1] for r in results if r[0] == "success")
        assert final_seat.locked_by_booking_id == winning_booking_id

    await engine.dispose()
