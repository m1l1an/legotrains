from __future__ import annotations

import sys
from pathlib import Path


def pytest_sessionstart(session) -> None:  # type: ignore[override]
    """Ensure src directory is on sys.path for tests."""

    root = Path(__file__).resolve().parents[1]
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
