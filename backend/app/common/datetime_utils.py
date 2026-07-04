"""
Shared datetime utilities.

_is_expired exists because of a real bug found during testing (see
app/auth/service.py history / tests/unit/test_auth_service.py): some DB
drivers (SQLite via aiosqlite, notably) silently return naive datetimes
even from columns declared DateTime(timezone=True), while Postgres does
not have this problem. Rather than duplicate this normalization in every
module that compares a DB-sourced datetime against "now" in Python code
(as opposed to inside a SQL WHERE clause, which the DB engine handles
natively and correctly either way), it lives here once.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(expires_at: datetime) -> bool:
    """True if expires_at is in the past, safe regardless of whether the
    DB driver returned a naive or timezone-aware datetime."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < utcnow()
