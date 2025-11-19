"""Registry tracking known train hubs and their connectivity state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Mapping

from .config import TrainConfig
from .state import HubConnectionState, HubState, TrainState


@dataclass(frozen=True)
class RegisteredTrain:
    """Represents a configured train with runtime state."""

    config: TrainConfig
    state: TrainState


class HubRegistry:
    """In-memory registry for configured trains and their hub state."""

    def __init__(self, configs: Mapping[str, TrainConfig]) -> None:
        self._trains: dict[str, RegisteredTrain] = {}
        for identifier, cfg in configs.items():
            state = TrainState(identifier=cfg.identifier, name=cfg.name)
            self._trains[identifier] = RegisteredTrain(config=cfg, state=state)

    @classmethod
    def from_train_configs(cls, configs: tuple[TrainConfig, ...]) -> HubRegistry:
        return cls({cfg.identifier: cfg for cfg in configs})

    def __iter__(self) -> Iterator[RegisteredTrain]:
        return iter(self._trains.values())

    def train_states(self) -> tuple[TrainState, ...]:
        return tuple(entry.state for entry in self._trains.values())

    def get(self, identifier: str) -> RegisteredTrain:
        try:
            return self._trains[identifier]
        except KeyError as exc:
            raise KeyError(f"Train `{identifier}` is not registered.") from exc

    def find_by_mac(self, hub_mac: str) -> RegisteredTrain | None:
        hub_mac_upper = hub_mac.upper()
        for train in self._trains.values():
            if train.config.hub_mac and train.config.hub_mac.upper() == hub_mac_upper:
                return train
        return None

    def find_by_name(self, name: str | None) -> RegisteredTrain | None:
        if not name:
            return None
        name_lower = name.lower()
        for train in self._trains.values():
            if train.config.name.lower() == name_lower:
                return train
        return None

    def update_hub_state(
        self,
        identifier: str,
        *,
        connection_state: HubConnectionState | None = None,
        battery_level: float | None = None,
        rssi: float | None = None,
    ) -> HubState:
        registered = self.get(identifier)
        hub_state = registered.state.hub or HubState(identifier=identifier)
        if connection_state is not None:
            hub_state = HubState(
                identifier=hub_state.identifier,
                connection_state=connection_state,
                battery_level=battery_level if battery_level is not None else hub_state.battery_level,
                rssi=rssi if rssi is not None else hub_state.rssi,
            )
        else:
            hub_state = HubState(
                identifier=hub_state.identifier,
                connection_state=hub_state.connection_state,
                battery_level=battery_level if battery_level is not None else hub_state.battery_level,
                rssi=rssi if rssi is not None else hub_state.rssi,
            )

        updated_state = TrainState(
            identifier=registered.state.identifier,
            name=registered.state.name,
            speed=registered.state.speed,
            motion=registered.state.motion,
            hub=hub_state,
            active_program=registered.state.active_program,
        )
        self._trains[identifier] = RegisteredTrain(config=registered.config, state=updated_state)
        return hub_state

    def set_speed(self, identifier: str, speed: int) -> TrainState:
        registered = self.get(identifier)
        updated_state = TrainState(
            identifier=registered.state.identifier,
            name=registered.state.name,
            speed=speed,
            motion=registered.state.motion,
            hub=registered.state.hub,
            active_program=registered.state.active_program,
        )
        self._trains[identifier] = RegisteredTrain(config=registered.config, state=updated_state)
        return updated_state


__all__ = ["HubRegistry", "RegisteredTrain"]
