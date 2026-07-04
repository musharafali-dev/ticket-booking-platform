"""
End-to-end integration test: the full user journey through real HTTP
requests against the assembled FastAPI app via httpx's ASGI transport.

Distinct from tests/unit/*, which call service functions directly and
never exercise FastAPI's routing, dependency injection, or serialization
layers. This is the only test in the suite that would catch a broken
route registration, a wrong response_model, or a dependency override
wired incorrectly — categories of bug unit tests structurally cannot see.
"""

from datetime import date, time, timedelta

import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
import app.models_registry  # noqa: F401
from app.main import app
from app.auth.models import User
from app.operators.models import Operator, Vehicle, Route, Schedule, Seat
from app.common.enums import (
    UserRole,
    TransportType,
    ScheduleStatus,
    SeatCategory,
    SeatStatus,
)
from app.common.security import hash_password


@pytest.fixture
async def e2e_client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with session_factory() as db:
        op_user = User(
            email="operator@e2etest.com",
            password_hash=hash_password("x"),
            first_name="Op",
            last_name="User",
            role=UserRole.OPERATOR,
            is_email_verified=True,
        )
        db.add(op_user)
        await db.flush()
        operator = Operator(
            user_id=op_user.id,
            operator_name="E2E Bus Co",
            operator_type=TransportType.BUS,
            is_verified=True,
        )
        db.add(operator)
        await db.flush()
        vehicle = Vehicle(
            operator_id=operator.id,
            vehicle_type=TransportType.BUS,
            registration_number="E2E-1",
            total_seats=10,
            seat_configuration={"ECONOMY": 10},
        )
        db.add(vehicle)
        await db.flush()
        route = Route(
            operator_id=operator.id,
            route_code="E2E-RT",
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
            departure_time=time(9, 0),
            arrival_time=time(15, 0),
            base_fare=3000.0,
            total_seats=10,
            available_seats=10,
            status=ScheduleStatus.SCHEDULED,
        )
        db.add(schedule)
        await db.flush()
        for i in range(10):
            db.add(
                Seat(
                    schedule_id=schedule.id,
                    seat_number=f"{i+1}A",
                    seat_category=SeatCategory.ECONOMY,
                    status=SeatStatus.AVAILABLE,
                    price=3000.0,
                )
            )
        await db.commit()
        schedule_id = schedule.id

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, schedule_id

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_full_booking_journey(e2e_client):
    client, schedule_id = e2e_client

    # 1. Register
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e@example.com",
            "password": "E2ETest123!",
            "first_name": "E2E",
            "last_name": "Test",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["is_email_verified"] is False

    # 2. Login
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "e2e@example.com", "password": "E2ETest123!"},
    )
    assert resp.status_code == 200
    access_token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. /me
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "e2e@example.com"

    # 4. Search
    resp = await client.get(
        "/api/v1/search/schedules",
        params={
            "departure_city": "Karachi",
            "arrival_city": "Lahore",
            "departure_date": str(date.today() + timedelta(days=1)),
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # 5. Schedule detail + seats
    resp = await client.get(f"/api/v1/search/schedules/{schedule_id}")
    assert resp.status_code == 200
    seats = resp.json()["seats"]
    assert len(seats) == 10
    seat_id = seats[0]["id"]

    # 6. Unauthenticated booking rejected
    resp = await client.post(
        "/api/v1/bookings",
        json={
            "schedule_id": schedule_id,
            "passengers": [
                {"seat_id": seat_id, "first_name": "John", "last_name": "Doe"}
            ],
            "contact_email": "e2e@example.com",
        },
    )
    assert resp.status_code == 401

    # 7. Authenticated booking succeeds
    resp = await client.post(
        "/api/v1/bookings",
        headers=headers,
        json={
            "schedule_id": schedule_id,
            "passengers": [
                {"seat_id": seat_id, "first_name": "John", "last_name": "Doe"}
            ],
            "contact_email": "e2e@example.com",
        },
    )
    assert resp.status_code == 201
    booking = resp.json()
    booking_id = booking["id"]
    assert booking["status"] == "PENDING"
    assert booking["total_amount"] == 3000.0

    # 8. Re-booking the same seat conflicts
    resp = await client.post(
        "/api/v1/bookings",
        headers=headers,
        json={
            "schedule_id": schedule_id,
            "passengers": [
                {"seat_id": seat_id, "first_name": "Jane", "last_name": "Doe"}
            ],
            "contact_email": "e2e@example.com",
        },
    )
    assert resp.status_code == 409

    # 9. List bookings
    resp = await client.get("/api/v1/bookings", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # 10. Pay (mock gateway, synchronous)
    resp = await client.post(
        "/api/v1/payments/initiate", headers=headers, json={"booking_id": booking_id}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"

    # 11. Booking now confirmed
    resp = await client.get(f"/api/v1/bookings/{booking_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"
    assert resp.json()["payment_status"] == "COMPLETED"

    # 12. Cancel
    resp = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=headers,
        json={"reason": "test"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"

    # 13. Seat released
    resp = await client.get(f"/api/v1/search/schedules/{schedule_id}")
    released_seat = next(s for s in resp.json()["seats"] if s["id"] == seat_id)
    assert released_seat["status"] == "AVAILABLE"


@pytest.mark.asyncio
async def test_health_check(e2e_client):
    client, _ = e2e_client
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_openapi_schema_generates_without_error(e2e_client):
    """
    Guards against a schema that imports/runs fine but produces a broken
    OpenAPI spec (e.g. from an unresolvable Pydantic forward reference) —
    the kind of thing that only breaks when /api/docs is actually loaded,
    not when the app object is merely constructed.
    """
    client, _ = e2e_client
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    assert "/api/v1/bookings" in schema["paths"]
