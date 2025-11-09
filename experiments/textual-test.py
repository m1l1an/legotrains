#!/usr/bin/env python3
# (C) 2025, Richard G. Roman <rits@rits.hu>
# Created on 2025-11-05 21:13:11
""" """

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, DataTable


class EmojiDemo(App):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        table = DataTable()
        table.add_columns("🐋 Pod", "💚 Status", "⚙️ CPU", "💾 Memory")
        table.add_rows(
            [
                ("nginx-1", "✅ Running", "12m", "128Mi"),
                ("redis-2", "🕒 Pending", "0m", "0Mi"),
            ]
        )
        yield table
        yield Label("Press Q to quit 😎")
        yield Footer()


if __name__ == "__main__":
    EmojiDemo().run()
