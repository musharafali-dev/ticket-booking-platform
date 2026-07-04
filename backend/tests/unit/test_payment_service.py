"""
Tests for app.payment.service.

Covers the mock gateway's synchronous completion path (the one path that's
fully testable without real credentials) and the resulting state
transitions on Booking and Seat.
"""

import secrets
from datetime import date, time, timedelta, datetime, timezone

import pytest
from sqlalchemy import select

from app.auth.models import User
from app.operators.models import Operator, Vehicle, Route, Schedule, Seat
from app.booking.models import Booking
from app.booking.schemas import BookingCreate, PassengerInput
from app.booking import service as booking_service
from app.payment import service as payment_service
from app.payment.models import Payment
from app.common.enums import (
    UserRole,
    TransportType,
    ScheduleStatus,
    SeatCategory,
    SeatStatus,
    BookingStatus,
    PaymentStatus,
    PaymentProvider,
)


async def _seed_pending_booking(db, price=2000.0):
    suffix = secrets.token_hex(4)
    customer = User(
        email=f"rider_{suffix}@test.com",
        password_hash="x",
        first_name="R",
        last_name="R",
        role=UserRole.CUSTOMER,
    )
    op_user = User(
        email=f"op_{suffix}@test.com",
        password_hash="x",
        first_name="O",
        last_name="O",
        role=UserRole.OPERATOR,
    )
    db.add_all([customer, op_user])
    await db.flush()

    operator = Operator(
        user_id=op_user.id,
        operator_name="Test Co",
        operator_type=TransportType.BUS,
        is_verified=True,
    )
    db.add(operator)
    await db.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        vehicle_type=TransportType.BUS,
        registration_number=f"BUS-{suffix}",
        total_seats=5,
        seat_configuration={"ECONOMY": 5},
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
        total_seats=5,
        available_seats=5,
        status=ScheduleStatus.SCHEDULED,
    )
    db.add(schedule)
    await db.flush()

    seat = Seat(
        schedule_id=schedule.id,
        seat_number="1A",
        seat_category=SeatCategory.ECONOMY,
        status=SeatStatus.AVAILABLE,
        price=price,
    )
    db.add(seat)
    await db.commit()
    await db.refresh(seat)
    await db.refresh(customer)

    payload = BookingCreate(
        schedule_id=schedule.id,
        passengers=[
            PassengerInput(seat_id=seat.id, first_name="John", last_name="Doe")
        ],
        contact_email="john@test.com",
    )
    booking = await booking_service.create_booking(db, customer.id, payload)
    return customer, booking, seat


@pytest.mark.asyncio
async def test_initiate_payment_with_mock_gateway_completes_synchronously(
    db_session, monkeypatch
):
    monkeypatch.setattr("app.config.settings.PAYMENT_PROVIDER", "mock")
    customer, booking, seat = await _seed_pending_booking(db_session)

    payment, result = await payment_service.initiate_payment(
        db_session, booking.id, customer.id
    )

    assert payment.status == PaymentStatus.COMPLETED
    assert payment.provider == PaymentProvider.MOCK
    assert result.requires_redirect is False
    assert result.redirect_url is None


@pytest.mark.asyncio
async def test_successful_mock_payment_confirms_booking(db_session, monkeypatch):
    monkeypatch.setattr("app.config.settings.PAYMENT_PROVIDER", "mock")
    customer, booking, seat = await _seed_pending_booking(db_session)

    await payment_service.initiate_payment(db_session, booking.id, customer.id)

    result = await db_session.execute(select(Booking).where(Booking.id == booking.id))
    refreshed_booking = result.scalar_one()
    assert refreshed_booking.status == BookingStatus.CONFIRMED
    assert refreshed_booking.payment_status == PaymentStatus.COMPLETED


@pytest.mark.asyncio
async def test_successful_payment_transitions_seat_to_booked(db_session, monkeypatch):
    monkeypatch.setattr("app.config.settings.PAYMENT_PROVIDER", "mock")
    customer, booking, seat = await _seed_pending_booking(db_session)

    await payment_service.initiate_payment(db_session, booking.id, customer.id)

    result = await db_session.execute(select(Seat).where(Seat.id == seat.id))
    refreshed_seat = result.scalar_one()
    assert refreshed_seat.status == SeatStatus.BOOKED


