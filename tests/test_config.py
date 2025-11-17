from __future__ import annotations

from pathlib import Path

import pytest

from legotrains.config import AppConfig, BLEConfig, ConfigError, TrainConfig, load_config


def test_load_config_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(path=tmp_path / "missing.yaml", env={})

    assert isinstance(config, AppConfig)
    assert len(config.trains) == 2
    assert all(isinstance(train, TrainConfig) for train in config.trains)
    assert config.ble == BLEConfig(adapter=None, scan_interval=2.5, connect_timeout=8.0)


def test_load_config_from_yaml(tmp_path: Path) -> None:
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
        trains:
          - id: freight
            name: Freight Runner
            hub_mac: AA:BB:CC:DD:EE:01
        ble:
          adapter: hci1
          scan_interval: 5
          connect_timeout: 12
        log_level: debug
        """,
        encoding="utf-8",
    )

    config = load_config(path=yaml_path, env={})

    assert config.trains == (
        TrainConfig(identifier="freight", name="Freight Runner", hub_mac="AA:BB:CC:DD:EE:01"),
    )
    assert config.ble == BLEConfig(adapter="hci1", scan_interval=5.0, connect_timeout=12.0)
    assert config.log_level == "DEBUG"


def test_env_overrides_train_mac_and_ble(tmp_path: Path) -> None:
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
        trains:
          - id: freight
            name: Freight
            hub_mac: AA:BB:CC:DD:EE:01
        """,
        encoding="utf-8",
    )

    env = {
        "LEGOTRAINS_TRAIN_FREIGHT_MAC": "AA:BB:CC:DD:EE:FF",
        "LEGOTRAINS_BLE_SCAN_INTERVAL": "3.5",
        "LEGOTRAINS_BLE_ADAPTER": "hci2",
    }

    config = load_config(path=yaml_path, env=env)

    assert config.trains[0].hub_mac == "AA:BB:CC:DD:EE:FF"
    assert config.trains[0].match_identifier == "AA:BB:CC:DD:EE:FF"
    assert config.ble.scan_interval == 3.5
    assert config.ble.adapter == "hci2"


def test_invalid_mac_in_yaml_raises(tmp_path: Path) -> None:
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
        trains:
          - id: freight
            name: Freight
            hub_mac: INVALID
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(path=yaml_path, env={})


def test_mac_is_optional_and_defaults_to_name(tmp_path: Path) -> None:
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
        trains:
          - id: passenger
            name: Passenger
        """,
        encoding="utf-8",
    )

    config = load_config(path=yaml_path, env={})

    assert config.trains[0].hub_mac is None
    assert config.trains[0].match_identifier == "Passenger"
