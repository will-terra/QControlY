"""Modelo de domínio — usado pela UI; sem dependência de BLE ou bytes."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class AncMode(Enum):
    OFF = "desligado"
    ANC = "cancelamento"
    TRANSPARENCY = "transparência"


class EqPreset(Enum):
    DEFAULT = "padrão"
    POP = "pop"
    CLASSIC = "clássico"
    JAZZ = "jazz"
    ROCK = "rock"
    BASS = "grave"


@dataclass
class DeviceState:
    battery: int | None = None
    anc: AncMode | None = None
    eq: EqPreset | None = None


@dataclass(frozen=True)
class DeviceInfo:
    name: str
    address: str
    rssi: int | None = None
