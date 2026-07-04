"""Pydantic schemas for payment endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.common.enums import PaymentStatus, PaymentProvider


class PaymentInitiateRequest(BaseModel):
    booking_id: int


class PaymentInitiateResponse(BaseModel):
    payment_reference: str
    redirect_url: Optional[str]
    requires_redirect: bool
    status: PaymentStatus


class PaymentResponse(BaseModel):
    id: int
    payment_reference: str
    booking_id: int
    amount: float
    currency: str
    provider: PaymentProvider
    status: PaymentStatus
    paid_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
