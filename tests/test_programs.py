from __future__ import annotations

import asyncio

import pytest

from legotrains.programs import (
    ProgramMetadata,
    TrainProgram,
    available_programs,
    discover_programs,
    load_program,
    register_program,
)


class FakeConnections:
    def __init__(self) -> None:
        self.speeds: list[tuple[str, int]] = []
        self.stopped: list[str] = []

    async def set_speed(self, train_id: str, speed: int) -> None:
        self.speeds.append((train_id, speed))

    async def stop(self, train_id: str) -> None:
        self.stopped.append(train_id)


def run(coro):
    return asyncio.run(coro)


@register_program
class DemoProgram(TrainProgram):
    metadata = ProgramMetadata(name="Demo", description="Test program")

    async def run(self) -> None:
        await self.set_speed("freight", 10)
        await self.stop("freight")


def test_program_registration_and_execution() -> None:
    async def scenario() -> None:
        connections = FakeConnections()
        program = load_program("Demo", connections)

        await program.run()

        assert connections.speeds == [("freight", 10)]
        assert connections.stopped == ["freight"]

    run(scenario())


def test_missing_metadata_raises() -> None:
    class InvalidProgram(TrainProgram):
        async def run(self) -> None:
            pass

    with pytest.raises(ValueError):
        register_program(InvalidProgram)


def test_discover_programs(monkeypatch) -> None:
    calls: list[str] = []

    def fake_import(module: str) -> None:
        calls.append(module)

    monkeypatch.setattr("legotrains.programs.import_module", lambda module: fake_import(module))
    discover_programs("programs.one", "programs.two")
    assert calls == ["programs.one", "programs.two"]
