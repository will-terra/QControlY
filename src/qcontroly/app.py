import logging
import sys
import importlib.resources
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from .ui.main_window import MainWindow

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    app = QApplication(sys.argv)
    
    res_path = importlib.resources.files("qcontroly.resources")
    
    QFontDatabase.addApplicationFont(str(res_path / "fonts" / "SourceSerif4-Regular.ttf"))
    QFontDatabase.addApplicationFont(str(res_path / "fonts" / "SourceSerif4-SemiBold.ttf"))
    
    app.setStyleSheet((res_path / "nanquim.qss").read_text(encoding="utf-8"))
    app.setQuitOnLastWindowClosed(False)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
