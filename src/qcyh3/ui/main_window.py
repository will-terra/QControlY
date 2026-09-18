from __future__ import annotations
import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QMenu, QPushButton, QSystemTrayIcon, QVBoxLayout, QWidget,
)
from ..core.model import AncMode, DeviceState, EqPreset
from .worker import BleWorker

_ICON_PATH = os.path.join(os.path.dirname(__file__), "icon.svg")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QControlY")
        self.resize(280, 420)
        self.setFixedWidth(280)

        self._devices: list = []
        self._device_name: str = ""
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
        panel = QWidget()
        panel.setObjectName("Panel")
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        inner_layout.setSpacing(15)

        # -- Topo: bateria + nome ------------------------------------------
        self.battery_lbl = QLabel("—")
        self.battery_lbl.setObjectName("BatteryEmpty")
        self.battery_lbl.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        self.device_name_lbl = QLabel("QCY H3S")
        self.device_name_lbl.setObjectName("DeviceName")
        self.device_name_lbl.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(self.battery_lbl)
        head.addWidget(self.device_name_lbl)
        head.addStretch()
        inner_layout.addLayout(head)

        # -- ANC -----------------------------------------------------------
        self.anc_buttons: dict[AncMode, QPushButton] = {}
        anc_group = QButtonGroup(self)
        anc_layout = QVBoxLayout()
        anc_layout.setSpacing(5)
        for mode in AncMode:
            b = QPushButton(mode.value.capitalize())
            b.setObjectName("Anc")
            b.setCheckable(True)
            b.setEnabled(False)
            b.clicked.connect(lambda _=False, m=mode: self.worker.set_anc(m))
            anc_group.addButton(b)
            self.anc_buttons[mode] = b
            anc_layout.addWidget(b)
        inner_layout.addLayout(anc_layout)

        # -- Equalizador (expansível) --------------------------------------
        self.eq_toggle = QPushButton("Equalizador · Padrão")
        self.eq_toggle.setObjectName("Link")
        self.eq_toggle.clicked.connect(self._toggle_eq_panel)
        inner_layout.addWidget(self.eq_toggle)

        self.eq_panel = QWidget()
        eq_layout = QVBoxLayout(self.eq_panel)
        eq_layout.setContentsMargins(0, 0, 0, 0)
        eq_layout.setSpacing(0)

        self.eq_buttons: dict[EqPreset, QPushButton] = {}
        eq_group = QButtonGroup(self)
        for preset in EqPreset:
            b = QPushButton(f"○  {preset.value.capitalize()}")
            b.setObjectName("EqRow")
            b.setCheckable(True)
            b.setEnabled(False)
            b.clicked.connect(lambda _=False, p=preset: self._on_eq_selected(p))
            eq_group.addButton(b)
            self.eq_buttons[preset] = b
            eq_layout.addWidget(b)
        self.eq_buttons[EqPreset.DEFAULT].setChecked(True)
        self.eq_panel.setVisible(False)
        inner_layout.addWidget(self.eq_panel)

        # -- Lista de dispositivos (visível durante scan) ------------------
        self.scan_link = QPushButton("Escanear")
        self.scan_link.setObjectName("Link")
        self.scan_link.clicked.connect(lambda: self.worker.scan(5.0))

        self.device_list = QListWidget()
        self.device_list.itemDoubleClicked.connect(self._connect_selected)
        self.device_list.setVisible(False)

        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.setObjectName("Primary")
        self.connect_btn.clicked.connect(self._connect_selected)

        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.setObjectName("Link")
        self.disconnect_btn.clicked.connect(self.worker.disconnect_device)
        self.disconnect_btn.setVisible(False)

        inner_layout.addWidget(self.scan_link)
        inner_layout.addWidget(self.device_list)
        inner_layout.addWidget(self.connect_btn)
        inner_layout.addWidget(self.disconnect_btn)

        inner_layout.addStretch()
        root.addWidget(inner)

        # -- Rodapé --------------------------------------------------------
        footer = QWidget()
        footer.setObjectName("Footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 0, 15, 0)

        toggle_btn = QPushButton("Mostrar / Ocultar")
        toggle_btn.clicked.connect(self._toggle_visibility)
        quit_btn = QPushButton("Sair")
        quit_btn.clicked.connect(self._quit)

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

    # ---- Ações -----------------------------------------------------------

    def _toggle_eq_panel(self):
        self.eq_panel.setVisible(not self.eq_panel.isVisible())

    def _mark_eq(self, active: EqPreset):
        for preset, btn in self.eq_buttons.items():
            mark = "●" if preset is active else "○"
            btn.setText(f"{mark}  {preset.value.capitalize()}")

    def _on_eq_selected(self, preset: EqPreset):
        self.eq_toggle.setText(f"Equalizador · {preset.value.capitalize()}")
        self._mark_eq(preset)
        if self.worker.is_connected:
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
        self.device_list.setVisible(bool(self._devices))
        self.statusBar().showMessage(f"{len(self._devices)} dispositivo(s) QCY")

        # Auto-conexão: conecta ao dispositivo com melhor sinal
        if self._devices and not self.worker.is_connected:
            best = max(self._devices, key=lambda d: d.rssi or -100)
            self.statusBar().showMessage(f"Conectando a {best.name}…")
            self.worker.connect_device(best.address)

    def _on_connected(self):
        self.connect_btn.setVisible(False)
        self.disconnect_btn.setVisible(True)
        self.device_list.setVisible(False)
        self.scan_link.setVisible(False)
        for b in self.anc_buttons.values():
            b.setEnabled(True)
        for b in self.eq_buttons.values():
            b.setEnabled(True)

        # Pega o nome do dispositivo conectado
        if self._devices:
            best = max(self._devices, key=lambda d: d.rssi or -100)
            self._device_name = best.name
            self.device_name_lbl.setText(self._device_name.upper())

        self.statusBar().showMessage("Conectado")

    def _on_disconnected(self) -> None:
        self.connect_btn.setVisible(True)
        self.disconnect_btn.setVisible(False)
        self.scan_link.setVisible(True)
        self.battery_lbl.setText("—")
        self.battery_lbl.setObjectName("BatteryEmpty")
        self.battery_lbl.style().unpolish(self.battery_lbl)
        self.battery_lbl.style().polish(self.battery_lbl)
        self.device_name_lbl.setText("QCY H3S")
        for b in self.anc_buttons.values():
            b.setEnabled(False)
            b.setChecked(False)
        for b in self.eq_buttons.values():
            b.setEnabled(False)
        self.statusBar().showMessage("Desconectado")

    def _on_state(self, state: DeviceState):
        if state.battery is not None:
            self.battery_lbl.setText(f"{state.battery}%")
            self.battery_lbl.setObjectName("Battery")
            self.battery_lbl.style().unpolish(self.battery_lbl)
            self.battery_lbl.style().polish(self.battery_lbl)
        if state.anc in self.anc_buttons:
            self.anc_buttons[state.anc].setChecked(True)
        if state.eq is not None:
            if state.eq in self.eq_buttons:
                self.eq_buttons[state.eq].setChecked(True)
            self.eq_toggle.setText(f"Equalizador · {state.eq.value.capitalize()}")
            self._mark_eq(state.eq)
