"""Centralized logging configuration."""

import logging

from rich.logging import RichHandler

from linux_doctor.config.settings import settings


def setup_logger(name: str) -> logging.Logger:
    """Configure and return a structured logger using Rich."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(settings.log_level)

        # Console handler with Rich formatting
        rich_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_path=False
        )

        formatter = logging.Formatter("%(message)s")
        rich_handler.setFormatter(formatter)
        logger.addHandler(rich_handler)

    return logger

log = setup_logger("linux_doctor")
