from __future__ import annotations

from legotrains.control_input import CommandType, InputMapper, InputCommand, default_input_mapper


def test_default_mapper_has_expected_bindings() -> None:
    mapper = default_input_mapper()
    cmd = mapper.map_key("w", timestamp_ms=lambda: 1000)
    assert cmd == InputCommand(train_id="freight", command=CommandType.SPEED_STEP, value=5)


def test_mapper_debounce() -> None:
    mapper = InputMapper(bindings={"w": InputCommand(train_id="freight", command=CommandType.SPEED_STEP, value=5)}, debounce_ms=50)

    first = mapper.map_key("w", timestamp_ms=lambda: 1000)
    assert first is not None
    second = mapper.map_key("w", timestamp_ms=lambda: 1010)
    assert second is None
    third = mapper.map_key("w", timestamp_ms=lambda: 1100)
    assert third is not None
