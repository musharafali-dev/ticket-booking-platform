"""Search API routes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.search import service
from app.search.schemas import ScheduleSearchResult, ScheduleDetailResponse
from app.common.enums import TransportType
from app.database import get_db

router = APIRouter()


@router.get("/schedules", response_model=list[ScheduleSearchResult])
async def search_schedules(
    departure_city: str = Query(..., min_length=1),
    arrival_city: str = Query(..., min_length=1),
    departure_date: date = Query(...),
    transport_type: TransportType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    schedules = await service.search_schedules(
        db,
        departure_city=departure_city,
        arrival_city=arrival_city,
        departure_date=departure_date,
        transport_type=transport_type,
    )
    return schedules


@router.get("/schedules/{schedule_id}", response_model=ScheduleDetailResponse)
async def get_schedule_detail(schedule_id: int, db: AsyncSession = Depends(get_db)):
    schedule = await service.get_schedule_with_seats(db, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.get("/cities", response_model=list[str])
async def list_cities(db: AsyncSession = Depends(get_db)):
    return await service.list_cities(db)
