"""Payment API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.payment import service
from app.payment.schemas import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentResponse,
)
from app.auth.models import User
from app.common.dependencies import get_current_user
from app.database import get_db

router = APIRouter()


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    data: PaymentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment, redirect_info = await service.initiate_payment(
        db, data.booking_id, current_user.id
    )

    return PaymentInitiateResponse(
        payment_reference=payment.payment_reference,
        redirect_url=redirect_info.redirect_url,
        requires_redirect=redirect_info.requires_redirect,
        status=payment.status,
    )


@router.get("/booking/{booking_id}", response_model=PaymentResponse)
async def get_payment_for_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_payment_for_booking(db, booking_id, current_user.id)
