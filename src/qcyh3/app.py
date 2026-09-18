import logging
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow

_QSS = Path(__file__).parent / "ui" / "nanquim.qss"


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    app = QApplication(sys.argv)
    
    from PySide6.QtGui import QFontDatabase
    QFontDatabase.addApplicationFont(str(Path(__file__).parent / "ui/fonts/SourceSerif4-Regular.ttf"))
    QFontDatabase.addApplicationFont(str(Path(__file__).parent / "ui/fonts/SourceSerif4-SemiBold.ttf"))
    
    app.setStyleSheet(_QSS.read_text(encoding="utf-8"))
    app.setQuitOnLastWindowClosed(False)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
