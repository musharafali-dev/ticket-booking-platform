"""
Payment business logic: orchestrates the gateway interface with booking
and seat state transitions. This module is the only thing that changes
depending on which gateway is active — it depends solely on
PaymentGatewayProvider, never a concrete class.
"""

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.payment.models import Payment
from app.payment.factory import get_payment_gateway
from app.payment.gateway import PaymentInitiationResult
from app.booking.models import Booking, BookingPassenger
from app.operators.models import Seat
from app.common.enums import PaymentStatus, BookingStatus, SeatStatus
from app.common.datetime_utils import is_expired


def _generate_payment_reference() -> str:
    return "PAY-" + secrets.token_hex(6).upper()


async def initiate_payment(
    db: AsyncSession, booking_id: int, user_id: int
) -> tuple[Payment, PaymentInitiationResult]:
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id)
    )
    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Booking is {booking.status.value}, cannot initiate payment",
        )
    if is_expired(booking.expires_at):
        raise HTTPException(
            status_code=400, detail="Booking has expired. Please create a new booking."
        )

    existing_payment = await db.execute(
        select(Payment).where(Payment.booking_id == booking_id)
    )
    if existing_payment.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=400, detail="A payment already exists for this booking"
        )

    gateway = get_payment_gateway()

    try:
        result = await gateway.initiate_payment(
            amount=booking.total_amount,
            currency="PKR",
            booking_reference=booking.booking_code,
            description=f"Ticket booking {booking.booking_code}",
        )
    except NotImplementedError as e:
        # Surfaces cleanly if PAYMENT_PROVIDER is set to jazzcash/easypaisa
        # before real credentials are configured, rather than a raw 500.
        raise HTTPException(status_code=503, detail=str(e))

    payment = Payment(
        payment_reference=_generate_payment_reference(),
        booking_id=booking.id,
        amount=booking.total_amount,
        currency="PKR",
        provider=gateway.provider,
        status=PaymentStatus.PROCESSING,
        external_transaction_id=result.external_transaction_id,
    )
    db.add(payment)
    booking.payment_status = PaymentStatus.PROCESSING
    await db.commit()
    await db.refresh(payment)

    # The mock gateway completes synchronously with no user redirect needed,
    # so we can confirm immediately rather than waiting for a callback that
    # will never arrive. Real gateways (requires_redirect=True) rely on
    # confirm_payment() being called later via their callback/webhook.
    if not result.requires_redirect:
        await confirm_payment(db, payment.id)
        await db.refresh(payment)

    return payment, result


async def confirm_payment(db: AsyncSession, payment_id: int) -> Payment:
    """
    Finalize a payment after the gateway confirms success: mark payment
    COMPLETED, booking CONFIRMED, and seats BOOKED (transitioning them out
    of LOCKED). This is the only path that turns a LOCKED seat into a
    permanently BOOKED one.
    """
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    gateway = get_payment_gateway()
    verification = await gateway.verify_payment(
        external_transaction_id=payment.external_transaction_id
    )

    if not verification.is_successful:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = (
            verification.failure_reason or "Payment verification failed"
        )

        booking_result = await db.execute(
            select(Booking).where(Booking.id == payment.booking_id)
        )
        booking = booking_result.scalar_one()
        booking.payment_status = PaymentStatus.FAILED

        await db.commit()
        await db.refresh(payment)
        return payment

    payment.status = PaymentStatus.COMPLETED
    payment.paid_at = datetime.now(timezone.utc)

    booking_result = await db.execute(
        select(Booking).where(Booking.id == payment.booking_id)
    )
    booking = booking_result.scalar_one()
    booking.status = BookingStatus.CONFIRMED
    booking.payment_status = PaymentStatus.COMPLETED

    seat_ids_result = await db.execute(
        select(BookingPassenger.seat_id).where(
            BookingPassenger.booking_id == booking.id
        )
    )
    seat_ids = list(seat_ids_result.scalars().all())

    await db.execute(
        update(Seat).where(Seat.id.in_(seat_ids)).values(status=SeatStatus.BOOKED)
    )

    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payment_for_booking(
    db: AsyncSession, booking_id: int, user_id: int
) -> Payment:
    result = await db.execute(
        select(Payment)
        .join(Booking, Payment.booking_id == Booking.id)
        .where(Payment.booking_id == booking_id, Booking.user_id == user_id)
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(
            status_code=404, detail="Payment not found for this booking"
        )
    return payment
