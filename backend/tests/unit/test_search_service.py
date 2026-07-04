"""Tests for app.search.service."""

from datetime import date, time, timedelta

import pytest

from app.auth.models import User
from app.operators.models import Operator, Vehicle, Route, Schedule, Seat
from app.common.enums import (
    UserRole,
    TransportType,
    ScheduleStatus,
    SeatCategory,
    SeatStatus,
)
from app.search import service


async def _make_operator_with_route_and_schedule(
    db,
    transport_type=TransportType.BUS,
    dep_city="Karachi",
    arr_city="Lahore",
    dep_date=None,
    available_seats=10,
    status=ScheduleStatus.SCHEDULED,
):
    dep_date = dep_date or date.today() + timedelta(days=1)

    op_user = User(
        email=f"op_{dep_city}_{arr_city}_{transport_type.value}@test.com",
        password_hash="x",
        first_name="Op",
        last_name="User",
        role=UserRole.OPERATOR,
    )
    db.add(op_user)
    await db.flush()

    operator = Operator(
        user_id=op_user.id,
        operator_name="Test Operator",
        operator_type=transport_type,
        is_verified=True,
    )
    db.add(operator)
    await db.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        vehicle_type=transport_type,
        registration_number=f"REG-{op_user.id}",
        total_seats=40,
        seat_configuration={"ECONOMY": 40},
    )
    db.add(vehicle)
    await db.flush()

    route = Route(
        operator_id=operator.id,
        route_code=f"RT-{op_user.id}",
        departure_city=dep_city,
        arrival_city=arr_city,
    )
    db.add(route)
    await db.flush()

    schedule = Schedule(
        operator_id=operator.id,
        route_id=route.id,
        vehicle_id=vehicle.id,
        departure_date=dep_date,
        departure_time=time(8, 0),
        arrival_time=time(14, 0),
        base_fare=2000.0,
        total_seats=40,
        available_seats=available_seats,
        status=status,
    )
    db.add(schedule)
    await db.flush()

    for i in range(available_seats):
        db.add(
            Seat(
                schedule_id=schedule.id,
                seat_number=f"{i+1}A",
                seat_category=SeatCategory.ECONOMY,
                status=SeatStatus.AVAILABLE,
                price=2000.0,
            )
        )
    await db.commit()
    return schedule


@pytest.mark.asyncio
async def test_search_matches_exact_route_and_date(db_session):
    schedule = await _make_operator_with_route_and_schedule(db_session)

    results = await service.search_schedules(
        db_session,
        departure_city="Karachi",
        arrival_city="Lahore",
        departure_date=schedule.departure_date,
    )

    assert len(results) == 1
    assert results[0].id == schedule.id


@pytest.mark.asyncio
async def test_search_case_insensitive(db_session):
    schedule = await _make_operator_with_route_and_schedule(
        db_session, dep_city="Karachi", arr_city="Lahore"
    )

    results = await service.search_schedules(
        db_session,
        departure_city="karachi",
        arrival_city="LAHORE",
        departure_date=schedule.departure_date,
    )
    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_excludes_wrong_date(db_session):
    schedule = await _make_operator_with_route_and_schedule(db_session)
    wrong_date = schedule.departure_date + timedelta(days=1)

    results = await service.search_schedules(
        db_session,
        departure_city="Karachi",
        arrival_city="Lahore",
        departure_date=wrong_date,
    )
    assert results == []


@pytest.mark.asyncio
async def test_search_excludes_cancelled_schedules(db_session):
    schedule = await _make_operator_with_route_and_schedule(
        db_session, status=ScheduleStatus.CANCELLED
    )

    results = await service.search_schedules(
        db_session,
        departure_city="Karachi",
        arrival_city="Lahore",
        departure_date=schedule.departure_date,
    )
    assert results == []


@pytest.mark.asyncio
async def test_search_excludes_fully_booked_schedules(db_session):
    schedule = await _make_operator_with_route_and_schedule(
        db_session, available_seats=0
    )

    results = await service.search_schedules(
        db_session,
        departure_city="Karachi",
        arrival_city="Lahore",
        departure_date=schedule.departure_date,
    )
    assert results == []


@pytest.mark.asyncio
async def test_search_filters_by_transport_type(db_session):
    bus_schedule = await _make_operator_with_route_and_schedule(
        db_session,
        transport_type=TransportType.BUS,
        dep_city="Quetta",
        arr_city="Multan",
    )
    train_schedule = await _make_operator_with_route_and_schedule(
        db_session,
        transport_type=TransportType.TRAIN,
        dep_city="Quetta",
        arr_city="Multan",
        dep_date=bus_schedule.departure_date,
    )

    results = await service.search_schedules(
        db_session,
        departure_city="Quetta",
        arrival_city="Multan",
        departure_date=bus_schedule.departure_date,
        transport_type=TransportType.TRAIN,
    )

    assert len(results) == 1
    assert results[0].id == train_schedule.id


@pytest.mark.asyncio
async def test_get_schedule_with_seats_returns_seat_list(db_session):
    schedule = await _make_operator_with_route_and_schedule(
        db_session, available_seats=5
    )

    result = await service.get_schedule_with_seats(db_session, schedule.id)

    assert result is not None
    assert len(result.seats) == 5


@pytest.mark.asyncio
async def test_get_schedule_with_seats_returns_none_for_missing_id(db_session):
    result = await service.get_schedule_with_seats(db_session, 999999)
    assert result is None


@pytest.mark.asyncio
async def test_list_cities_returns_unique_sorted(db_session):
    await _make_operator_with_route_and_schedule(
        db_session, dep_city="Lahore", arr_city="Karachi"
    )
    await _make_operator_with_route_and_schedule(
        db_session, dep_city="Karachi", arr_city="Islamabad"
    )

    cities = await service.list_cities(db_session)

    assert cities == sorted(set(cities))
    assert "Karachi" in cities
    assert "Lahore" in cities
    assert "Islamabad" in cities
