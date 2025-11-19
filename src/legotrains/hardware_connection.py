"""Connection manager for Powered Up hubs."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Protocol

from .hardware_registry import HubRegistry
from .state import Event, EventBus, EventSeverity, HubConnectionState, StateStore


class HubSession(Protocol):
    """Protocol representing an active hub session."""

    async def set_speed(self, speed: int) -> None: ...

    async def stop(self) -> None: ...

    async def close(self) -> None: ...


class HubAdapter(Protocol):
    """Protocol for creating hub sessions."""

    async def connect(self, target: str) -> HubSession: ...


@dataclass
class _ConnectionRecord:
    identifier: str
    session: HubSession | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class HubConnectionManager:
    """Coordinates BLE connections and exposes high-level commands."""

    def __init__(
        self,
        registry: HubRegistry,
        adapter: HubAdapter,
        *,
        event_bus: EventBus | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
        state_store: StateStore | None = None,
    ) -> None:
        self._registry = registry
        self._adapter = adapter
        self._connections: dict[str, _ConnectionRecord] = {
            train.config.identifier: _ConnectionRecord(identifier=train.config.identifier)
            for train in registry
        }
        self._event_bus = event_bus
        self._loop = loop
        self._state_store = state_store

    async def handle_discovery(self, identifier: str) -> None:
        await self.connect(identifier)

    async def connect(self, identifier: str, *, rssi: float | None = None) -> None:
        record = self._connections[identifier]
        async with record.lock:
            if record.session:
                return
            train = self._registry.get(identifier)
            target = train.config.match_identifier
            await self._update_state(identifier, HubConnectionState.CONNECTING, rssi=rssi)
            await self._publish_event(
                Event(
                    type="hub_connecting",
                    message=f"Connecting to {identifier}",
                    severity=EventSeverity.INFO,
                    payload={"train": identifier},
                )
            )
            try:
                session = await self._adapter.connect(target)
            except Exception as exc:
                await self._update_state(identifier, HubConnectionState.DISCONNECTED, rssi=rssi)
                await self._publish_event(
                    Event(
                        type="hub_connect_failed",
                        message=f"Failed to connect {identifier}: {exc}",
                        severity=EventSeverity.ERROR,
                        payload={"train": identifier},
                    )
                )
                raise
            record.session = session
            await self._update_state(identifier, HubConnectionState.CONNECTED, rssi=rssi)
            await self._publish_event(
                Event(
                    type="hub_connected",
                    message=f"Connected to {identifier}",
                    severity=EventSeverity.INFO,
                    payload={"train": identifier},
                )
            )

    async def disconnect(self, identifier: str) -> None:
        record = self._connections[identifier]
        async with record.lock:
            if not record.session:
                return
            await record.session.close()
            record.session = None
            await self._update_state(identifier, HubConnectionState.DISCONNECTED)
            await self._publish_event(
                Event(
                    type="hub_disconnected",
                    message=f"Disconnected {identifier}",
                    severity=EventSeverity.WARNING,
                    payload={"train": identifier},
                )
            )

    async def set_speed(self, identifier: str, speed: int) -> None:
        session = await self._require_session(identifier)
        await session.set_speed(speed)
        self._registry.set_speed(identifier, speed)
        await self._sync_state_store()

    async def stop(self, identifier: str) -> None:
        session = await self._require_session(identifier)
        await session.stop()
        self._registry.set_speed(identifier, 0)
        await self._sync_state_store()

    async def shutdown(self) -> None:
        for identifier in list(self._connections):
            await self.disconnect(identifier)

    async def _require_session(self, identifier: str) -> HubSession:
        record = self._connections[identifier]
        if not record.session:
            raise RuntimeError(f"No active session for {identifier}")
        return record.session

    async def _update_state(
        self,
        identifier: str,
        connection_state: HubConnectionState,
        *,
        rssi: float | None = None,
    ) -> None:
        self._registry.update_hub_state(identifier, connection_state=connection_state, rssi=rssi)
        await self._sync_state_store()

    async def _publish_event(self, event: Event) -> None:
        if not self._event_bus:
            return
        loop = self._loop or asyncio.get_event_loop()
        if loop.is_running():
            await self._event_bus.publish(event)
        else:  # pragma: no cover
            asyncio.run(self._event_bus.publish(event))

    async def _sync_state_store(self) -> None:
        if not self._state_store:
            return
        await self._state_store.upsert_trains(self._registry.train_states())
