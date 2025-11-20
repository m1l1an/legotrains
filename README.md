
# LegoTrains

A text-UI (TUI) app to teach Python programming via controlling Lego Powered Up trains.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pip install pytest ruff black
```

## Running the App

Source code now lives under `src/`. To launch the placeholder Textual entrypoint (until the full UI lands), run:

```bash
python -m legotrains.main
```

You can also execute exploratory spikes in `experiments/`, e.g.:

```bash
python experiments/textual-test.py
```

## Testing & Code Quality

- **Unit tests** (required for every feature): `pytest`
- **Type coverage**: all modules must include type hints; prefer `from __future__ import annotations` and run `mypy` locally if available.
- **Pre-commit checks**:
  - `ruff check .`
  - `black --check .`
  - Or run both via `pre-commit run --all-files` once hooks are configured.

## Configuration

The app loads settings from `~/.legotrains.yaml`. Example:

```yaml
trains:
  - id: freight
    name: FreightTrain
    hub_mac: AA:BB:CC:DD:EE:FF
  - id: passenger
    name: PassengerTrain
ble:
  adapter: hci0
  scan_interval: 2.5
  connect_timeout: 8
log_level: DEBUG
```

Environment overrides:

- `LEGOTRAINS_CONFIG_FILE`: alternate YAML path
- `LEGOTRAINS_TRAIN_<ID>_MAC`: override MACs per train
- `LEGOTRAINS_BLE_SCAN_INTERVAL`, `LEGOTRAINS_BLE_CONNECT_TIMEOUT`, `LEGOTRAINS_BLE_ADAPTER`
- `LEGOTRAINS_LOG_LEVEL`: `DEBUG`, `INFO`, etc.

## Writing Custom Programs

1. Create a module under `src/legotrains/programs/` (or supply your own package) and subclass `TrainProgram`.
2. Decorate the class with `@register_program` and provide a `ProgramMetadata` name/description.
3. Implement `async def run(self)` and use helpers like `await self.set_speed("freight", 20)` and `await self.stop("freight")`.
4. Register additional modules via `discover_programs("legotrains.programs.examples.start_all")` or by loading an entire package at startup with `discover_programs_from_package("legotrains.programs.examples")`.
5. Example program: `Start All Trains` (see `src/legotrains/programs/examples/start_all.py`) sets both trains to 20% for 2 seconds, then stops them.

## Technical Notes

We are using pylgbst ("Python Lego Boost") to connect to the Lego Powered Up hubs.

We need to install the latest from GitHub - the current version on PyPi does not support the latest Bleak library.

## Links

- [Official Lego BLE Protocol Documentation](https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#document-index)
- Optional hardware prerequisites: install the OS-specific BLE stack and ensure `pylgbst` exposes `PoweredUPHub`; if unavailable, the app will fall back to logging only.

# AI Assisted Coding Notes

This application has largely been written by using OpenAI Codex. First, [[doc/PRD.md]] was hand-written, then Codex came up with [[doc/ai/DESIGN.md]] (which was a bit refined), then plan was created and put into [[doc/ai/PLAN.md]].

## Notes on Dev Experience

- looks nice, almost all unit tests pass at first shot
- but... it does not work.
- code is overcomplicated (eg, log levels not being used at all, never used constructor parameters - typical YAGNI)
- basic things need to be manually instructed (eg, start scanning for trains in the beginning, produce logs about it)
- the overall design and async workings are impressive though
- lot of errors still left in the code - Pylance shows them

## Main Prompts Used

```
read doc/PRD.md - setup up a directory and build structure that follows contemporary standards. Create an empty entrypoint (main?) python file.
```

```
make a detailed design doc and save it under doc/ai/DESIGN.md
```

```
create a detailed implementation plan in doc/ai/PLAN.md, breaking down the implementation into individual tasks. Unit tests are essential.
```

*From here on, we essentially had Codex implement the predefined tasks. Ran pytest and had it fix all errors.*