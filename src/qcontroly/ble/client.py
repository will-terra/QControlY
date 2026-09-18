"""Transporte BLE: conexão GATT, write e notify. Fala em Frames, não em domínio."""
from __future__ import annotations
import logging
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from ..core.protocol import Frame, FrameParser, build_frame
from . import uuids

log = logging.getLogger(__name__)

# Sequência de handshake proprietária do H3S (capturada via btsnoop_hci.log).
# Sem esses pacotes o fone derruba a conexão BLE após ~2 segundos.
_HANDSHAKE = [
    b"\xfe\xdc\xba\xc0\x03\x00\x06\x53\xff\xff\xff\xff\x00\xef",
    b"\xfe\xdc\xba\xc0\xc0\x00\x07\x54\x05\x07\x6a\xac\x6e\x38\xef",
    b"\xfe\xdc\xba\xc0\xc1\x00\x05\x55\x00\x00\x0d\x21\xef",
]


class QcyBleClient:
    def __init__(self, on_frame=None, on_disconnect=None):
        self._client: BleakClient | None = None
        self._parser = FrameParser()
        self._on_frame = on_frame
        self._on_disconnect = on_disconnect
        self._seq = 1

    @property
    def connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    async def connect(self, address: str) -> None:
        self._parser.reset()
        self._seq = 0x56
        self._client = BleakClient(address, disconnected_callback=self._handle_disconnect)
        await self._client.connect()

        # Tenta ler o nome real gravado na characteristic GAP
        try:
            name_bytes = await self._client.read_gatt_char(uuids.GATT_DEVICE_NAME)
            real_name = name_bytes.decode("utf-8", errors="ignore").strip("\x00")
            if real_name:
                from .scanner import save_cached_name
                save_cached_name(address, real_name)
        except Exception:
            log.debug("Não foi possível ler o nome do dispositivo %s", address)

        await self._client.start_notify(uuids.QCY_NOTIFY, self._handle_notify)

        # Handshake de autenticação
        for pkt in _HANDSHAKE:
            try:
                await self._client.write_gatt_char(uuids.QCY_WRITE, pkt, response=False)
            except Exception:
                log.warning("Falha ao enviar handshake para %s", address)
                break

    async def disconnect(self) -> None:
        if self.connected:
            await self._client.disconnect()

    async def send(self, cmd: int, payload: bytes = b"") -> bytes:
        """Monta e envia um quadro de comando. Retorna os bytes transmitidos."""
        if not self.connected:
            raise ConnectionError("não conectado")

        self._seq = (self._seq + 1) % 256
        frame = build_frame(cmd, payload, seq=self._seq)
        await self._client.write_gatt_char(uuids.QCY_WRITE, frame, response=False)
        return frame

    def _handle_notify(self, _ch: BleakGATTCharacteristic, data: bytearray) -> None:
        for frame in self._parser.feed(bytes(data)):
            log.debug("RX cmd=%#04x payload=%s", frame.cmd, frame.payload.hex(" "))
            if self._on_frame:
                self._on_frame(frame)

    def _handle_disconnect(self, _client) -> None:
        self._parser.reset()
        if self._on_disconnect:
            self._on_disconnect()
