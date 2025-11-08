# Repository Guidelines

## Project Structure & Module Organization
- `experiments/` holds runnable spikes such as `textual-test.py` and motor/BLE probes; promote stable prototypes into a future `src/` package before shipping.
- `doc/PRD.md` captures user goals—sync implementation notes there as features evolve.
- `sounds/` stores audio assets triggered by the TUI; keep filenames snake_case to align with Python module imports.
- `requirements.txt` pins runtime dependencies (`textual`, `pygame`, bleeding-edge `pylgbst`). Update it alongside any new modules you introduce.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates an isolated environment; always work inside it to keep Bleak versions consistent.
- `pip install -r requirements.txt` installs the TUI stack plus the GitHub version of `pylgbst` required for Powered Up hubs.
- `python experiments/textual-test.py` launches the sample data-table UI; replace the entry point with your module when validating new widgets.
- `PYTHONPATH=. python experiments/motortest.py --hub <mac>` is the quickest loop for confirming hub connectivity before integrating into the main app.

## Coding Style & Naming Conventions
- Target Python 3.11+, 4-space indentation, Black-compatible formatting, and type hints on public APIs.
- Modules and packages use `snake_case`; Textual widget classes stay `PascalCase`.
- Prefer pure functions or small service classes for hub control, keeping UI logic inside Textual views.
- Run `ruff check` (if installed) or `python -m compileall experiments` before committing to catch syntax issues.

## Testing Guidelines
- Use `pytest` for new automated tests; place them under `tests/` mirroring the package being exercised (`tests/test_motor_control.py`).
- Name fixtures after the hardware they stub (e.g., `powered_up_hub`); gate BLE-dependent tests behind `pytest -m "ble"` so CI can skip them.
- Until formal suites exist, document manual validation steps in PRs (commands, expected LED or motion patterns).

## Commit & Pull Request Guidelines
- Follow the repo’s concise history (`PRD added`, `Moved experiments to separate dir`); keep subjects under 60 characters and write in the imperative.
- Batch related changes per commit (docs, code, assets) and include context in the body when touching hardware-facing code.
- PRs should link issues, describe user-visible behavior, list test commands, and attach screenshots or terminal recordings for TUI changes.

## Hardware & Connectivity Tips
- Install the latest BLE stack for your OS before pairing hubs; flaky connections almost always trace back to outdated Bleak backends.
- Keep USB/BLE logs (`experiments/bleakscanner.py`) handy when debugging hub discovery—commit sanitized snippets so others can reproduce findings.
