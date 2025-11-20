"""Configuration loader for LegoTrains."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Final, Mapping, MutableMapping, Sequence
import os
import re

import yaml

DEFAULT_CONFIG_PATH: Final[Path] = Path.home() / ".legotrains.yaml"
CONFIG_ENV_VAR: Final[str] = "LEGOTRAINS_CONFIG_FILE"
TRAIN_MAC_ENV_PREFIX: Final[str] = "LEGOTRAINS_TRAIN_"
BLE_ADAPTER_ENV: Final[str] = "LEGOTRAINS_BLE_ADAPTER"
BLE_SCAN_INTERVAL_ENV: Final[str] = "LEGOTRAINS_BLE_SCAN_INTERVAL"
BLE_CONNECT_TIMEOUT_ENV: Final[str] = "LEGOTRAINS_BLE_CONNECT_TIMEOUT"
HARDWARE_ADAPTER_ENV: Final[str] = "LEGOTRAINS_HARDWARE_ADAPTER"

DEFAULT_SCAN_INTERVAL_SECONDS: Final[float] = 2.5
DEFAULT_CONNECT_TIMEOUT_SECONDS: Final[float] = 8.0

DEFAULT_TRAINS: Final[tuple[dict[str, str | None]], ...] = (
    {"id": "freight", "name": "FreightTrain", "hub_mac": None},
    {"id": "passenger", "name": "PassengerTrain", "hub_mac": None},
)

MAC_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9A-F]{2}(?::[0-9A-F]{2}){5}$", re.IGNORECASE)


class ConfigError(RuntimeError):
    """Raised when configuration cannot be parsed."""


@dataclass(frozen=True)
class TrainConfig:
    """Configuration describing a train and its hub."""

    identifier: str
    name: str
    hub_mac: str | None = None

    @property
    def match_identifier(self) -> str:
        """Prefer MAC for identification if present, otherwise fall back to name."""

        return self.hub_mac or self.name


@dataclass(frozen=True)
class BLEConfig:
    """Configuration for Bluetooth scanning and connections."""

    adapter: str | None
    scan_interval: float
    connect_timeout: float


@dataclass(frozen=True)
class AppConfig:
    """Top-level LegoTrains configuration."""

    trains: tuple[TrainConfig, ...]
    ble: BLEConfig
    log_level: str


def load_config(path: Path | None = None, env: Mapping[str, str] | None = None) -> AppConfig:
    """Load configuration from YAML and environment overrides."""

    env_map: MutableMapping[str, str] = dict(os.environ if env is None else env)
    config_path = _resolve_config_path(path, env_map)
    data = _load_yaml(config_path)

    trains = _parse_trains(data.get("trains"))
    trains = _apply_train_env_overrides(trains, env_map)

    ble = _parse_ble(data.get("ble"), env_map)
    log_level = (data.get("log_level") or env_map.get("LEGOTRAINS_LOG_LEVEL") or "INFO").upper()

    return AppConfig(trains=trains, ble=ble, log_level=log_level)


def _resolve_config_path(path_override: Path | None, env_map: Mapping[str, str]) -> Path:
    if path_override is not None:
        return path_override
    env_path = env_map.get(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path)
    return DEFAULT_CONFIG_PATH


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"Failed to parse YAML config at {path}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Configuration root must be a mapping.")
    return data


def _parse_trains(raw: Any) -> tuple[TrainConfig, ...]:
    source: Sequence[Any]
    if raw is None:
        source = DEFAULT_TRAINS
    elif isinstance(raw, Sequence):
        source = raw
    else:
        raise ConfigError("`trains` must be a sequence.")

    trains: list[TrainConfig] = []
    for entry in source:
        if not isinstance(entry, Mapping):
            raise ConfigError("Each train entry must be a mapping.")
        identifier = str(entry.get("id") or "").strip()
        name = str(entry.get("name") or "").strip()
        hub_mac_raw = entry.get("hub_mac")
        hub_mac = str(hub_mac_raw).strip() if hub_mac_raw is not None else ""
        if not identifier:
            raise ConfigError("Train entry missing `id`.")
        if not name:
            raise ConfigError(f"Train `{identifier}` missing `name`.")
        if hub_mac:
            if not _is_valid_mac(hub_mac):
                raise ConfigError(f"Train `{identifier}` has invalid hub_mac `{hub_mac}`.")
            mac_value: str | None = hub_mac.upper()
        else:
            mac_value = None
        trains.append(TrainConfig(identifier=identifier, name=name, hub_mac=mac_value))

    if not trains:
        raise ConfigError("At least one train must be configured.")

    return tuple(trains)


def _apply_train_env_overrides(
    trains: tuple[TrainConfig, ...],
    env_map: Mapping[str, str],
) -> tuple[TrainConfig, ...]:
    result: list[TrainConfig] = []
    for train in trains:
        key = f"{TRAIN_MAC_ENV_PREFIX}{train.identifier.upper()}_MAC"
        override = env_map.get(key)
        if override:
            mac = override.strip()
            if not _is_valid_mac(mac):
                raise ConfigError(f"Environment override `{key}` has invalid MAC `{mac}`.")
            result.append(replace(train, hub_mac=mac.upper()))
        else:
            result.append(train)
    return tuple(result)


def _parse_ble(raw: Any, env_map: Mapping[str, str]) -> BLEConfig:
    adapter = env_map.get(BLE_ADAPTER_ENV)
    scan_interval = _read_float(
        key=BLE_SCAN_INTERVAL_ENV,
        env_map=env_map,
        default=DEFAULT_SCAN_INTERVAL_SECONDS,
    )
    connect_timeout = _read_float(
        key=BLE_CONNECT_TIMEOUT_ENV,
        env_map=env_map,
        default=DEFAULT_CONNECT_TIMEOUT_SECONDS,
    )

    if isinstance(raw, Mapping):
        adapter = str(raw.get("adapter")) if raw.get("adapter") is not None else adapter
        scan_interval = _read_numeric_config(raw.get("scan_interval"), scan_interval, "scan_interval")
        connect_timeout = _read_numeric_config(raw.get("connect_timeout"), connect_timeout, "connect_timeout")

    if scan_interval <= 0:
        raise ConfigError("scan_interval must be greater than zero.")
    if connect_timeout <= 0:
        raise ConfigError("connect_timeout must be greater than zero.")

    return BLEConfig(
        adapter=(adapter or None),
        scan_interval=scan_interval,
        connect_timeout=connect_timeout,
    )


def _read_float(key: str, env_map: Mapping[str, str], default: float) -> float:
    raw = env_map.get(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"Environment variable `{key}` must be numeric.") from exc


def _read_numeric_config(value: Any, current: float, field_name: str) -> float:
    if value is None:
        return current
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"`ble.{field_name}` must be numeric.") from exc


def _is_valid_mac(value: str) -> bool:
    if not value:
        return False
    return bool(MAC_PATTERN.fullmatch(value))


__all__ = [
    "AppConfig",
    "BLEConfig",
    "TrainConfig",
    "ConfigError",
    "load_config",
    "DEFAULT_CONFIG_PATH",
]
