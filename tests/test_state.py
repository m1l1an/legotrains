from __future__ import annotations

import asyncio

from typing import Any, Coroutine, List, TypeVar

from legotrains.state import (
    AppState,
    Event,
    EventBus,
    EventSeverity,
    StateStore,
    TrainMotion,
    TrainState,
)


T = TypeVar("T")


def run(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


async def _collect(queue: asyncio.Queue[T], count: int) -> List[T]:
    results: List[T] = []
    for _ in range(count):
        results.append(await queue.get())
    return results


def test_state_store_upsert_and_subscribe() -> None:
    async def scenario() -> None:
        store = StateStore()
        queue = store.subscribe(maxsize=2)

        initial = await queue.get()
        assert initial.trains == ()

        train = TrainState(identifier="freight", name="Freight", speed=10, motion=TrainMotion.FORWARD)
        await store.upsert_trains([train])

        updated = await queue.get()
        assert updated.get_train("freight") == train

    run(scenario())


def test_state_store_update_train() -> None:
    async def scenario() -> None:
        store = StateStore(initial_state=AppState(trains=(TrainState(identifier="freight", name="Freight"),)))

        updated = await store.update_train("freight", speed=5, motion=TrainMotion.REVERSE)

        assert updated.speed == 5
        snapshot = await store.snapshot()
        assert snapshot.get_train("freight") == updated

    run(scenario())


def test_event_bus_publish_order() -> None:
    async def scenario() -> None:
        bus = EventBus()
        queue = bus.subscribe(maxsize=5)

        events = [
            Event(type="info", message="Ready"),
            Event(type="warn", message="Check hub", severity=EventSeverity.WARNING),
        ]
        for event in events:
            await bus.publish(event)

        received = await _collect(queue, len(events))
        assert received == events

    run(scenario())
