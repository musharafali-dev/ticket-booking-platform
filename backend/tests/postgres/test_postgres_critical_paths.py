"""
Critical-path tests run against REAL Postgres, not SQLite.

This file deliberately does not re-test everything the SQLite suite
already covers -- that would be redundant effort for this timeline. It
targets specifically the behaviors most likely to differ between
backends, based on concrete bugs already found in this project:

1. Native ENUM constraint enforcement (SQLite has no real ENUM type)
2. Timezone-aware datetime round-tripping (SQLite silently drops tzinfo;
   already caused one real bug in auth token expiry)
3. The seat-locking concurrency guarantee, under REAL concurrent
   connections against a REAL database with REAL MVCC -- the SQLite
   version of this test (tests/unit/test_booking_service.py) uses a
   shared SQLite file specifically to approximate what only Postgres
   can actually provide natively.
"""
import asyncio
import secrets
from datetime import date, time, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.auth.models import User, EmailVerificationToken
from app.auth import service as auth_service
from app.auth.schemas import UserRegister
from app.operators.models import Operator, Vehicle, Route, Schedule, Seat
from app.booking.schemas import BookingCreate, PassengerInput
from app.booking import service as booking_service
from app.common.enums import UserRole, TransportType, ScheduleStatus, SeatCategory, SeatStatus
from tests.postgres.conftest import TEST_DATABASE_URL


@pytest.mark.asyncio
async def test_native_enum_rejects_invalid_value_at_db_level(pg_session):
    """
    This is THE test that SQLite structurally cannot perform: proving the
    database itself, not just application code, rejects an invalid enum
    value. This is the defense-in-depth guarantee the enum design was
    chosen for (see app/common/enums.py docstring).
    """
    user = User(
        email="enumtest@example.com", password_hash="x", first_name="E", last_name="T",
        role=UserRole.CUSTOMER,
    )
    pg_session.add(user)
    await pg_session.commit()

    with pytest.raises(Exception) as exc_info:
        await pg_session.execute(
            text("UPDATE users SET role = 'HACKER' WHERE id = :id"), {"id": user.id}
        )
        await pg_session.commit()

    assert "invalid input value for enum" in str(exc_info.value).lower()
    await pg_session.rollback()


@pytest.mark.asyncio
async def test_email_verification_token_expiry_against_real_postgres(pg_session):
    """
    Re-verifies the exact bug found earlier (naive-vs-aware datetime
    comparison) against real Postgres, which has proper TIMESTAMPTZ
    support and should never have exhibited this bug in the first place --
    confirming the fix works correctly on the backend where it was never
    actually broken, not just on the backend where the workaround was needed.
    """
    registration = UserRegister(
        email="pgverify@example.com", password="StrongPass123!",
        first_name="PG", last_name="Test",
    )
    user = await auth_service.register_user(pg_session, registration)

    result = await pg_session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    )
    token_row = result.scalar_one()

    verified_user = await auth_service.verify_email(pg_session, token_row.token)
    assert verified_user.is_email_verified is True


async def _seed_pg_schedule(db, num_seats=1):
    suffix = secrets.token_hex(4)
    customer = User(email=f"rider_{suffix}@test.com", password_hash="x", first_name="R", last_name="R", role=UserRole.CUSTOMER)
    op_user = User(email=f"op_{suffix}@test.com", password_hash="x", first_name="O", last_name="O", role=UserRole.OPERATOR)
    db.add_all([customer, op_user])
    await db.flush()

    operator = Operator(user_id=op_user.id, operator_name="PG Test Co", operator_type=TransportType.BUS, is_verified=True)
    db.add(operator)
    await db.flush()

    vehicle = Vehicle(operator_id=operator.id, vehicle_type=TransportType.BUS, registration_number=f"PG-{suffix}", total_seats=num_seats, seat_configuration={"ECONOMY": num_seats})
    db.add(vehicle)
    await db.flush()

    route = Route(operator_id=operator.id, route_code=f"PGRT-{suffix}", departure_city="Karachi", arrival_city="Lahore")
    db.add(route)
    await db.flush()

    schedule = Schedule(
        operator_id=operator.id, route_id=route.id, vehicle_id=vehicle.id,
        departure_date=date.today() + timedelta(days=1), departure_time=time(8, 0), arrival_time=time(14, 0),
        base_fare=2000.0, total_seats=num_seats, available_seats=num_seats, status=ScheduleStatus.SCHEDULED,
    )
    db.add(schedule)
    await db.flush()

    seats = []
    for i in range(num_seats):
        seat = Seat(schedule_id=schedule.id, seat_number=f"{i+1}A", seat_category=SeatCategory.ECONOMY, status=SeatStatus.AVAILABLE, price=2000.0)
        db.add(seat)
        seats.append(seat)

    await db.commit()
    for s in seats:
        await db.refresh(s)
    await db.refresh(customer)

    return customer, schedule, seats


@pytest.mark.asyncio
async def test_concurrent_booking_same_seat_real_postgres_mvcc():
    """
    THE most important test in this file: the exact double-booking
    regression test from tests/unit/test_booking_service.py, but against
    real Postgres with real MVCC and real concurrent connections instead
    of two aiosqlite connections to a shared file (which only
    approximates concurrent access). This is the actual proof that the
    conditional-UPDATE locking strategy (see app/booking/service.py::lock_seats)
    holds under the real target database's concurrency model, not just a
    reasonable stand-in for it.
    """
    engine = create_async_engine(TEST_DATABASE_URL)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: None)
    except Exception as e:
        pytest.skip(f"Postgres not reachable: {e}")

    from app.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as setup_session:
        customer, schedule, seats = await _seed_pg_schedule(setup_session, num_seats=1)
        customer_id = customer.id
        schedule_id = schedule.id
        seat_id = seats[0].id

    async def attempt_booking():
        async with session_factory() as session:
            try:
                payload = BookingCreate(
                    schedule_id=schedule_id,
                    passengers=[PassengerInput(seat_id=seat_id, first_name="John", last_name="Doe")],
                    contact_email="john@test.com",
                )
                booking = await booking_service.create_booking(session, customer_id, payload)
                return ("success", booking.id)
            except Exception as e:
                return ("failure", getattr(e, "status_code", str(e)))

    # 5 concurrent attempts (more aggressive than the SQLite version's 2)
    # since real Postgres can handle genuine parallel connections rather
    # than aiosqlite's more limited concurrency model.
    results = await asyncio.gather(*[attempt_booking() for _ in range(5)])

    outcomes = [r[0] for r in results]
    assert outcomes.count("success") == 1, f"Expected exactly 1 success under real concurrency, got: {results}"
    assert outcomes.count("failure") == 4, f"Expected exactly 4 conflicts, got: {results}"

    for r in results:
        if r[0] == "failure":
            assert r[1] == 409, f"Expected 409 conflict status, got {r[1]}"

    async with session_factory() as verify_session:
        result = await verify_session.execute(select(Seat).where(Seat.id == seat_id))
        final_seat = result.scalar_one()
        assert final_seat.status == SeatStatus.LOCKED

        winning_booking_id = next(r[1] for r in results if r[0] == "success")
        assert final_seat.locked_by_booking_id == winning_booking_id

    await engine.dispose()
