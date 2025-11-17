"""BLE scanner service integrating with HubRegistry."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Protocol
import contextlib

from .hardware_registry import HubRegistry
from .state import Event, EventBus, EventSeverity

if TYPE_CHECKING:
    from .hardware_connection import HubConnectionManager


@dataclass(slots=True)
class ScanResult:
    """Represents a single BLE discovery result."""

    address: str
    rssi: float | None = None


class ScannerBackend(Protocol):
    """Protocol describing the BLE scanner dependency."""

    async def scan(self) -> Iterable[ScanResult]:
        ...


class BleScannerService:
    """Background scanner that looks for known hubs."""

    def __init__(
        self,
        registry: HubRegistry,
        backend: ScannerBackend,
        *,
        interval: float = 2.5,
        event_bus: EventBus | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
        connection_manager: "HubConnectionManager | None" = None,
    ) -> None:
        self._registry = registry
        self._backend = backend
        self._interval = interval
        self._event_bus = event_bus
        self._loop = loop
        self._connection_manager = connection_manager
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        loop = self._loop or asyncio.get_event_loop()
        if self._event_bus:
            loop.create_task(
                self._event_bus.publish(
                    Event(type="scanner_start", message="Scanning for hubs...", severity=EventSeverity.INFO)
                )
            )
        self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self._stop_event.set()

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            await self._perform_scan()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                continue

    async def _perform_scan(self) -> None:
        try:
            results = await self._backend.scan()
        except Exception as exc:  # pragma: no cover - defensive
            await self._publish_event(
                Event(type="scanner_error", message=str(exc), severity=EventSeverity.ERROR)
            )
            return

        for result in results:
            train = self._registry.find_by_mac(result.address)
            if not train:
                continue
            if self._connection_manager:
                await self._connection_manager.handle_discovery(result.address, rssi=result.rssi)
            await self._publish_event(
                Event(
                    type="hub_discovered",
                    message=f"Detected hub for {train.config.name}",
                    severity=EventSeverity.INFO,
                    payload={"train": train.state.identifier, "rssi": result.rssi},
                )
            )

    async def _publish_event(self, event: Event) -> None:
        if not self._event_bus:
            return
        loop = self._loop or asyncio.get_event_loop()
        if loop.is_running():
            await self._event_bus.publish(event)
        else:  # pragma: no cover - fallback
            asyncio.run(self._event_bus.publish(event))
