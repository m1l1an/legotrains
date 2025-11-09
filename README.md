
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

## Installing Pre-requisites

pip install -r requirements.txt

## Technical Notes

We are using pylgbst ("Python Lego Boost") to connect to the Lego Powered Up hubs.

We need to install the latest from GitHub - the current version on PyPi does not support the latest Bleak library.