@pytest.mark.asyncio
async def test_cannot_initiate_payment_twice_for_same_booking(db_session, monkeypatch):
    monkeypatch.setattr("app.config.settings.PAYMENT_PROVIDER", "mock")
    customer, booking, seat = await _seed_pending_booking(db_session)

    await payment_service.initiate_payment(db_session, booking.id, customer.id)

    with pytest.raises(Exception) as exc_info:
        await payment_service.initiate_payment(db_session, booking.id, customer.id)
    assert getattr(exc_info.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_cannot_pay_for_someone_elses_booking(db_session, monkeypatch):
    monkeypatch.setattr("app.config.settings.PAYMENT_PROVIDER", "mock")
    customer, booking, seat = await _seed_pending_booking(db_session)

    other_user = User(
        email="intruder@test.com",
        password_hash="x",
        first_name="I",
        last_name="U",
        role=UserRole.CUSTOMER,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    with pytest.raises(Exception) as exc_info:
        await payment_service.initiate_payment(db_session, booking.id, other_user.id)
    assert getattr(exc_info.value, "status_code", None) == 404


@pytest.mark.asyncio
async def test_cannot_pay_for_expired_booking(db_session, monkeypatch):
    monkeypatch.setattr("app.config.settings.PAYMENT_PROVIDER", "mock")
    customer, booking, seat = await _seed_pending_booking(db_session)

    result = await db_session.execute(select(Booking).where(Booking.id == booking.id))
    b = result.scalar_one()
    b.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    with pytest.raises(Exception) as exc_info:
        await payment_service.initiate_payment(db_session, booking.id, customer.id)
    assert getattr(exc_info.value, "status_code", None) == 400
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_jazzcash_gateway_without_credentials_raises_clean_503(
    db_session, monkeypatch
):
    """
    Regression guard for a real usability concern: setting
    PAYMENT_PROVIDER=jazzcash without configuring credentials should fail
    with a clear, actionable 503 — not a raw NotImplementedError leaking
    as an unhandled 500 or a confusing stack trace.
    """
    monkeypatch.setattr("app.config.settings.PAYMENT_PROVIDER", "jazzcash")
    monkeypatch.setattr("app.config.settings.JAZZCASH_MERCHANT_ID", "")
    customer, booking, seat = await _seed_pending_booking(db_session)

    with pytest.raises(Exception) as exc_info:
        await payment_service.initiate_payment(db_session, booking.id, customer.id)
    assert getattr(exc_info.value, "status_code", None) == 503
    assert "not configured" in exc_info.value.detail.lower()


def test_jazzcash_signature_verification_round_trips(monkeypatch):
    """
    Verifies the HMAC signing/verification scheme is internally consistent:
    a signature computed by _compute_secure_hash must be accepted by
    verify_callback_signature for the same fields, and rejected if any
    field is tampered with.
    """
    monkeypatch.setattr(
        "app.config.settings.JAZZCASH_INTEGRITY_SALT", "test-salt-value"
    )
    from app.payment.gateways.jazzcash_gateway import JazzCashGateway

    gateway = JazzCashGateway()
    fields = {"pp_Amount": 500000, "pp_MerchantID": "TEST123", "pp_TxnRefNo": "T123"}
    signature = gateway._compute_secure_hash(fields)

    payload_with_sig = {**fields, "pp_SecureHash": signature}
    assert gateway.verify_callback_signature(payload_with_sig, signature) is True

    tampered = {**fields, "pp_Amount": 999999, "pp_SecureHash": signature}
    assert gateway.verify_callback_signature(tampered, signature) is False


def test_easypaisa_signature_verification_round_trips(monkeypatch):
    monkeypatch.setattr("app.config.settings.EASYPAISA_HASH_KEY", "test-hash-key")
    from app.payment.gateways.easypaisa_gateway import EasyPaisaGateway

    gateway = EasyPaisaGateway()
    fields = {"storeId": "STORE1", "amount": "5000.00", "orderRefNum": "EP123"}
    signature = gateway._compute_hash(fields)

    payload_with_sig = {**fields, "signature": signature}
    assert gateway.verify_callback_signature(payload_with_sig, signature) is True

    tampered = {**fields, "amount": "1.00", "signature": signature}
    assert gateway.verify_callback_signature(tampered, signature) is False
