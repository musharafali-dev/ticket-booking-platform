"""Pydantic schemas for search endpoints."""

from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import TransportType, ScheduleStatus


class ScheduleSearchQuery(BaseModel):
    departure_city: str
    arrival_city: str
    departure_date: date
    transport_type: Optional[TransportType] = None
    min_seats_available: int = Field(default=1, ge=1)


class OperatorSummary(BaseModel):
    id: int
    operator_name: str
    operator_type: TransportType

    model_config = ConfigDict(from_attributes=True)


class RouteSummary(BaseModel):
    id: int
    route_code: str
    departure_city: str
    arrival_city: str
    distance_km: Optional[float]
    estimated_duration_minutes: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class ScheduleSearchResult(BaseModel):
    id: int
    departure_date: date
    departure_time: time
    arrival_time: time
    base_fare: float
    available_seats: int
    total_seats: int
    status: ScheduleStatus
    operator: OperatorSummary
    route: RouteSummary

    model_config = ConfigDict(from_attributes=True)


class SeatDetail(BaseModel):
    id: int
    seat_number: str
    seat_category: str
    status: str
    price: float

    model_config = ConfigDict(from_attributes=True)


class ScheduleDetailResponse(ScheduleSearchResult):
    seats: list[SeatDetail]
