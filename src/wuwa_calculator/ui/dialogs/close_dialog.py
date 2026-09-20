"""Confirm-exit dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QMessageBox, QWidget

TETHYS_CLOSE_ICON_PATH: str | None = None
TETHYS_CLOSE_ICON_URL: str | None = None
TETHYS_CLOSE_ICON_LOCAL: str | None = str(
    Path(__file__).resolve().parents[2] / "Assets" / "close_icon.png"
)


def _circular_pixmap(source: QPixmap, size: int = 64) -> QPixmap:
    icon_pixmap = source.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    circular = QPixmap(size, size)
    circular.fill(Qt.GlobalColor.transparent)
    painter = QPainter(circular)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, icon_pixmap)
    painter.end()
    return circular


class TethysCloseDialog(QMessageBox):
    def __init__(
        self,
        icon_path: str | None = None,
        icon_url: str | None = None,
        icon_local: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fechar Tethys")
        self.setText("Deseja realmente fechar o Tethys?")

        icon_loaded = False
        if icon_local:
            local_path = Path(icon_local)
            if local_path.exists():
                icon_pixmap = QPixmap(str(local_path))
                if not icon_pixmap.isNull():
                    self.setIconPixmap(_circular_pixmap(icon_pixmap))
                    icon_loaded = True

        if not icon_loaded and icon_url:
            fetched = self._fetch_icon_from_url(icon_url)
            if fetched is not None and not fetched.isNull():
                self.setIconPixmap(fetched)
                icon_loaded = True

        if not icon_loaded:
            self.setIcon(QMessageBox.Icon.Warning)

        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        button_yes = self.button(QMessageBox.StandardButton.Yes)
        button_no = self.button(QMessageBox.StandardButton.No)
        if button_yes is not None:
            button_yes.setText("Sim")
        if button_no is not None:
            button_no.setText("Não")
            self.setDefaultButton(QMessageBox.StandardButton.No)

        self.setStyleSheet("""
            QMessageBox {
                background-color: #0c0b10;
                border: 1px solid #3d3859;
                border-radius: 12px;
            }
            QLabel {
                color: #f3f3f5;
                font-family: 'Segoe UI';
                font-size: 14px;
                background: transparent;
            }
            QPushButton {
                background-color: #1a1829;
                color: #f3f3f5;
                border: 1px solid #3d3859;
                border-radius: 6px;
                padding: 6px 20px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #2b2740;
                border: 1px solid #d4af37;
                color: #d4af37;
            }
            QPushButton:pressed {
                background-color: #14121f;
            }
        """)

    @staticmethod
    def _fetch_icon_from_url(url: str) -> QPixmap | None:
        try:
            from urllib.request import Request, urlopen

            request = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )
            with urlopen(request, timeout=5) as response:
                data = response.read()
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    return _circular_pixmap(pixmap)
            return None
        except OSError:
            return None

    @staticmethod
    def confirm_close(
        icon_path: str | None = None,
        icon_url: str | None = None,
        icon_local: str | None = None,
        parent: QWidget | None = None,
    ) -> bool:
        dialog = TethysCloseDialog(icon_path, icon_url, icon_local, parent)
        return dialog.exec() == QMessageBox.StandardButton.Yes
