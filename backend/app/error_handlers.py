"""
Global exception handling.

Two concerns this addresses:
1. Unhandled exceptions must never leak stack traces or internal details
   to the client in production — that's an information-disclosure risk
   (reveals file paths, library versions, sometimes query fragments).
2. Domain exceptions raised by service layers (BookingNotFoundError,
   InvalidBookingStateError, etc.) that a route forgot to catch should
   still produce a sensible HTTP response instead of a raw 500.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.booking.exceptions import (
    BookingError,
    BookingNotFoundError,
    InvalidBookingStateError,
)
from app.config import settings

logger = logging.getLogger("app.errors")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BookingNotFoundError)
    async def booking_not_found_handler(request: Request, exc: BookingNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
        )

    @app.exception_handler(InvalidBookingStateError)
    async def invalid_booking_state_handler(
        request: Request, exc: InvalidBookingStateError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
        )

    @app.exception_handler(BookingError)
    async def booking_error_handler(request: Request, exc: BookingError):
        # Catch-all for any other domain booking error not specifically handled above.
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.method} {request.url.path}")

        # Never leak internals to the client, even in debug mode — if you
        # need the traceback, read the server logs. debug-mode frameworks
        # that echo tracebacks into HTTP responses are a common source of
        # accidental production information disclosure when DEBUG=true
        # gets left on by mistake.
        detail = (
            "An internal error occurred"
            if not settings.DEBUG
            else f"{type(exc).__name__}: {exc}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": detail},
        )
