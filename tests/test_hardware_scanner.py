from __future__ import annotations

import asyncio
from typing import Iterable, List

from legotrains.config import TrainConfig
from legotrains.hardware_registry import HubRegistry
from legotrains.hardware_scanner import BleScannerService, ScanResult
from legotrains.state import EventBus


class FakeScannerBackend:
    def __init__(self, results: Iterable[ScanResult]) -> None:
        self.results = list(results)
        self.calls = 0

    async def scan(self) -> Iterable[ScanResult]:
        self.calls += 1
        return self.results


def run(coro):
    return asyncio.run(coro)


def test_scanner_publishes_events_for_known_macs() -> None:
    async def scenario() -> None:
        registry = HubRegistry.from_train_configs(
            (
                TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB:CC:01"),
            )
        )
        backend = FakeScannerBackend([ScanResult(address="aa:bb:cc:01", rssi=-40)])
        bus = EventBus()
        queue = bus.subscribe(maxsize=5)

        manager = FakeConnectionManager()
        scanner = BleScannerService(
            registry,
            backend,
            interval=0.1,
            event_bus=bus,
            loop=asyncio.get_running_loop(),
            connection_manager=manager,
        )
        await scanner._perform_scan()

        event = await queue.get()
        assert event.type == "hub_discovered"
        assert event.payload["train"] == "freight"
        assert manager.calls == [("aa:bb:cc:01", -40)]

    run(scenario())
class FakeConnectionManager:
    def __init__(self) -> None:
        self.calls: list[tuple[str, float | None]] = []

    async def handle_discovery(self, mac: str, *, rssi: float | None = None) -> None:
        self.calls.append((mac, rssi))
