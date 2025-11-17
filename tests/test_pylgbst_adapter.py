from __future__ import annotations

import asyncio

from legotrains.hardware.pylgbst_adapter import PylgbstAdapter, _resolve_connection_target, PylgbstHubSession


class DummyMotor:
    def __init__(self) -> None:
        self.power_values: list[int] = []
        self.stopped = False

    def start_power(self, speed: int) -> None:
        self.power_values.append(speed)

    def stop(self) -> None:
        self.stopped = True


class DummyHub:
    def __init__(self, connection=None) -> None:
        self.connection = connection
        self.motor_A = DummyMotor()

    def disconnect(self) -> None:
        pass


def fake_connection_factory(*, hub_mac=None, hub_name=None):
    return object()


def test_resolve_connection_target() -> None:
    assert _resolve_connection_target("AA:BB")[0] == "AA:BB"
    assert _resolve_connection_target("Freight")[1] == "Freight"


def test_adapter_connects_with_dummy_hub() -> None:
    adapter = PylgbstAdapter(
        event_bus=None,
        connection_factory=fake_connection_factory,
        hub_cls=DummyHub,  # type: ignore[arg-type]
    )
    session = asyncio.run(adapter.connect("Freight"))  # type: ignore[arg-type]
    assert isinstance(session, PylgbstHubSession)
