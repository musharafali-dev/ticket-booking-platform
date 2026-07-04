"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Enum type definitions ----
    # IMPORTANT: do NOT pre-create these via e.create(bind, checkfirst=True)
    # and then also pass them as column types to op.create_table(). That was
    # the original (broken) approach here, and it fails against real Postgres
    # with "type X already exists" — Alembic's create_table() auto-creates
    # Enum column types internally via a `before_create` DDL event that does
    # NOT respect checkfirst=True the way SQLAlchemy's own
    # MetaData.create_all() does. This went undetected against SQLite during
    # initial development because SQLite has no native ENUM type at all (it's
    # emulated as VARCHAR + CHECK), so this Postgres-specific DDL path was
    # never exercised until running this migration against real Postgres.
    #
    # Since each enum below is used in exactly one create_table() call, the
    # correct approach is simply to let create_table() create it on first
    # (and only) use — no separate creation step needed. If an enum were ever
    # reused across multiple tables, the correct pattern would be to create
    # it once explicitly with checkfirst=True, then pass
    # sa.Enum(..., name="x", create_type=False) to every subsequent column
    # referencing it.
    user_role = sa.Enum("CUSTOMER", "OPERATOR", "ADMIN", name="user_role")
    transport_type = sa.Enum("BUS", "TRAIN", "AIRPLANE", name="transport_type")
    vehicle_type = sa.Enum("BUS", "TRAIN", "AIRPLANE", name="vehicle_type")
    schedule_status = sa.Enum("SCHEDULED", "CANCELLED", "COMPLETED", name="schedule_status")
    seat_category = sa.Enum("ECONOMY", "BUSINESS", "FIRST", name="seat_category")
    seat_status = sa.Enum("AVAILABLE", "LOCKED", "BOOKED", "BLOCKED", name="seat_status")
    booking_status = sa.Enum("PENDING", "CONFIRMED", "CANCELLED", "EXPIRED", name="booking_status")
    payment_status = sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", "REFUNDED", name="payment_status")
    payment_record_status = sa.Enum(
        "PENDING", "PROCESSING", "COMPLETED", "FAILED", "REFUNDED", name="payment_record_status"
    )
    payment_provider = sa.Enum("MOCK", "JAZZCASH", "EASYPAISA", name="payment_provider")

    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("cnic_number", sa.String(20), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="CUSTOMER"),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("phone_number", name="uq_users_phone"),
        sa.UniqueConstraint("cnic_number", name="uq_users_cnic"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    # ---- email_verification_tokens ----
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("token", name="uq_email_verification_token"),
    )
    op.create_index("ix_evt_user_id", "email_verification_tokens", ["user_id"])
    op.create_index("ix_evt_token", "email_verification_tokens", ["token"])

    # ---- refresh_tokens ----
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("token_hash", name="uq_refresh_token_hash"),
    )
    op.create_index("ix_rt_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_rt_token_hash", "refresh_tokens", ["token_hash"])

    # ---- operators ----
    op.create_table(
        "operators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("operator_name", sa.String(255), nullable=False),
        sa.Column("operator_type", transport_type, nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_operators_user_id"),
    )
    op.create_index("ix_operators_type", "operators", ["operator_type"])
    op.create_index("ix_operators_verified", "operators", ["is_verified"])

    # ---- vehicles ----
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_type", vehicle_type, nullable=False),
        sa.Column("registration_number", sa.String(50), nullable=False),
        sa.Column("total_seats", sa.Integer(), nullable=False),
        sa.Column("seat_configuration", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("amenities", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("registration_number", name="uq_vehicles_registration"),
    )
    op.create_index("ix_vehicles_operator_id", "vehicles", ["operator_id"])

    # ---- routes ----
    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_code", sa.String(50), nullable=False),
        sa.Column("departure_city", sa.String(100), nullable=False),
        sa.Column("arrival_city", sa.String(100), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("route_code", name="uq_routes_code"),
    )
    op.create_index("ix_routes_operator_id", "routes", ["operator_id"])
    op.create_index("ix_routes_departure_city", "routes", ["departure_city"])
    op.create_index("ix_routes_arrival_city", "routes", ["arrival_city"])

    # ---- schedules ----
    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_id", sa.Integer(), sa.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("departure_time", sa.Time(), nullable=False),
        sa.Column("arrival_time", sa.Time(), nullable=False),
        sa.Column("base_fare", sa.Float(), nullable=False),
        sa.Column("total_seats", sa.Integer(), nullable=False),
        sa.Column("available_seats", sa.Integer(), nullable=False),
        sa.Column("status", schedule_status, nullable=False, server_default="SCHEDULED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "vehicle_id", "departure_date", "departure_time", name="uq_vehicle_departure"
        ),
    )
    op.create_index("ix_schedules_operator_id", "schedules", ["operator_id"])
    op.create_index("ix_schedules_route_id", "schedules", ["route_id"])
    op.create_index("ix_schedules_vehicle_id", "schedules", ["vehicle_id"])
    op.create_index("ix_schedules_departure_date", "schedules", ["departure_date"])
    op.create_index("ix_schedules_status", "schedules", ["status"])

    # ---- bookings (created before seats so seats can FK into it) ----
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_code", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("schedules.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("number_of_passengers", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("status", booking_status, nullable=False, server_default="PENDING"),
        sa.Column("payment_status", payment_status, nullable=False, server_default="PENDING"),
        sa.Column("contact_email", sa.String(255), nullable=False),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("booking_code", name="uq_bookings_code"),
    )
    op.create_index("ix_bookings_code", "bookings", ["booking_code"])
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_schedule_id", "bookings", ["schedule_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_payment_status", "bookings", ["payment_status"])

    # ---- seats ----
    op.create_table(
        "seats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seat_number", sa.String(10), nullable=False),
        sa.Column("seat_category", seat_category, nullable=False),
        sa.Column("status", seat_status, nullable=False, server_default="AVAILABLE"),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "locked_by_booking_id", sa.Integer(),
            sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
        ),
        sa.UniqueConstraint("schedule_id", "seat_number", name="uq_schedule_seat"),
    )
    op.create_index("ix_seats_schedule_id", "seats", ["schedule_id"])
    op.create_index("ix_seats_status", "seats", ["status"])

    # ---- booking_passengers ----
    op.create_table(
        "booking_passengers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seat_id", sa.Integer(), sa.ForeignKey("seats.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("id_type", sa.String(50), nullable=True),
        sa.Column("id_number", sa.String(50), nullable=True),
        sa.Column("seat_number", sa.String(10), nullable=False),
        sa.UniqueConstraint("booking_id", "seat_id", name="uq_booking_seat"),
    )
    op.create_index("ix_bp_booking_id", "booking_passengers", ["booking_id"])

    # ---- payments ----
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_reference", sa.String(100), nullable=False),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PKR"),
        sa.Column("provider", payment_provider, nullable=False),
        sa.Column("status", payment_record_status, nullable=False, server_default="PENDING"),
        sa.Column("external_transaction_id", sa.String(255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("payment_reference", name="uq_payments_reference"),
        sa.UniqueConstraint("booking_id", name="uq_payments_booking_id"),
    )
    op.create_index("ix_payments_reference", "payments", ["payment_reference"])
    op.create_index("ix_payments_status", "payments", ["status"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("booking_passengers")
    op.drop_table("seats")
    op.drop_table("bookings")
    op.drop_table("schedules")
    op.drop_table("routes")
    op.drop_table("vehicles")
    op.drop_table("operators")
    op.drop_table("refresh_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_table("users")

    bind = op.get_bind()
    for name in [
        "payment_provider", "payment_record_status", "payment_status", "booking_status",
        "seat_status", "seat_category", "schedule_status", "vehicle_type",
        "transport_type", "user_role",
    ]:
        sa.Enum(name=name).drop(bind, checkfirst=True)
