"""Application entrypoint."""

from __future__ import annotations

import asyncio

from .programs import available_programs, discover_programs_from_package
from .runtime import build_runtime
from .ui.app import LegoTrainsApp


def main() -> None:
    """Launch the Textual UI."""

    discover_programs_from_package("legotrains.programs.examples")
    runtime = build_runtime()
    program_names = [meta.name for meta in available_programs()]
    app = LegoTrainsApp(
        state_store=runtime.state_store,
        program_names=program_names,
        command_handler=runtime.command_handler,
        input_mapper=runtime.input_mapper,
        event_bus=runtime.event_bus,
        scanner=runtime.scanner,
    )
    try:
        app.run()
    finally:
        if runtime.scanner:
            try:
                asyncio.run(runtime.scanner.stop())
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    main()
