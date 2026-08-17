"""Logging configuration for the application."""

import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """Configure the root logger to emit structured logs to stdout."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
