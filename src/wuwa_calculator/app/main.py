import os
import sys
from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module
from ..ui.panels.window import WuwaQtWindow as MainWindow
from ..ui.windows.appearance import apply_saved_stylesheet

if __name__ == "__main__":
    raise SystemExit(main())


def main() -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.ffmpeg=false")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_saved_stylesheet(app)  # QSettings + application_qss
    window = MainWindow()
    window.show()
    return app.exec()
