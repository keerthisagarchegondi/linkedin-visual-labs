"""Tests for structured JSON logging."""

from __future__ import annotations

import io
import json
import logging

from linkedin_visual_labs.common.logging import (
    configure_structured_logger,
)


def test_structured_logger_writes_json() -> None:
    stream = io.StringIO()

    logger = configure_structured_logger(
        "linkedin_visual_labs.test",
        stream=stream,
    )

    logger.info(
        "simulation complete",
        extra={
            "event": "simulation_complete",
            "project_id": "p01_bayesian_dice",
            "seed": 42,
        },
    )

    payload = json.loads(stream.getvalue())

    assert payload["level"] == "INFO"
    assert payload["logger"] == "linkedin_visual_labs.test"
    assert payload["message"] == "simulation complete"
    assert payload["event"] == "simulation_complete"
    assert payload["project_id"] == "p01_bayesian_dice"
    assert payload["seed"] == 42
    assert "timestamp" in payload


def test_configure_structured_logger_does_not_duplicate_handlers() -> None:
    first_stream = io.StringIO()
    second_stream = io.StringIO()

    logger = configure_structured_logger(
        "linkedin_visual_labs.duplicate_test",
        stream=first_stream,
    )

    logger = configure_structured_logger(
        "linkedin_visual_labs.duplicate_test",
        stream=second_stream,
    )

    logger.info("one event")

    assert first_stream.getvalue() == ""
    assert len(logger.handlers) == 1
    assert logger.level == logging.INFO
    assert second_stream.getvalue().count("\n") == 1
