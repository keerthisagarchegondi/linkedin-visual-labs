"""Structured logging for reproducible project pipelines."""

from __future__ import annotations

import json
import logging as std_logging
from datetime import UTC, datetime
from typing import TextIO

STANDARD_LOG_RECORD_ATTRIBUTES = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonFormatter(std_logging.Formatter):
    """Format log records as one JSON object per line."""

    def format(self, record: std_logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in STANDARD_LOG_RECORD_ATTRIBUTES and not key.startswith("_"):
                payload[key] = value

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            sort_keys=True,
            default=str,
        )


def configure_structured_logger(
    name: str,
    *,
    level: int = std_logging.INFO,
    stream: TextIO | None = None,
) -> std_logging.Logger:
    """Create or reset a logger using deterministic JSON structure."""
    logger = std_logging.getLogger(name)

    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    handler = std_logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)

    return logger
