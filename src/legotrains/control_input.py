"""Key input mapping utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping


class CommandType(Enum):
    """Semantic command types triggered by input."""

    SPEED_STEP = "speed_step"
    SPEED_MAX = "speed_max"
    SPEED_STOP = "speed_stop"


@dataclass(frozen=True)
class InputCommand:
    """Represents a command derived from user input."""

    train_id: str
    command: CommandType
    value: int | None = None


class InputMapper:
    """Maps keystrokes to domain commands."""

    def __init__(self, bindings: Mapping[str, InputCommand], *, debounce_ms: int = 100) -> None:
        self._bindings = dict(bindings)
        self._debounce_ms = debounce_ms
        self._last_seen: dict[str, float] = {}

    def map_key(self, key: str, timestamp_ms: Callable[[], float] | None = None) -> InputCommand | None:
        key_lower = key.lower()
        cmd = self._bindings.get(key) or self._bindings.get(key_lower)
        if not cmd:
            return None
        now = (timestamp_ms or (lambda: time.time() * 1000.0))()
        last = self._last_seen.get(key_lower, 0.0)
        if now - last < self._debounce_ms:
            return None
        self._last_seen[key_lower] = now
        return cmd


def default_input_mapper() -> InputMapper:
    bindings: dict[str, InputCommand] = {}
    bindings["w"] = InputCommand(train_id="freight", command=CommandType.SPEED_STEP, value=5)
    bindings["s"] = InputCommand(train_id="freight", command=CommandType.SPEED_STEP, value=-5)
    bindings["x"] = InputCommand(train_id="freight", command=CommandType.SPEED_STOP)
    bindings["i"] = InputCommand(train_id="passenger", command=CommandType.SPEED_STEP, value=5)
    bindings["k"] = InputCommand(train_id="passenger", command=CommandType.SPEED_STEP, value=-5)
    bindings[","] = InputCommand(train_id="passenger", command=CommandType.SPEED_STOP)

    bindings["W"] = InputCommand(train_id="freight", command=CommandType.SPEED_MAX, value=100)
    bindings["S"] = InputCommand(train_id="freight", command=CommandType.SPEED_MAX, value=-100)
    bindings["I"] = InputCommand(train_id="passenger", command=CommandType.SPEED_MAX, value=100)
    bindings["K"] = InputCommand(train_id="passenger", command=CommandType.SPEED_MAX, value=-100)
    return InputMapper(bindings=bindings)
