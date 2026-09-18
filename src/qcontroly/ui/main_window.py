from PySide6.QtCore import QTimer, Qt, QEvent
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from ..core.model import DeviceState
from .worker import BleWorker
from .tray import TrayManager
from .components.header import HeaderComponent
from .components.anc_panel import AncPanelComponent
from .components.eq_panel import EqPanelComponent
from .components.device_list import DeviceListComponent

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QControlY")
        self.setFixedWidth(280)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.worker = BleWorker()

        self._build_ui()
        self.tray_manager = TrayManager(self)
        self._wire_worker()

        self.worker.start()
        QTimer.singleShot(100, lambda: self.worker.scan(5.0))

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_manager.show_message(
            "QControlY",
            "O aplicativo continua rodando em segundo plano."
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._old_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_old_pos') and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.pos() + delta)
            self._old_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        if hasattr(self, '_old_pos'):
            del self._old_pos
        event.accept()

    def event(self, event: QEvent):
        res = super().event(event)
        if event.type() == QEvent.Type.LayoutRequest:
            self.adjustSize()
        return res

    def _build_ui(self) -> None:
        panel = QWidget()
        panel.setObjectName("Panel")
        panel.setFixedWidth(280)
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        inner_layout.setSpacing(15)

        self.header = HeaderComponent()
        self.anc_panel = AncPanelComponent()
        self.eq_panel = EqPanelComponent()
        self.device_list = DeviceListComponent()

        # Connect UI interactions to worker
        self.anc_panel.anc_changed.connect(lambda mode: self.worker.set_anc(mode) if self.worker.is_connected else None)
        self.eq_panel.eq_changed.connect(lambda preset: self.worker.set_eq(preset) if self.worker.is_connected else None)
        self.device_list.scan_requested.connect(lambda: self.worker.scan(5.0))
        self.device_list.connect_requested.connect(lambda addr: self._connect_device(addr))
        self.device_list.disconnect_requested.connect(self.worker.disconnect_device)

        inner_layout.addWidget(self.header)
        inner_layout.addWidget(self.anc_panel)
        inner_layout.addWidget(self.eq_panel)
        inner_layout.addWidget(self.device_list)
        inner_layout.addStretch()

        root.addWidget(inner)

        # Footer
        footer = QWidget()
        footer.setObjectName("Footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 0, 15, 0)

        toggle_btn = QPushButton("Mostrar / Ocultar")
        toggle_btn.clicked.connect(lambda: self.tray_manager.toggle_visibility())
        quit_btn = QPushButton("Sair")
        quit_btn.clicked.connect(lambda: self.tray_manager.quit_app())

        footer_layout.addWidget(toggle_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(quit_btn)

        root.addWidget(footer)

        self.setCentralWidget(panel)
        self.statusBar().hide()

    def _wire_worker(self) -> None:
        w = self.worker
        w.deviceFound.connect(self._on_devices)
        w.connected.connect(self._on_connected)
        w.disconnected.connect(self._on_disconnected)
        w.stateChanged.connect(self._on_state)
        w.error.connect(lambda m: self.statusBar().showMessage(f"Erro: {m}"))

    def _connect_device(self, addr: str):
        self.statusBar().showMessage("Conectando…")
        self.worker.connect_device(addr)

    def _on_devices(self, devices):
        self.device_list.set_devices(list(devices))
        self.statusBar().showMessage(f"{len(devices)} dispositivo(s) QCY")
        
        if devices and not self.worker.is_connected:
            best = self.device_list.auto_connect_best()
            if best:
                self.statusBar().showMessage(f"Conectando a {best.name}…")

    def _on_connected(self):
        self.device_list.set_connected_state(True)
        self.anc_panel.set_enabled(True)
        self.eq_panel.set_enabled(True)
        
        if self.device_list._devices:
            best = max(self.device_list._devices, key=lambda d: d.rssi or -100)
            self.header.set_device_name(best.name)
            
        self.statusBar().showMessage("Conectado")

    def _on_disconnected(self) -> None:
        self.device_list.set_connected_state(False)
        self.anc_panel.set_enabled(False)
        self.eq_panel.set_enabled(False)
        
        self.header.set_battery(None)
        self.header.set_device_name("QCY H3S")
        self.statusBar().showMessage("Desconectado")

    def _on_state(self, state: DeviceState):
        if state.battery is not None:
            self.header.set_battery(state.battery)
        if state.anc is not None:
            self.anc_panel.set_anc_mode(state.anc)
        if state.eq is not None:
            self.eq_panel.set_eq_preset(state.eq)
