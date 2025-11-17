from __future__ import annotations

import asyncio

from legotrains.runtime import build_runtime


def test_build_runtime_initializes_state_store(monkeypatch) -> None:
    runtime = build_runtime()
    snapshot = asyncio.run(runtime.state_store.snapshot())
    assert len(snapshot.trains) >= 1
