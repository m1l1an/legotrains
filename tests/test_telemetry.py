from __future__ import annotations

import asyncio
import logging

from legotrains.state import EventSeverity, EventBus
from legotrains.telemetry import TelemetrySettings, configure_logging


def run(coro):
    return asyncio.run(coro)


def teardown_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_logging_publishes_events() -> None:
    async def scenario() -> None:
        bus = EventBus()
        queue = bus.subscribe(maxsize=5)
        loop = asyncio.get_running_loop()

        logger = configure_logging(TelemetrySettings(level="INFO"), event_bus=bus, loop=loop)
        logger.info("Train ready", extra={"train": "freight"})

        event = await queue.get()
        assert event.type == "log"
        assert event.severity == EventSeverity.INFO
        assert event.payload["train"] == "freight"
        teardown_logger(logger)

    run(scenario())


def test_logging_warning_maps_to_severity_warning() -> None:
    async def scenario() -> None:
        bus = EventBus()
        queue = bus.subscribe(maxsize=5)
        loop = asyncio.get_running_loop()

        logger = configure_logging(TelemetrySettings(level="INFO"), event_bus=bus, loop=loop)
        logger.warning("Battery low")

        event = await queue.get()
        assert event.severity == EventSeverity.WARNING
        teardown_logger(logger)

    run(scenario())
