from __future__ import annotations

from textual.widgets import ListItem

from legotrains.ui.widgets import ProgramList, TrainPanel, TrainPanelData


def test_train_panel_renders_title() -> None:
    panel = TrainPanel(TrainPanelData(name="FreightTrain", status="<Moving>", speed=10, connection="CONNECTED"))
    rendered = panel.render()
    assert rendered.title == "FreightTrain"


def test_program_list_handles_empty() -> None:
    widget = ProgramList(programs=[])
    assert len(widget.children) == 0
