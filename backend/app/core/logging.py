"""Structured Logging Configuration for Kollamo.ai Backend."""

import logging
import sys
import re
from typing import Any
try:
    from app.core.config import settings
except ImportError:
    from backend.app.core.config import settings

# Sensitive parameter patterns to sanitize from logs
SENSITIVE_PATTERNS = [
    re.compile(r"(key|secret|password|token)=([^&\s]+)", re.IGNORECASE),
    re.compile(r"(bearer\s+)([A-Za-z0-9_\-\.]+)", re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive tokens, passwords, and keys from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(r"\1=***REDACTED***", record.msg)
        return True


def setup_logging() -> logging.Logger:
    """Configures structured application logger."""
    logger = logging.getLogger("kollamo")
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
