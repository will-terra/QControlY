from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

class HeaderComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.battery_lbl = QLabel("—")
        self.battery_lbl.setObjectName("BatteryEmpty")
        self.battery_lbl.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        self.device_name_lbl = QLabel("QCY H3S")
        self.device_name_lbl.setObjectName("DeviceName")
        self.device_name_lbl.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.battery_lbl)
        layout.addWidget(self.device_name_lbl)
        layout.addStretch()

    def set_battery(self, percent: int | None):
        if percent is None:
            self.battery_lbl.setText("—")
            self.battery_lbl.setObjectName("BatteryEmpty")
        else:
            self.battery_lbl.setText(f"{percent}%")
            self.battery_lbl.setObjectName("Battery")
        self.battery_lbl.style().unpolish(self.battery_lbl)
        self.battery_lbl.style().polish(self.battery_lbl)

    def set_device_name(self, name: str):
        self.device_name_lbl.setText(name.upper())
