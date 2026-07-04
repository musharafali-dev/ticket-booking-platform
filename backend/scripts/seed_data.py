"""
Seed the database with demo data: operators, vehicles, routes, and schedules
for the next 7 days, with full seat inventory generated per schedule.

Idempotent: safe to re-run. Checks for existing seed marker (admin user)
before inserting, so it won't create duplicates if run twice.

Usage:
    python -m scripts.seed_data
"""

import asyncio
import sys
from datetime import date, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import AsyncSessionLocal, engine, Base
import app.models_registry  # noqa: F401
from app.auth.models import User
from app.operators.models import Operator, Vehicle, Route, Schedule, Seat
from app.common.enums import (
    UserRole,
    TransportType,
    SeatCategory,
    SeatStatus,
    ScheduleStatus,
)
from app.common.security import hash_password

PAKISTANI_ROUTES = [
    ("Karachi", "Lahore", 1215, 14 * 60),
    ("Lahore", "Islamabad", 375, 5 * 60),
    ("Karachi", "Islamabad", 1400, 16 * 60),
    ("Lahore", "Karachi", 1215, 14 * 60),
    ("Islamabad", "Peshawar", 185, 3 * 60),
    ("Lahore", "Multan", 340, 5 * 60),
    ("Karachi", "Hyderabad", 165, 2 * 60 + 30),
    ("Lahore", "Faisalabad", 130, 2 * 60),
    ("Islamabad", "Lahore", 375, 5 * 60),
    ("Quetta", "Karachi", 690, 10 * 60),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        existing = await db.execute(
            select(User).where(User.email == "admin@ticketbooking.pk")
        )
        if existing.scalar_one_or_none():
            print("Seed data already present, skipping.")
            return

        # ---- Admin user ----
        admin = User(
            email="admin@ticketbooking.pk",
            password_hash=hash_password("Admin@12345"),
            first_name="Platform",
            last_name="Admin",
            role=UserRole.ADMIN,
            is_email_verified=True,
        )
        db.add(admin)

        # ---- Demo customer ----
        customer = User(
            email="customer@example.com",
            password_hash=hash_password("Customer@123"),
            first_name="Ali",
            last_name="Khan",
            phone_number="+92-300-1234567",
            role=UserRole.CUSTOMER,
            is_email_verified=True,
        )
        db.add(customer)

        # ---- Operators (one per transport type) ----
        operator_defs = [
            ("Daewoo Express", TransportType.BUS, "operator.bus@example.com"),
            ("Pakistan Railways", TransportType.TRAIN, "operator.train@example.com"),
            ("PIA Domestic", TransportType.AIRPLANE, "operator.air@example.com"),
        ]

        operators = []
        for name, ttype, email in operator_defs:
            op_user = User(
                email=email,
                password_hash=hash_password("Operator@123"),
                first_name=name.split()[0],
                last_name="Operator",
                role=UserRole.OPERATOR,
                is_email_verified=True,
            )
            db.add(op_user)
            await db.flush()  # get op_user.id without committing

            operator = Operator(
                user_id=op_user.id,
                operator_name=name,
                operator_type=ttype,
                is_verified=True,
            )
            db.add(operator)
            operators.append(operator)

        await db.flush()

        # ---- Vehicles (2 per operator) ----
        vehicles_by_operator = {}
        for i, operator in enumerate(operators):
            vehicles_by_operator[operator.operator_type] = []
            for v in range(2):
                if operator.operator_type == TransportType.BUS:
                    total_seats, config = 40, {"ECONOMY": 40}
                elif operator.operator_type == TransportType.TRAIN:
                    total_seats, config = 60, {"ECONOMY": 45, "BUSINESS": 15}
                else:  # AIRPLANE
                    total_seats, config = 150, {"ECONOMY": 130, "BUSINESS": 20}

                vehicle = Vehicle(
                    operator_id=operator.id,
                    vehicle_type=operator.operator_type,
                    registration_number=f"{operator.operator_type.value[:2]}-{i}{v}-2026",
                    total_seats=total_seats,
                    seat_configuration=config,
                    amenities=(
                        {"wifi": True, "charging_ports": True}
                        if operator.operator_type != TransportType.BUS
                        else {"ac": True}
                    ),
                )
                db.add(vehicle)
                vehicles_by_operator[operator.operator_type].append(vehicle)

        await db.flush()

        # ---- Routes (distributed across operators) ----
        routes = []
        for idx, (dep_city, arr_city, distance, duration) in enumerate(
            PAKISTANI_ROUTES
        ):
            operator = operators[idx % len(operators)]
            route = Route(
                operator_id=operator.id,
                route_code=f"RT-{idx + 1:04d}",
                departure_city=dep_city,
                arrival_city=arr_city,
                distance_km=distance,
                estimated_duration_minutes=duration,
            )
            db.add(route)
            routes.append((route, operator))

        await db.flush()

        # ---- Schedules for next 7 days + seat inventory ----
        base_fare_by_type = {
            TransportType.BUS: 2500.0,
            TransportType.TRAIN: 1800.0,
            TransportType.AIRPLANE: 15000.0,
        }

        seat_letters = "ABCDEF"
        schedules_created = 0
        seats_created = 0

        # Track (vehicle_id, date, hour) triples already used — a single vehicle
        # can't depart twice at the same date/time (DB unique constraint), so we
        # must respect that here rather than relying on the DB to fail loudly.
        used_vehicle_slots: set[tuple] = set()

        for route_idx, (route, operator) in enumerate(routes):
            # Alternate between the operator's two vehicles per route so the
            # same vehicle isn't double-booked into overlapping time slots.
            vehicles = vehicles_by_operator[operator.operator_type]
            vehicle = vehicles[route_idx % len(vehicles)]
            base_fare = base_fare_by_type[operator.operator_type]

            for day_offset in range(7):
                dep_date = date.today() + timedelta(days=day_offset)

                hour = 6
                while (vehicle.id, dep_date, hour) in used_vehicle_slots and hour < 22:
                    hour += 3
                used_vehicle_slots.add((vehicle.id, dep_date, hour))

                duration_hours = max(1, (route.estimated_duration_minutes or 180) // 60)
                arrival_hour = (hour + duration_hours) % 24

                schedule = Schedule(
                    operator_id=operator.id,
                    route_id=route.id,
                    vehicle_id=vehicle.id,
                    departure_date=dep_date,
                    departure_time=time(hour=hour),
                    arrival_time=time(hour=arrival_hour),
                    base_fare=base_fare,
                    total_seats=vehicle.total_seats,
                    available_seats=vehicle.total_seats,
                    status=ScheduleStatus.SCHEDULED,
                )
                db.add(schedule)
                await db.flush()
                schedules_created += 1

                # Generate seat inventory matching the vehicle's seat_configuration
                seat_num = 0
                for category_name, count in vehicle.seat_configuration.items():
                    category = SeatCategory[category_name]
                    price_multiplier = 1.5 if category == SeatCategory.BUSINESS else 1.0
                    for _ in range(count):
                        row = seat_num // len(seat_letters) + 1
                        letter = seat_letters[seat_num % len(seat_letters)]
                        seat = Seat(
                            schedule_id=schedule.id,
                            seat_number=f"{row}{letter}",
                            seat_category=category,
                            status=SeatStatus.AVAILABLE,
                            price=round(base_fare * price_multiplier, 2),
                        )
                        db.add(seat)
                        seat_num += 1
                        seats_created += 1

        await db.commit()
        print(
            f"Seed complete: {len(operators)} operators, {len(routes)} routes, "
            f"{schedules_created} schedules, {seats_created} seats."
        )
        print("\nDemo credentials:")
        print("  Admin:    admin@ticketbooking.pk / Admin@12345")
        print("  Customer: customer@example.com / Customer@123")
        print("  Operator: operator.bus@example.com / Operator@123")


if __name__ == "__main__":
    asyncio.run(seed())
