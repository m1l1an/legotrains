"""Textual application shell for LegoTrains."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
import contextlib

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.events import Key
from textual.widgets import Footer, Header, ListView

from ..config import DEFAULT_TRAINS
from ..control_commands import TrainCommandHandler
from ..control_input import InputMapper
from ..programs import load_program
from ..state import AppState, Event, EventBus, StateStore, TrainMotion, TrainState
from ..hardware_scanner import BleScannerService
from .widgets import LogPanel, ProgramList, TrainPanel, TrainPanelData


class LegoTrainsApp(App[None]):
    """High-level TUI composition."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main-panels {
        layout: horizontal;
        height: 1fr;
        min-height: 20;
    }
    TrainPanel, ProgramList {
        width: 1fr;
    }
    LogPanel {
        height: 9;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(
        self,
        *,
        state_store: StateStore | None = None,
        program_names: Sequence[str] | None = None,
        command_handler: TrainCommandHandler | None = None,
        input_mapper: InputMapper | None = None,
        event_bus: EventBus | None = None,
        scanner: BleScannerService | None = None,
    ) -> None:
        super().__init__()
        self._state_store = state_store or self._build_default_state_store()
        self._program_names = list(program_names or [])
        self._state_task: asyncio.Task[None] | None = None
        self._state_queue: asyncio.Queue[AppState] | None = None
        self._command_handler = command_handler
        self._input_mapper = input_mapper
        self._event_bus = event_bus
        self._scanner = scanner
        self._event_queue: asyncio.Queue[Event] | None = None
        self._event_task: asyncio.Task[None] | None = None
        self._log_panel: LogPanel

    def compose(self) -> ComposeResult:
        self._passenger_panel = TrainPanel(
            TrainPanelData(
                name="PassengerTrain",
                status="<Stopped>",
                speed=0,
                connection="DISCONNECTED",
            ),
            id="passenger-panel",
        )
        self._freight_panel = TrainPanel(
            TrainPanelData(
                name="FreightTrain",
                status="<Stopped>",
                speed=0,
                connection="DISCONNECTED",
            ),
            id="freight-panel",
        )
        self._program_list = ProgramList(programs=self._program_names)
        self._panels = {
            "passenger": self._passenger_panel,
            "freight": self._freight_panel,
        }

        yield Header(show_clock=True)
        yield Container(
            self._passenger_panel,
            self._program_list,
            self._freight_panel,
            id="main-panels",
        )
        self._log_panel = LogPanel()
        yield self._log_panel
        yield Footer()

    async def on_key(self, event: Key) -> None:
        if self._input_mapper and self._command_handler:
            if event.character:
                command = self._input_mapper.map_key(event.character)
                if command:
                    await self._command_handler.handle(command)
                    return
        if event.key == "q":
            await self.action_quit()

    async def on_list_view_selected(self, message: ListView.Selected) -> None:
        if not self._command_handler:
            return
        if message.index >= len(self._program_names):
            return
        program_name = self._program_names[message.index]
        await self._run_program(program_name)

    async def _run_program(self, name: str) -> None:
        if not self._command_handler:
            return
        program = load_program(name, self._command_handler.connections, self._command_handler.event_bus)
        await program.run()

    async def on_mount(self) -> None:
        self._state_queue = self._state_store.subscribe(maxsize=5)
        loop = asyncio.get_running_loop()
        self._state_task = loop.create_task(self._watch_state())
        if self._event_bus:
            self._event_queue = self._event_bus.subscribe(maxsize=20)
            self._event_task = loop.create_task(self._watch_events())
        if self._scanner:
            self._scanner.start()

    async def on_unmount(self) -> None:
        if self._scanner:
            await self._scanner.stop()
        if self._state_task:
            self._state_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._state_task
            self._state_task = None
        if self._event_task:
            self._event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._event_task
            self._event_task = None

    async def _watch_state(self) -> None:
        if not self._state_queue:
            return
        while True:
            state = await self._state_queue.get()
            self._apply_state(state)

    async def _watch_events(self) -> None:
        if not self._event_queue:
            return
        while True:
            event = await self._event_queue.get()
            self._log_panel.add_entry(event.message)

    def _apply_state(self, state: AppState) -> None:
        for train in state.trains:
            panel = self._panels.get(train.identifier)
            if panel:
                panel.update_data(self._panel_data_from_train(train))
        self._program_list.update_programs(self._program_names)

    @staticmethod
    def _panel_data_from_train(train: TrainState) -> TrainPanelData:
        status = "<Moving>" if train.speed != 0 or train.motion != TrainMotion.STOPPED else "<Stopped>"
        connection = "DISCONNECTED"
        if train.hub:
            connection = train.hub.connection_state.name
        return TrainPanelData(
            name=train.name,
            status=status,
            speed=train.speed,
            connection=connection,
        )

    @staticmethod
    def _build_default_state_store() -> StateStore:
        trains = tuple(
            TrainState(
                identifier=cfg["id"],
                name=cfg["name"],
            )
            for cfg in DEFAULT_TRAINS
        )
        return StateStore(AppState(trains=trains))
