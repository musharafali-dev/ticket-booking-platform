"""
Seed the database with demo data: operators, vehicles, routes, and schedules
for the next 7 days, with full seat inventory generated per schedule.

This script drops existing tables and recreates them to ensure a fresh, rich
and clean seed dataset.

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
    ("Peshawar", "Islamabad", 185, 3 * 60),
    ("Multan", "Lahore", 340, 5 * 60),
    ("Faisalabad", "Lahore", 130, 2 * 60),
    ("Karachi", "Quetta", 690, 10 * 60),
]


async def seed():
    print("Dropping existing database tables to perform a clean, rich reset...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
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

        # ---- Operators (3 per transport type) ----
        operator_defs = [
            ("Daewoo Express", TransportType.BUS, "operator.daewoo@example.com"),
            ("Faisal Movers", TransportType.BUS, "operator.faisal@example.com"),
            ("Bilal Travels", TransportType.BUS, "operator.bilal@example.com"),
            ("Pakistan Railways", TransportType.TRAIN, "operator.train@example.com"),
            ("Tezgam Express", TransportType.TRAIN, "operator.tezgam@example.com"),
            ("Green Line Express", TransportType.TRAIN, "operator.greenline@example.com"),
            ("PIA Domestic", TransportType.AIRPLANE, "operator.pia@example.com"),
            ("AirSial", TransportType.AIRPLANE, "operator.airsial@example.com"),
            ("Airblue", TransportType.AIRPLANE, "operator.airblue@example.com"),
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
            await db.flush()  # get op_user.id

            operator = Operator(
                user_id=op_user.id,
                operator_name=name,
                operator_type=ttype,
                is_verified=True,
            )
            db.add(operator)
            operators.append(operator)

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

        # ---- Vehicles & Schedules allocation ----
        departure_slots = {
            TransportType.BUS: [time(8, 0), time(14, 0), time(20, 0)],
            TransportType.TRAIN: [time(9, 0), time(18, 0)],
            TransportType.AIRPLANE: [time(11, 0), time(17, 0)],
        }

        # Create dedicated vehicles for each route-departure slot to avoid duplicates
        vehicles_by_route_slot = {}
        vehicle_counter = 1
        for route, operator in routes:
            slots = departure_slots[operator.operator_type]
            vehicles_by_route_slot[route.id] = []
            for slot_idx in range(len(slots)):
                if operator.operator_type == TransportType.BUS:
                    total_seats, config = 40, {"ECONOMY": 40}
                elif operator.operator_type == TransportType.TRAIN:
                    total_seats, config = 60, {"ECONOMY": 45, "BUSINESS": 15}
                else:  # AIRPLANE
                    total_seats, config = 150, {"ECONOMY": 130, "BUSINESS": 20}

                vehicle = Vehicle(
                    operator_id=operator.id,
                    vehicle_type=operator.operator_type,
                    registration_number=f"{operator.operator_type.value[:2]}-{operator.id}-{vehicle_counter}-2026",
                    total_seats=total_seats,
                    seat_configuration=config,
                    amenities=(
                        {"wifi": True, "charging_ports": True}
                        if operator.operator_type != TransportType.BUS
                        else {"ac": True}
                    ),
                )
                db.add(vehicle)
                vehicles_by_route_slot[route.id].append(vehicle)
                vehicle_counter += 1

        await db.flush()

        # ---- Schedules & Seat Inventory for next 7 days ----
        base_fare_by_type = {
            TransportType.BUS: 2500.0,
            TransportType.TRAIN: 1800.0,
            TransportType.AIRPLANE: 15000.0,
        }

        seat_letters = "ABCDEF"
        schedules_created = 0
        seats_created = 0

        for route, operator in routes:
            vehicles = vehicles_by_route_slot[route.id]
            base_fare = base_fare_by_type[operator.operator_type]
            slots = departure_slots[operator.operator_type]

            # Adjust base fares based on operator names to simulate premium vs budget options
            if "PIA" in operator.operator_name or "Daewoo" in operator.operator_name or "Green" in operator.operator_name:
                base_fare *= 1.15
            elif "Bilal" in operator.operator_name:
                base_fare *= 0.9

            for day_offset in range(7):
                dep_date = date.today() + timedelta(days=day_offset)

                for slot_idx, dep_time in enumerate(slots):
                    # Dedicate the vehicle assigned to this slot
                    vehicle = vehicles[slot_idx]

                    duration_hours = max(1, (route.estimated_duration_minutes or 180) // 60)
                    arrival_hour = (dep_time.hour + duration_hours) % 24
                    arr_time = time(hour=arrival_hour, minute=dep_time.minute)

                    schedule = Schedule(
                        operator_id=operator.id,
                        route_id=route.id,
                        vehicle_id=vehicle.id,
                        departure_date=dep_date,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        base_fare=round(base_fare, 2),
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
            f"{schedules_created} schedules, {seats_created} seats generated."
        )
        print("\nDemo credentials:")
        print("  Admin:    admin@ticketbooking.pk / Admin@12345")
        print("  Customer: customer@example.com / Customer@123")
        print("  Operator (Bus): operator.daewoo@example.com / Operator@123")
        print("  Operator (Train): operator.train@example.com / Operator@123")
        print("  Operator (Flight): operator.pia@example.com / Operator@123")


if __name__ == "__main__":
    asyncio.run(seed())
