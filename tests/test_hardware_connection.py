from __future__ import annotations

import asyncio

import pytest

from typing import Iterable

from legotrains.config import TrainConfig
from legotrains.hardware_connection import HubConnectionManager, HubSession
from legotrains.hardware_registry import HubRegistry
from legotrains.state import AppState, EventBus, HubConnectionState, StateStore, TrainState


class FakeSession(HubSession):
    def __init__(self) -> None:
        self.speeds: list[int] = []
        self.stopped = False
        self.closed = False

    async def set_speed(self, speed: int) -> None:
        self.speeds.append(speed)

    async def stop(self) -> None:
        self.stopped = True

    async def close(self) -> None:
        self.closed = True


class FakeAdapter:
    def __init__(self) -> None:
        self.targets: list[str] = []
        self.session = FakeSession()
        self.should_fail = False

    async def connect(self, target: str) -> HubSession:
        self.targets.append(target)
        if self.should_fail:
            raise RuntimeError("boom")
        return self.session


def run(coro):
    return asyncio.run(coro)


def test_connect_invoked_updates_state() -> None:
    async def scenario() -> None:
        configs = (
            TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB:CC:01"),
        )
        registry = HubRegistry.from_train_configs(configs)
        adapter = FakeAdapter()
        bus = EventBus()
        queue = bus.subscribe(maxsize=10)
        state_store = FakeStateStore()
        manager = HubConnectionManager(
            registry,
            adapter,
            event_bus=bus,
            loop=asyncio.get_running_loop(),
            state_store=state_store,
        )

        await manager.connect("freight")

        assert adapter.targets == ["AA:BB:CC:01"]
        hub_state = registry.get("freight").state.hub
        assert hub_state is not None
        assert hub_state.connection_state == HubConnectionState.CONNECTED
        assert (await queue.get()).type == "hub_connecting"
        event = await queue.get()
        assert event.type == "hub_connected"
        assert any("freight" in update for update in state_store.updates)

    run(scenario())


def test_set_speed_requires_active_session() -> None:
    async def scenario() -> None:
        registry = HubRegistry.from_train_configs(
            (TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB:CC:01"),)
        )
        adapter = FakeAdapter()
        manager = HubConnectionManager(registry, adapter, loop=asyncio.get_running_loop())

        await manager.connect("freight")
        await manager.set_speed("freight", 40)
        assert adapter.session.speeds == [40]
        assert registry.get("freight").state.speed == 40

    run(scenario())


def test_connect_failure_updates_state_and_emits_event() -> None:
    async def scenario() -> None:
        registry = HubRegistry.from_train_configs(
            (TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB:CC:01"),)
        )
        adapter = FakeAdapter()
        adapter.should_fail = True
        bus = EventBus()
        queue = bus.subscribe(maxsize=10)
        manager = HubConnectionManager(registry, adapter, event_bus=bus, loop=asyncio.get_running_loop())

        with pytest.raises(RuntimeError):
            await manager.connect("freight")
        hub_state = registry.get("freight").state.hub
        assert hub_state is not None
        assert hub_state.connection_state == HubConnectionState.DISCONNECTED
        assert (await queue.get()).type == "hub_connecting"
        event = await queue.get()
        assert event.type == "hub_connect_failed"

    run(scenario())
class FakeStateStore(StateStore):
    def __init__(self) -> None:
        super().__init__(AppState(trains=()))
        self.updates: list[tuple[str, ...]] = []

    async def upsert_trains(self, trains: Iterable[TrainState]):
        await super().upsert_trains(trains)
        self.updates.append(tuple(state.identifier for state in trains))
