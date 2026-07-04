"""
Logging configuration.

Kept minimal and stdlib-only for the MVP — structured JSON logging,
correlation IDs, and shipping to an aggregator (ELK, CloudWatch, etc.)
are flagged as follow-up work once there's real traffic to justify the
operational complexity. Console output is sufficient for local dev and
for reading `docker-compose logs` during the first weeks of production.
"""

import logging
import sys

from app.config import settings


def configure_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # SQLAlchemy's engine logger is separately controlled by DATABASE_ECHO
    # (see app.database) — keep it quiet here regardless of LOG_LEVEL to
    # avoid drowning application logs in SQL statement noise.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
