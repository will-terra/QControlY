"""Descoberta de dispositivos QCY via BLE."""
from __future__ import annotations
import json
import logging
from pathlib import Path
from bleak import BleakScanner
from . import uuids
from ..core.model import DeviceInfo

log = logging.getLogger(__name__)

CACHE_FILE = Path.home() / ".qcy_h3_devices.json"


def get_cached_name(address: str) -> str | None:
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                return data.get(address)
    except Exception:
        pass
    return None


def save_cached_name(address: str, name: str) -> None:
    data = {}
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
    except Exception:
        pass
    data[address] = name
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


async def scan(timeout: float = 3.0) -> list[DeviceInfo]:
    """Escaneia e devolve dispositivos QCY, ordenados por RSSI (mais perto primeiro)."""
    results = await BleakScanner.discover(timeout=timeout, return_adv=True)
    found: list[DeviceInfo] = []
    for dev, adv in results.values():
        name = adv.local_name or dev.name or ""

        cached = get_cached_name(dev.address)
        if cached:
            name = cached

        if _is_qcy(name, adv.service_uuids) or cached:
            log.info("Dispositivo QCY encontrado: %s (%s)", name, dev.address)
            found.append(DeviceInfo(name=name or "QCY (?)", address=dev.address, rssi=adv.rssi))
    return sorted(found, key=lambda d: -(d.rssi if d.rssi is not None else -200))


def _is_qcy(name: str, service_uuids: list[str]) -> bool:
    if any(m in name.upper() for m in uuids.NAME_MATCH):
        return True

    valid_services = [
        uuids.QCY_SERVICE.lower(),
        "0000fee7-0000-1000-8000-00805f9b34fb",
        "0000fee8-0000-1000-8000-00805f9b34fb",
    ]
    return any(u.lower() in valid_services for u in service_uuids)
