"""Structured logging and telemetry utilities."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Mapping

from .state import Event, EventBus, EventSeverity

LOG_PAYLOAD_FIELDS = ("train", "program", "hub")


@dataclass(slots=True)
class TelemetrySettings:
    """Settings controlling logging integration."""

    level: str = "INFO"


def configure_logging(
    settings: TelemetrySettings,
    event_bus: EventBus | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
) -> logging.Logger:
    """Configure application logging.

    Args:
        settings: Telemetry configuration (log level, filters).
        event_bus: Optional event bus to mirror log records into.
        loop: Event loop used for async publishing (defaults to asyncio.get_running_loop()).
    """

    logger = logging.getLogger("legotrains")
    logger.setLevel(settings.level.upper())
    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(stream_handler)
    if event_bus:
        logger.addHandler(EventBusHandler(event_bus=event_bus, loop=loop))
    return logger


class EventBusHandler(logging.Handler):
    """Logging handler that mirrors log records into the EventBus."""

    def __init__(self, event_bus: EventBus, loop: asyncio.AbstractEventLoop | None = None) -> None:
        super().__init__()
        self._bus = event_bus
        self._loop = loop

    def emit(self, record: logging.LogRecord) -> None:
        payload = _extract_payload(record)
        event = Event(
            type="log",
            message=self.format(record) if self.formatter else record.getMessage(),
            severity=_map_level(record.levelno),
            payload=payload,
        )
        loop = self._loop or _get_event_loop()
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self._bus.publish(event), loop)
        else:
            asyncio.run(self._bus.publish(event))


def _extract_payload(record: logging.LogRecord) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "logger": record.name,
        "level": record.levelname,
    }
    for field in LOG_PAYLOAD_FIELDS:
        if hasattr(record, field):
            payload[field] = getattr(record, field)
    if isinstance(record.args, Mapping):
        payload["args"] = dict(record.args)
    return payload


def _map_level(level_no: int) -> EventSeverity:
    if level_no >= logging.ERROR:
        return EventSeverity.ERROR
    if level_no >= logging.WARNING:
        return EventSeverity.WARNING
    return EventSeverity.INFO


def _get_event_loop() -> asyncio.AbstractEventLoop | None:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


__all__ = ["TelemetrySettings", "configure_logging", "EventBusHandler"]
