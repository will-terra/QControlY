from __future__ import annotations
import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QGroupBox, QHBoxLayout, QLabel,
    QListWidget, QMainWindow, QMenu, QPushButton, QSystemTrayIcon,
    QVBoxLayout, QWidget,
)
from ..core.model import AncMode, DeviceState, EqPreset
from .worker import BleWorker

_ICON_PATH = os.path.join(os.path.dirname(__file__), "icon.svg")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QControlY — QCY H3 / H3 Pro / H3S")
        self.resize(860, 520)

        self._devices: list = []
        self.worker = BleWorker()

        self._build_ui()
        self._setup_tray()
        self._wire_worker()
        self.worker.start()

        QTimer.singleShot(100, lambda: self.worker.scan(5.0))

    # ---- Eventos ---------------------------------------------------------

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "QControlY",
            "O aplicativo continua rodando em segundo plano.",
            QSystemTrayIcon.Information,
            2000,
        )

    # ---- System Tray -----------------------------------------------------

    def _setup_tray(self):
        icon = QIcon(_ICON_PATH)
        self.setWindowIcon(icon)

        self._tray = QSystemTrayIcon(icon, self)

        menu = QMenu()
        show_action = QAction("Mostrar / Ocultar", self)
        show_action.triggered.connect(self._toggle_visibility)
        menu.addAction(show_action)

        quit_action = QAction("Sair", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self._toggle_visibility()

    def _quit(self):
        self.worker.stop()
        QApplication.quit()

    # ---- UI --------------------------------------------------------------

    def _build_ui(self) -> None:
        scan_btn = QPushButton("Escanear")
        scan_btn.clicked.connect(lambda: self.worker.scan(5.0))

        self.device_list = QListWidget()
        self.device_list.itemDoubleClicked.connect(self._connect_selected)

        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self._connect_selected)
        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.clicked.connect(self.worker.disconnect_device)

        left_layout = QVBoxLayout()
        left_layout.addWidget(scan_btn)
        left_layout.addWidget(self.device_list, stretch=1)
        left_layout.addWidget(self.connect_btn)
        left_layout.addWidget(self.disconnect_btn)
        left = QGroupBox("Dispositivos")
        left.setLayout(left_layout)

        self.battery_lbl = QLabel("Bateria: —")
        self.battery_lbl.setAlignment(Qt.AlignCenter)

        self.anc_buttons: dict[AncMode, QPushButton] = {}
        group = QButtonGroup(self)
        anc_row = QHBoxLayout()
        for mode in AncMode:
            b = QPushButton(mode.value.capitalize())
            b.setCheckable(True)
            b.setEnabled(False)
            b.clicked.connect(lambda _=False, m=mode: self.worker.set_anc(m))
            group.addButton(b)
            self.anc_buttons[mode] = b
            anc_row.addWidget(b)

        anc_box = QGroupBox("Cancelamento de ruído")
        anc_layout = QVBoxLayout(anc_box)
        anc_layout.addWidget(self.battery_lbl)
        anc_layout.addLayout(anc_row)

        self.eq_combo = QComboBox()
        self.eq_combo.setEnabled(False)
        self.eq_combo.blockSignals(True)
        for preset in EqPreset:
            self.eq_combo.addItem(preset.value.capitalize(), preset)
        self.eq_combo.blockSignals(False)
        self.eq_combo.currentIndexChanged.connect(self._on_eq_changed)

        eq_box = QGroupBox("Equalizador")
        eq_layout = QVBoxLayout(eq_box)
        eq_layout.addWidget(self.eq_combo)

        right = QVBoxLayout()
        right.addWidget(anc_box)
        right.addWidget(eq_box)

        cols = QHBoxLayout()
        cols.addWidget(left, stretch=1)
        cols.addLayout(right, stretch=2)
        central = QWidget()
        central.setLayout(cols)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Pronto — clique em Escanear")

    def _wire_worker(self) -> None:
        w = self.worker
        w.deviceFound.connect(self._on_devices)
        w.connected.connect(self._on_connected)
        w.disconnected.connect(self._on_disconnected)
        w.stateChanged.connect(self._on_state)
        w.error.connect(lambda m: self.statusBar().showMessage(f"Erro: {m}"))

    # ---- Ações -----------------------------------------------------------

    def _on_eq_changed(self, index: int) -> None:
        preset = self.eq_combo.itemData(index)
        if preset and self.worker.is_connected:
            self.worker.set_eq(preset)

    def _connect_selected(self, *_):
        row = self.device_list.currentRow()
        if 0 <= row < len(self._devices):
            self.statusBar().showMessage("Conectando…")
            self.worker.connect_device(self._devices[row].address)

    # ---- Callbacks do Worker ---------------------------------------------

    def _on_devices(self, devices):
        self._devices = list(devices)
        self.device_list.clear()
        for d in self._devices:
            self.device_list.addItem(f"{d.name}  ({d.rssi or '?'} dBm)")
        self.statusBar().showMessage(f"{len(self._devices)} dispositivo(s) QCY")

        # Auto-conexão: conecta ao dispositivo com melhor sinal
        if self._devices and not self.worker.is_connected:
            best = max(self._devices, key=lambda d: d.rssi or -100)
            self.statusBar().showMessage(f"Conectando a {best.name}…")
            self.worker.connect_device(best.address)

    def _on_connected(self):
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        for b in self.anc_buttons.values():
            b.setEnabled(True)
        self.eq_combo.setEnabled(True)
        self.statusBar().showMessage("Conectado")

    def _on_disconnected(self) -> None:
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.battery_lbl.setText("Bateria: —")
        for b in self.anc_buttons.values():
            b.setEnabled(False)
            b.setChecked(False)
        self.eq_combo.setEnabled(False)
        self.statusBar().showMessage("Desconectado")

    def _on_state(self, state: DeviceState):
        if state.battery is not None:
            self.battery_lbl.setText(f"Bateria: {state.battery}%")
        if state.anc in self.anc_buttons:
            self.anc_buttons[state.anc].setChecked(True)
        if state.eq is not None:
            i = self.eq_combo.findData(state.eq)
            if i >= 0:
                self.eq_combo.blockSignals(True)
                self.eq_combo.setCurrentIndex(i)
                self.eq_combo.blockSignals(False)
