"""
Centralized enums.

Using Python enums (backed by Postgres native ENUM types) instead of free-text
VARCHAR columns for status fields catches typos at write-time ("CONFRIMED")
instead of letting them silently corrupt queries at read-time.
"""

import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


class TransportType(str, enum.Enum):
    BUS = "BUS"
    TRAIN = "TRAIN"
    AIRPLANE = "AIRPLANE"


class SeatCategory(str, enum.Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"  # held during checkout, not yet paid
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"  # operator-side maintenance block


class ScheduleStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"  # created, awaiting payment
    CONFIRMED = "CONFIRMED"  # paid
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"  # payment window elapsed


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentProvider(str, enum.Enum):
    MOCK = "MOCK"
    JAZZCASH = "JAZZCASH"
    EASYPAISA = "EASYPAISA"
