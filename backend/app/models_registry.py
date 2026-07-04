"""
Single import point for all ORM models.

SQLAlchemy's Base.metadata only knows about models that have been imported
somewhere in the process. Alembic's --autogenerate diffs against that
metadata, so a model that's never imported is invisible to migrations —
this file exists purely to guarantee every model gets imported once,
in one place, so that can't happen silently.
"""

from app.auth.models import User, EmailVerificationToken, RefreshToken  # noqa: F401
from app.operators.models import Operator, Vehicle, Route, Schedule, Seat  # noqa: F401
from app.booking.models import Booking, BookingPassenger  # noqa: F401
from app.payment.models import Payment  # noqa: F401
