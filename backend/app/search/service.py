"""
Search business logic.

Key performance decision: we use selectinload for operator/route/vehicle
relationships so listing N schedules costs a small constant number of
queries, not N+1. Seat availability is read from Schedule.available_seats
(a maintained counter) rather than counting Seat rows live — counting
thousands of seat rows per search result under load would be needlessly
expensive when the counter is already kept in sync by the booking flow.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.operators.models import Schedule, Route
from app.common.enums import TransportType, ScheduleStatus


async def search_schedules(
    db: AsyncSession,
    departure_city: str,
    arrival_city: str,
    departure_date: date,
    transport_type: TransportType | None = None,
    min_seats_available: int = 1,
) -> list[Schedule]:
    stmt = (
        select(Schedule)
        .join(Schedule.route)
        .where(
            Route.departure_city.ilike(departure_city.strip()),
            Route.arrival_city.ilike(arrival_city.strip()),
            Schedule.departure_date == departure_date,
            Schedule.status == ScheduleStatus.SCHEDULED,
            Schedule.available_seats >= min_seats_available,
        )
        .options(
            selectinload(Schedule.operator),
            selectinload(Schedule.route),
        )
        .order_by(Schedule.departure_time)
    )

    if transport_type is not None:
        stmt = stmt.where(Schedule.operator.has(operator_type=transport_type))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_schedule_with_seats(
    db: AsyncSession, schedule_id: int
) -> Schedule | None:
    stmt = (
        select(Schedule)
        .where(Schedule.id == schedule_id)
        .options(
            selectinload(Schedule.operator),
            selectinload(Schedule.route),
            selectinload(Schedule.seats),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_cities(db: AsyncSession) -> list[str]:
    """
    Returns the distinct set of cities that appear as either a departure or
    arrival point across all active routes — used to populate search
    autocomplete on the frontend.
    """
    dep_result = await db.execute(select(Route.departure_city).distinct())
    arr_result = await db.execute(select(Route.arrival_city).distinct())
    cities = set(dep_result.scalars().all()) | set(arr_result.scalars().all())
    return sorted(cities)
