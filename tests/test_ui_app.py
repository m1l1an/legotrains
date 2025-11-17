from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import ListView

from types import SimpleNamespace
import asyncio

from legotrains.programs import ProgramMetadata, TrainProgram, register_program, load_program
from legotrains.state import HubConnectionState, HubState, TrainMotion, TrainState
from legotrains.ui.app import LegoTrainsApp


def test_panel_data_from_train_connected() -> None:
    train = TrainState(
        identifier="freight",
        name="Freight",
        speed=20,
        motion=TrainMotion.FORWARD,
        hub=HubState(identifier="freight", connection_state=HubConnectionState.CONNECTED),
    )
    data = LegoTrainsApp._panel_data_from_train(train)
    assert data.connection == "CONNECTED"
    assert data.status == "<Moving>"


def test_panel_data_from_train_stopped() -> None:
    train = TrainState(identifier="passenger", name="Passenger", speed=0)
    data = LegoTrainsApp._panel_data_from_train(train)
    assert data.status == "<Stopped>"
    assert data.connection == "DISCONNECTED"


class FakeProgram(TrainProgram):
    metadata = ProgramMetadata(name="FakeProgram")
    called = False

    async def run(self) -> None:
        FakeProgram.called = True


register_program(FakeProgram)


def test_run_program_invokes_registered_program() -> None:
    handler = SimpleNamespace(connections=None, event_bus=None)
    app = LegoTrainsApp(command_handler=handler)  # type: ignore[arg-type]

    asyncio.run(app._run_program("FakeProgram"))

    assert FakeProgram.called is True
