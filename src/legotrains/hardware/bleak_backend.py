"""Bleak-based scanner backend."""

from __future__ import annotations

from bleak import BleakScanner
from typing import Iterable

from ..hardware_scanner import ScanResult, ScannerBackend


class BleakScannerBackend(ScannerBackend):
    def __init__(self, adapter: str | None = None) -> None:
        self._adapter = adapter

    async def scan(self) -> Iterable[ScanResult]:
        devices = await BleakScanner.discover(adapter=self._adapter)
        return [
            ScanResult(
                address=device.address,
                name=getattr(device, "name", None),
            )
            for device in devices
        ]
