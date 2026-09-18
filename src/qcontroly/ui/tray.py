import importlib.resources
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

class TrayManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
        # Load icon from resources
        res_path = importlib.resources.files("qcontroly.resources")
        icon_path = str(res_path / "icon.svg")
        self.icon = QIcon(icon_path)
        
        self.main_window.setWindowIcon(self.icon)
        self.tray = QSystemTrayIcon(self.icon, self.main_window)
        
        self._build_menu()
        
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _build_menu(self):
        menu = QMenu()
        show_action = QAction("Mostrar / Ocultar", self.main_window)
        show_action.triggered.connect(self.toggle_visibility)
        menu.addAction(show_action)
        
        quit_action = QAction("Sair", self.main_window)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)

    def toggle_visibility(self):
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.activateWindow()

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.toggle_visibility()

    def quit_app(self):
        # We assume main_window has a worker attribute
        if hasattr(self.main_window, 'worker'):
            self.main_window.worker.stop()
        QApplication.quit()

    def show_message(self, title: str, message: str, msecs: int = 2000):
        self.tray.showMessage(title, message, QSystemTrayIcon.Information, msecs)
