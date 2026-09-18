"""Thread dedicada que roda o event loop asyncio para comunicação BLE (bleak).

A UI chama os métodos públicos de qualquer thread; os resultados voltam
via Signals do Qt (entrega na thread da UI automaticamente).
"""
from __future__ import annotations
import asyncio
from PySide6.QtCore import QThread, Signal
from ..ble import scanner
from ..ble.client import QcyBleClient
from ..core import commands
from ..core.protocol import Frame
from ..core.model import DeviceState


class BleWorker(QThread):
    deviceFound = Signal(list)
    connected = Signal()
    disconnected = Signal()
    stateChanged = Signal(object)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = QcyBleClient(
            on_frame=self._on_frame,
            on_disconnect=lambda: self.disconnected.emit(),
        )

    # ---- Ciclo de vida ---------------------------------------------------

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self):
        if self._loop is None or not self._loop.is_running():
            return

        async def _shutdown():
            try:
                if self.is_connected:
                    await self._client.disconnect()
            except Exception:
                pass

        try:
            coro = _shutdown()
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            future.result(timeout=2)
        except Exception:
            coro.close()
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self.wait(2000)

    def _run(self, coro):
        if self._loop is None:
            self.error.emit("Worker BLE não iniciado")
            return None
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    # ---- API pública (chamar da thread da UI) ----------------------------

    @property
    def is_connected(self) -> bool:
        return self._client.connected

    def scan(self, timeout: float = 5.0):
        async def job():
            try:
                self.deviceFound.emit(await scanner.scan(timeout))
            except Exception as e:
                self.error.emit(f"Falha no escaneamento: {e}")
        self._run(job())

    def connect_device(self, address: str):
        async def job():
            try:
                await self._client.connect(address)
                self.connected.emit()
                for cmd, payload in commands.get_state():
                    await self._send(cmd, payload)
            except Exception as e:
                self.error.emit(f"Falha na conexão: {e}")
        self._run(job())

    def disconnect_device(self):
        self._run(self._client.disconnect())

    def set_anc(self, mode):
        cmd, payload = commands.set_anc(mode)
        self._run(self._send(cmd, payload))

    def set_eq(self, preset):
        cmd, payload = commands.set_eq(preset)
        async def job():
            try:
                await self._send(cmd, payload)
                self.stateChanged.emit(DeviceState(eq=preset))
            except Exception as e:
                self.error.emit(f"Falha ao aplicar EQ: {e}")
        self._run(job())

    # ---- Interno ---------------------------------------------------------

    async def _send(self, cmd: int, payload: bytes):
        try:
            await self._client.send(cmd, payload)
        except Exception as e:
            self.error.emit(f"Falha no envio: {e}")

    def _on_frame(self, frame: Frame):
        state = commands.parse_frame(frame)
        if state is not None:
            self.stateChanged.emit(state)
