from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget
from PySide6.QtCore import Signal
from ...core.model import DeviceInfo

class DeviceListComponent(QWidget):
    scan_requested = Signal()
    connect_requested = Signal(str) # address
    disconnect_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices: list[DeviceInfo] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.scan_btn = QPushButton("Escanear")
        self.scan_btn.setObjectName("Link")
        self.scan_btn.clicked.connect(self.scan_requested.emit)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_connect_clicked)
        self.list_widget.setVisible(False)

        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.setObjectName("Primary")
        self.connect_btn.clicked.connect(self._on_connect_clicked)

        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.setObjectName("Link")
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        self.disconnect_btn.setVisible(False)

        layout.addWidget(self.scan_btn)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.disconnect_btn)

    def _on_connect_clicked(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._devices):
            self.connect_requested.emit(self._devices[row].address)

    def set_devices(self, devices: list[DeviceInfo]):
        self._devices = devices
        self.list_widget.clear()
        for d in self._devices:
            self.list_widget.addItem(f"{d.name}  ({d.rssi or '?'} dBm)")
        self.list_widget.setVisible(bool(self._devices))

    def auto_connect_best(self) -> DeviceInfo | None:
        if self._devices:
            best = max(self._devices, key=lambda d: d.rssi or -100)
            self.connect_requested.emit(best.address)
            return best
        return None

    def set_connected_state(self, connected: bool):
        self.connect_btn.setVisible(not connected)
        self.disconnect_btn.setVisible(connected)
        self.list_widget.setVisible(not connected)
        self.scan_btn.setVisible(not connected)
