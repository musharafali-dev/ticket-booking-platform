"""Booking API routes."""

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.booking import service
from app.booking.schemas import BookingCreate, BookingResponse, BookingCancelRequest
from app.booking.exceptions import BookingNotFoundError, InvalidBookingStateError
from app.auth.models import User
from app.common.dependencies import get_current_user
from app.database import get_db

router = APIRouter()


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_booking(db, current_user.id, data)


@router.get("", response_model=list[BookingResponse])
async def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_user_bookings(db, current_user.id)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.get_booking_by_id(db, booking_id, user_id=current_user.id)
    except BookingNotFoundError:
        raise HTTPException(status_code=404, detail="Booking not found")


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    data: BookingCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.cancel_booking(
            db, booking_id, current_user.id, data.reason
        )
    except BookingNotFoundError:
        raise HTTPException(status_code=404, detail="Booking not found")
    except InvalidBookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
