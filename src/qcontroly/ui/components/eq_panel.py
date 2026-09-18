from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Signal
from ...core.model import EqPreset

class EqPanelComponent(QWidget):
    eq_changed = Signal(EqPreset)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.eq_toggle = QPushButton("Equalizador · Padrão")
        self.eq_toggle.setObjectName("Link")
        self.eq_toggle.clicked.connect(self._toggle_eq_panel)
        layout.addWidget(self.eq_toggle)

        self.eq_container = QWidget()
        container_layout = QVBoxLayout(self.eq_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.eq_buttons: dict[EqPreset, QPushButton] = {}
        self.eq_group = QButtonGroup(self)
        
        for preset in EqPreset:
            b = QPushButton(f"○  {preset.value.capitalize()}")
            b.setObjectName("EqRow")
            b.setCheckable(True)
            b.setEnabled(False)
            b.clicked.connect(lambda _=False, p=preset: self._on_eq_selected(p))
            self.eq_group.addButton(b)
            self.eq_buttons[preset] = b
            container_layout.addWidget(b)
            
        self.eq_buttons[EqPreset.DEFAULT].setChecked(True)
        self.eq_container.setVisible(False)
        layout.addWidget(self.eq_container)

    def _toggle_eq_panel(self):
        self.eq_container.setVisible(not self.eq_container.isVisible())

    def _mark_eq(self, active: EqPreset):
        for preset, btn in self.eq_buttons.items():
            mark = "●" if preset is active else "○"
            btn.setText(f"{mark}  {preset.value.capitalize()}")

    def _on_eq_selected(self, preset: EqPreset):
        self.eq_changed.emit(preset)

    def set_enabled(self, enabled: bool):
        for b in self.eq_buttons.values():
            b.setEnabled(enabled)

    def set_eq_preset(self, preset: EqPreset):
        if preset in self.eq_buttons:
            self.eq_buttons[preset].setChecked(True)
        self.eq_toggle.setText(f"Equalizador · {preset.value.capitalize()}")
        self._mark_eq(preset)
