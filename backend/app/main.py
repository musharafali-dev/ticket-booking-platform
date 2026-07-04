"""
FastAPI application entry point.

This is the only file that assembles routers into a running app — each
feature module (auth, search, booking, payment) stays independently
importable and testable, and this file's only job is composition.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import configure_logging
from app.error_handlers import register_exception_handlers
from app.database import engine
import app.models_registry  # noqa: F401 — ensures all models are registered before any table access

from app.auth.routes import router as auth_router
from app.search.routes import router as search_router
from app.booking.routes import router as booking_router
from app.payment.routes import router as payment_router

configure_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting up | environment={settings.ENVIRONMENT} | payment_provider={settings.PAYMENT_PROVIDER}"
    )
    yield
    logger.info("Shutting down")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ticket Booking Platform API",
        description="Bus, train, and airplane ticket booking across Pakistan",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "environment": settings.ENVIRONMENT}

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(booking_router, prefix="/api/v1/bookings", tags=["Bookings"])
    app.include_router(payment_router, prefix="/api/v1/payments", tags=["Payments"])

    return app


app = create_app()
