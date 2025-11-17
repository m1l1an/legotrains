"""Adapter wrapping pylgbst MoveHub connectivity."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Optional

from pylgbst import get_connection_auto
from pylgbst.hub import MoveHub
from pylgbst.peripherals import EncodedMotor

from ..state import Event, EventBus, EventSeverity
from ..hardware_connection import HubAdapter, HubSession


def _resolve_connection_target(target: str) -> tuple[Optional[str], Optional[str]]:
    if ":" in target:
        return target, None
    return None, target


@dataclass
class PylgbstHubSession(HubSession):
    hub: MoveHub
    event_bus: EventBus | None = None

    def __post_init__(self) -> None:
        self._motor: EncodedMotor | None = None
        self._lock = asyncio.Lock()

    async def _ensure_motor(self) -> EncodedMotor:
        if self._motor:
            return self._motor

        loop = asyncio.get_running_loop()

        def _load_motor() -> EncodedMotor:
            motor = self.hub.motor_A or self.hub.motor_B or self.hub.motor_external
            if not motor:
                raise RuntimeError("No motor found on MoveHub")
            return motor

        async with self._lock:
            if not self._motor:
                self._motor = await loop.run_in_executor(None, _load_motor)
                if self.event_bus:
                    await self.event_bus.publish(Event(type="hub_ready", message="Motor initialized"))
            return self._motor

    async def set_speed(self, speed: int) -> None:
        motor = await self._ensure_motor()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, motor.start_power, speed)

    async def stop(self) -> None:
        if not self._motor:
            return
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._motor.stop)

    async def close(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.hub.disconnect)


class PylgbstAdapter(HubAdapter):
    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        connection_factory: Callable[..., any] = get_connection_auto,
        hub_cls: type[MoveHub] = MoveHub,
    ) -> None:
        self._event_bus = event_bus
        self._connection_factory = connection_factory
        self._hub_cls = hub_cls

    async def connect(self, target: str) -> HubSession:
        hub_mac, hub_name = _resolve_connection_target(target)
        loop = asyncio.get_running_loop()

        def _connect() -> MoveHub:
            connection = self._connection_factory(hub_mac=hub_mac, hub_name=hub_name)
            return self._hub_cls(connection)

        hub = await loop.run_in_executor(None, _connect)
        return PylgbstHubSession(hub=hub, event_bus=self._event_bus)
