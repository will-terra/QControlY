"""Tabela de comandos do protocolo BLE proprietário dos fones QCY H3 / H3 Pro / H3S.

Opcodes e payloads confirmados via captura btsnoop_hci.log (Wireshark).
"""
from __future__ import annotations
from .model import AncMode, DeviceState, EqPreset
from .protocol import Frame


class Cmd:
    REQUEST = 0xFE
    SET_ANC = 0x17
    BATTERY = 0x1D
    SET_EQ = 0x22


def get_state() -> list[tuple[int, bytes]]:
    """Solicita o estado atual do fone (ANC e Bateria) via opcode REQUEST."""
    return [
        (Cmd.REQUEST, bytes([Cmd.SET_ANC])),
        (Cmd.REQUEST, bytes([Cmd.BATTERY])),
    ]


def set_anc(mode: AncMode) -> tuple[int, bytes]:
    """Monta payload para alternar o modo de cancelamento de ruído."""
    if mode == AncMode.ANC:
        return Cmd.SET_ANC, bytes([0x01, 0x05, 0x00])
    elif mode == AncMode.TRANSPARENCY:
        return Cmd.SET_ANC, bytes([0x03, 0x01, 0x04])
    else:
        return Cmd.SET_ANC, bytes([0x02, 0x00, 0x00])


# Payloads DSP de 42 bytes para cada preset de equalização (capturados via btsnoop).
_EQ_PAYLOADS = {
    EqPreset.POP:     bytes.fromhex("0170fe1e000000500000aa005cf93c00022c0138ffc80002bc02c800640002b00406ffc80002f00a2c016400028813d4fec800021027a8fd2c0102f82ac800c80003"),
    EqPreset.BASS:    bytes.fromhex("0270fe1e000000320000aa005cf92800022c0138ffc80002bc02c800640002b00406ffc80002f00a900164000288130000c800021027a8fd2c0102f82ac800c80003"),
    EqPreset.ROCK:    bytes.fromhex("0370fe4600f4013c0002aa005cf93c00022c0138ffc80002bc02c800640002b00406ffc80002f00a00006400028813a8fd6400021027a8fd2c0102f82a0000460002"),
    EqPreset.JAZZ:    bytes.fromhex("0470fe46002c01320002aa005cf93c00022c0138ffc80002bc020000640002b00406ffc80002f00a900164000288130000c800021027d4fe2c0102f82ac800c80003"),
    EqPreset.CLASSIC: bytes.fromhex("0570fe1e000000320000aa005cf93c00022c0138ffc80002bc02c800640002b00406ffc80002f00a000064000288130cfec800021027a8fd2c0102f82a0000c80002"),
    EqPreset.DEFAULT: bytes.fromhex("0670fe1e000000640000aa0088fa3c00022c0138ffc80002bc02c800640002b00406ffc80002f00a2c016400028813d4fec800021027a8fd2c0102f82ac800c80003"),
}


def set_eq(preset: EqPreset) -> tuple[int, bytes]:
    """Monta payload DSP de 42 bytes para o preset de equalização."""
    return Cmd.SET_EQ, _EQ_PAYLOADS.get(preset, _EQ_PAYLOADS[EqPreset.DEFAULT])


def parse_frame(frame: Frame) -> DeviceState | None:
    """Converte uma notificação BLE em estado parcial do dispositivo."""
    if frame.cmd == Cmd.SET_ANC and len(frame.payload) >= 3:
        mode_byte = frame.payload[0]
        if mode_byte == 0x01:
            anc = AncMode.ANC
        elif mode_byte == 0x03:
            anc = AncMode.TRANSPARENCY
        else:
            anc = AncMode.OFF
        return DeviceState(anc=anc)

    elif frame.cmd == Cmd.BATTERY and len(frame.payload) >= 1:
        bat_val = frame.payload[0]
        if bat_val <= 10:
            bat = bat_val * 10
        else:
            bat = min(bat_val & 0x7F, 100)
        return DeviceState(battery=bat)

    return None
