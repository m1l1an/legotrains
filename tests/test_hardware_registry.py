from __future__ import annotations

from legotrains.config import TrainConfig
from legotrains.hardware_registry import HubRegistry
from legotrains.state import HubConnectionState


def test_registry_initializes_trains() -> None:
    configs = (
        TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB:CC:00:00:01"),
        TrainConfig(identifier="passenger", name="Passenger"),
    )
    registry = HubRegistry.from_train_configs(configs)

    registered = list(registry)
    assert len(registered) == 2
    assert registered[0].config == configs[0]
    assert registered[0].state.identifier == "freight"


def test_find_by_mac_matches_only_when_present() -> None:
    configs = (
        TrainConfig(identifier="freight", name="Freight", hub_mac="AA:BB:CC:00:00:01"),
    )
    registry = HubRegistry.from_train_configs(configs)

    match = registry.find_by_mac("aa:bb:cc:00:00:01")
    assert match is not None
    assert match.config.identifier == "freight"
    assert registry.find_by_mac("aa:bb") is None


def test_find_by_name_matches_case_insensitive() -> None:
    registry = HubRegistry.from_train_configs(
        (TrainConfig(identifier="freight", name="FreightTrain", hub_mac=None),)
    )
    match = registry.find_by_name("freighttrain")
    assert match is not None
    assert match.config.identifier == "freight"


def test_update_hub_state_sets_connection_details() -> None:
    registry = HubRegistry.from_train_configs(
        (
            TrainConfig(identifier="freight", name="Freight", hub_mac=None),
        )
    )

    hub_state = registry.update_hub_state(
        "freight",
        connection_state=HubConnectionState.CONNECTED,
        battery_level=90.0,
    )

    assert hub_state.connection_state == HubConnectionState.CONNECTED
    assert hub_state.battery_level == 90.0
    assert registry.get("freight").state.hub == hub_state


def test_train_states_snapshot() -> None:
    configs = (
        TrainConfig(identifier="freight", name="Freight", hub_mac=None),
        TrainConfig(identifier="passenger", name="Passenger", hub_mac=None),
    )
    registry = HubRegistry.from_train_configs(configs)
    states = registry.train_states()
    assert len(states) == 2
    assert {state.identifier for state in states} == {"freight", "passenger"}
