"""Pydantic schemas for booking endpoints."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator

from app.common.enums import BookingStatus, PaymentStatus


class PassengerInput(BaseModel):
    seat_id: int
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    id_type: Optional[str] = Field(default=None, max_length=50)
    id_number: Optional[str] = Field(default=None, max_length=50)


class BookingCreate(BaseModel):
    schedule_id: int
    passengers: list[PassengerInput] = Field(min_length=1, max_length=10)
    contact_email: EmailStr
    contact_phone: Optional[str] = None

    @model_validator(mode="after")
    def seats_must_be_unique(self):
        seat_ids = [p.seat_id for p in self.passengers]
        if len(seat_ids) != len(set(seat_ids)):
            raise ValueError("Each passenger must have a distinct seat")
        return self


class PassengerResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    seat_number: str

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: int
    booking_code: str
    number_of_passengers: int
    total_amount: float
    status: BookingStatus
    payment_status: PaymentStatus
    contact_email: str
    expires_at: datetime
    created_at: datetime
    passengers: list[PassengerResponse]

    model_config = ConfigDict(from_attributes=True)


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)
