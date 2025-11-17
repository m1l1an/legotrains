from __future__ import annotations

import asyncio

from legotrains.config import TrainConfig
from legotrains.control_commands import TrainCommandHandler, clamp_speed
from legotrains.control_input import CommandType, InputCommand
from legotrains.hardware_connection import HubConnectionManager
from legotrains.hardware_registry import HubRegistry


class FakeConnections:
    def __init__(self) -> None:
        self.speed_calls: list[tuple[str, int]] = []
        self.stop_calls: list[str] = []

    async def set_speed(self, identifier: str, speed: int) -> None:
        self.speed_calls.append((identifier, speed))

    async def stop(self, identifier: str) -> None:
        self.stop_calls.append(identifier)


class AdapterBacking:
    async def connect(self, target: str):
        raise NotImplementedError


def run(coro):
    return asyncio.run(coro)


def test_clamp_speed() -> None:
    assert clamp_speed(200) == 100
    assert clamp_speed(-200) == -100
    assert clamp_speed(50) == 50


def test_speed_step_command_updates_speed(monkeypatch) -> None:
    async def scenario() -> None:
        registry = HubRegistry.from_train_configs(
            (
                TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB"),
            )
        )
        fake_connections = FakeConnections()
        handler = TrainCommandHandler(registry=registry, connections=fake_connections)  # type: ignore[arg-type]
        await handler.handle(InputCommand(train_id="freight", command=CommandType.SPEED_STEP, value=10))
        assert fake_connections.speed_calls == [("freight", 10)]

    run(scenario())


def test_stop_command_calls_stop(monkeypatch) -> None:
    async def scenario() -> None:
        registry = HubRegistry.from_train_configs(
            (
                TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB"),
            )
        )
        fake_connections = FakeConnections()
        handler = TrainCommandHandler(registry=registry, connections=fake_connections)  # type: ignore[arg-type]
        await handler.handle(InputCommand(train_id="freight", command=CommandType.SPEED_STOP))
        assert fake_connections.stop_calls == ["freight"]

    run(scenario())
