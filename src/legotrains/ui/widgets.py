"""Reusable UI widgets for the LegoTrains TUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rich.panel import Panel
from rich.table import Table
from textual.widgets import Label, ListItem, ListView, Static


@dataclass(slots=True)
class TrainPanelData:
    name: str
    status: str
    speed: int
    connection: str


class TrainPanel(Static):
    """Displays the status of a single train."""

    DEFAULT_CSS = """
    TrainPanel {
        height: 100%;
        border: solid gray;
        padding: 1;
        content-align: center middle;
    }
    """

    def __init__(self, data: TrainPanelData, id: str | None = None) -> None:
        super().__init__(id=id)
        self._data = data

    def update_data(self, data: TrainPanelData) -> None:
        self._data = data
        self.refresh()

    def render(self) -> Panel:
        table = Table.grid(padding=(0, 1))
        table.add_row(f"[b]{self._data.status}[/b]")
        table.add_row(f"Speed: [cyan]{self._data.speed}[/cyan]")
        table.add_row(f"[dim]{self._data.connection}[/dim]")
        return Panel(table, title=f"{self._data.name}")


class ProgramList(ListView):
    """Selectable list of programs."""

    DEFAULT_CSS = """
    ProgramList {
        border: solid gray;
        width: 1fr;
    }
    """

    def __init__(self, programs: Iterable[str]) -> None:
        items = [ListItem(Label(name)) for name in programs]
        super().__init__(*items)
        self._programs = list(programs)

    def update_programs(self, programs: Iterable[str]) -> None:
        self._programs = list(programs)
        self.clear()
        for name in self._programs:
            self.append(ListItem(Label(name)))

LOG_LINES_DISPLAYED = 9


class LogPanel(Static):
    """Log panel with fixed height derived from LOG_LINES_DISPLAYED."""

    DEFAULT_CSS = f"""
    LogPanel {{
        height: {LOG_LINES_DISPLAYED};
        border: solid gray;
        padding: 1;
    }}
    """

    def __init__(self, max_entries: int = LOG_LINES_DISPLAYED) -> None:
        super().__init__()
        self._entries: list[str] = []
        self._max_entries = max_entries

    def add_entry(self, message: str) -> None:
        self._entries.append(message)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        self.refresh()

    def render(self) -> Panel:
        table = Table.grid()
        if not self._entries:
            table.add_row("[dim]Log messages appear here...[/dim]")
        else:
            for entry in self._entries[-self._max_entries :]:
                table.add_row(entry)
        return Panel(table, title="Log")
