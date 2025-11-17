"""Translate input commands into connection actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .control_input import CommandType, InputCommand
from .hardware_registry import HubRegistry
from .state import Event, EventBus, EventSeverity


def clamp_speed(value: int) -> int:
    return max(-100, min(100, value))


class ConnectionController(Protocol):
    async def set_speed(self, identifier: str, speed: int) -> None:
        ...

    async def stop(self, identifier: str) -> None:
        ...


@dataclass(slots=True)
class TrainCommandHandler:
    registry: HubRegistry
    connections: ConnectionController
    event_bus: EventBus | None = None

    async def handle(self, cmd: InputCommand) -> None:
        train = self.registry.get(cmd.train_id)
        current_speed = train.state.speed

        if cmd.command == CommandType.SPEED_STEP:
            delta = cmd.value or 0
            target = clamp_speed(current_speed + delta)
            if await self._try_set_speed(cmd.train_id, target):
                await self._log(f"{cmd.train_id} speed set to {target}")
        elif cmd.command == CommandType.SPEED_MAX:
            target = clamp_speed(cmd.value or 0)
            if await self._try_set_speed(cmd.train_id, target):
                await self._log(f"{cmd.train_id} max speed {target}")
        elif cmd.command == CommandType.SPEED_STOP:
            if await self._try_stop(cmd.train_id):
                await self._log(f"{cmd.train_id} stopped", severity=EventSeverity.INFO)
        else:
            raise ValueError(f"Unsupported command: {cmd.command}")

    async def _log(self, message: str, *, severity: EventSeverity = EventSeverity.INFO) -> None:
        if not self.event_bus:
            return
        await self.event_bus.publish(Event(type="command", message=message, severity=severity))

    async def _try_set_speed(self, train_id: str, speed: int) -> bool:
        try:
            await self.connections.set_speed(train_id, speed)
            return True
        except RuntimeError as exc:
            await self._log(str(exc), severity=EventSeverity.WARNING)
            return False

    async def _try_stop(self, train_id: str) -> bool:
        try:
            await self.connections.stop(train_id)
            return True
        except RuntimeError as exc:
            await self._log(str(exc), severity=EventSeverity.WARNING)
            return False
