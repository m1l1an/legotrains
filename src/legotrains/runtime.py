"""Runtime assembly for LegoTrains services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import AppConfig, TrainConfig, load_config
from .control_commands import TrainCommandHandler
from .control_input import InputMapper, default_input_mapper
from .hardware_connection import HubAdapter, HubConnectionManager
from .hardware_registry import HubRegistry
from .hardware_scanner import BleScannerService, ScannerBackend
from .hardware.bleak_backend import BleakScannerBackend
from .hardware.pylgbst_adapter import PylgbstAdapter
from .state import AppState, EventBus, StateStore, TrainState


@dataclass(slots=True)
class RuntimeContext:
    config: AppConfig
    event_bus: EventBus
    state_store: StateStore
    registry: HubRegistry
    connection_manager: HubConnectionManager
    command_handler: TrainCommandHandler
    input_mapper: InputMapper
    scanner: BleScannerService | None = None


class NullHubAdapter(HubAdapter):
    async def connect(self, target: str):
        raise RuntimeError("No hub adapter configured.")


def build_runtime(
    *,
    config_path: Path | None = None,
    adapter: HubAdapter | None = None,
    scanner_backend: ScannerBackend | None = None,
) -> RuntimeContext:
    config = load_config(config_path)
    registry = HubRegistry.from_train_configs(config.trains)
    state_store = StateStore(AppState(trains=registry.train_states()))
    event_bus = EventBus()
    connection_manager = HubConnectionManager(
        registry,
    adapter or PylgbstAdapter(event_bus=event_bus),
        event_bus=event_bus,
        state_store=state_store,
    )
    command_handler = TrainCommandHandler(registry=registry, connections=connection_manager, event_bus=event_bus)
    mapper = default_input_mapper()
    backend = scanner_backend
    scanner = None
    try:
        backend = backend or BleakScannerBackend(adapter=config.ble.adapter)
    except RuntimeError:
        backend = None
    if backend:
        scanner = BleScannerService(
            registry,
            backend,
            interval=config.ble.scan_interval,
            event_bus=event_bus,
            connection_manager=connection_manager,
        )

    return RuntimeContext(
        config=config,
        event_bus=event_bus,
        state_store=state_store,
        registry=registry,
        connection_manager=connection_manager,
        command_handler=command_handler,
        input_mapper=mapper,
        scanner=scanner,
    )
