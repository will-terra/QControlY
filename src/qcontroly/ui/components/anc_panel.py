from PySide6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup, QPushButton
from PySide6.QtCore import Signal
from ...core.model import AncMode

class AncPanelComponent(QWidget):
    anc_changed = Signal(AncMode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.anc_buttons: dict[AncMode, QPushButton] = {}
        self.anc_group = QButtonGroup(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        for mode in AncMode:
            b = QPushButton(mode.value.capitalize())
            b.setObjectName("Anc")
            b.setCheckable(True)
            b.setEnabled(False)
            b.clicked.connect(lambda _=False, m=mode: self.anc_changed.emit(m))
            self.anc_group.addButton(b)
            self.anc_buttons[mode] = b
            layout.addWidget(b)

    def set_enabled(self, enabled: bool):
        for b in self.anc_buttons.values():
            b.setEnabled(enabled)
            if not enabled:
                b.setChecked(False)

    def set_anc_mode(self, mode: AncMode):
        if mode in self.anc_buttons:
            self.anc_buttons[mode].setChecked(True)
