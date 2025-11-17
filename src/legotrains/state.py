"""Application state management and event bus utilities."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Final, MutableMapping


class HubConnectionState(Enum):
    """Connection lifecycle state for a Powered Up hub."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()


class TrainMotion(Enum):
    """Direction of travel for a train."""

    STOPPED = auto()
    FORWARD = auto()
    REVERSE = auto()


class EventSeverity(Enum):
    """Severity level for published events."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass(frozen=True)
class HubState:
    """Runtime details for a hub connection."""

    identifier: str
    connection_state: HubConnectionState = HubConnectionState.DISCONNECTED
    battery_level: float | None = None
    rssi: float | None = None


@dataclass(frozen=True)
class TrainState:
    """Runtime snapshot for a train."""

    identifier: str
    name: str
    speed: int = 0
    motion: TrainMotion = TrainMotion.STOPPED
    hub: HubState | None = None
    active_program: str | None = None


@dataclass(frozen=True)
class AppState:
    """Immutable snapshot of the entire application state."""

    trains: tuple[TrainState, ...] = ()
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_train(self, identifier: str) -> TrainState | None:
        for train in self.trains:
            if train.identifier == identifier:
                return train
        return None


@dataclass(frozen=True)
class Event:
    """Domain event published to subscribers."""

    type: str
    message: str
    severity: EventSeverity = EventSeverity.INFO
    payload: MutableMapping[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """Async-safe publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[Event]] = set()
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe(self, *, maxsize: int = 100) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=maxsize)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Event]) -> None:
        self._subscribers.discard(queue)

    async def publish(self, event: Event) -> None:
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = None
        async with self._lock:
            dead: list[asyncio.Queue[Event]] = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    try:
                        queue.get_nowait()
                        queue.put_nowait(event)
                    except asyncio.QueueEmpty:
                        dead.append(queue)
            for queue in dead:
                self._subscribers.discard(queue)


class StateStore:
    """Concurrency-safe store for immutable AppState snapshots."""

    def __init__(self, initial_state: AppState | None = None) -> None:
        self._state = initial_state or AppState()
        self._lock = asyncio.Lock()
        self._subscribers: set[asyncio.Queue[AppState]] = set()

    async def snapshot(self) -> AppState:
        async with self._lock:
            return self._state

    async def upsert_trains(self, trains: Iterable[TrainState]) -> AppState:
        async with self._lock:
            current = {train.identifier: train for train in self._state.trains}
            for train in trains:
                current[train.identifier] = train
            self._state = AppState(trains=tuple(current.values()))
            new_state = self._state
        await self._broadcast(new_state)
        return new_state

    async def update_train(self, identifier: str, **changes: Any) -> TrainState:
        async with self._lock:
            train = self._find_train(identifier)
            updated_train = replace(train, **changes)
            trains = {
                t.identifier: (updated_train if t.identifier == identifier else t)
                for t in self._state.trains
            }
            self._state = AppState(trains=tuple(trains.values()))
            new_state = self._state
        await self._broadcast(new_state)
        return updated_train

    def subscribe(self, *, maxsize: int = 1) -> asyncio.Queue[AppState]:
        queue: asyncio.Queue[AppState] = asyncio.Queue(maxsize=maxsize)
        queue.put_nowait(self._state)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[AppState]) -> None:
        self._subscribers.discard(queue)

    def _find_train(self, identifier: str) -> TrainState:
        for train in self._state.trains:
            if train.identifier == identifier:
                return train
        raise KeyError(f"Train `{identifier}` not found in state store.")

    async def _broadcast(self, state: AppState) -> None:
        dead: list[asyncio.Queue[AppState]] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(state)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait(state)
                except asyncio.QueueEmpty:
                    dead.append(queue)
        for queue in dead:
            self._subscribers.discard(queue)


__all__ = [
    "AppState",
    "Event",
    "EventBus",
    "EventSeverity",
    "HubConnectionState",
    "HubState",
    "StateStore",
    "TrainMotion",
    "TrainState",
]
