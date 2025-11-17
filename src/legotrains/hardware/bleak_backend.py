"""Bleak-based scanner backend."""

from __future__ import annotations

from typing import Iterable

try:
    from bleak import BleakScanner
except ImportError as exc:  # pragma: no cover - fallback when bleak missing
    raise RuntimeError("bleak is required for BLE scanning") from exc

from ..hardware_scanner import ScanResult, ScannerBackend


class BleakScannerBackend(ScannerBackend):
    def __init__(self, adapter: str | None = None) -> None:
        self._adapter = adapter

    async def scan(self) -> Iterable[ScanResult]:
        devices = await BleakScanner.discover(adapter=self._adapter)
        results: list[ScanResult] = []
        for device in devices:
            rssi = getattr(device, "rssi", None)
            if rssi is None:
                metadata = getattr(device, "metadata", {}) or {}
                rssi = metadata.get("RSSI")
            results.append(ScanResult(address=device.address, rssi=rssi))
        return results
