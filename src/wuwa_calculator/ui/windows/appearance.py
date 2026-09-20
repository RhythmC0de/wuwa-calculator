"""Apply saved QSettings to QSS, glows, and the wallpaper label."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QUrl, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget

from src.wuwa_calculator.ui.styles.styles import (
    accent_preset,
    application_qss,
    refresh_glows,
    wallpaper_palette,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKGROUND = PACKAGE_ROOT / "Assets" / "app_background_reference.png"
SETTINGS_ORG = "Tethys"
SETTINGS_APP = "Tethys"


def load_preference_bundle() -> tuple[bool, str, int, str]:
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    background = settings.value("background", True, type=bool)
    wallpaper = settings.value("wallpaper", "", type=str)
    interface_opacity = settings.value("interface_opacity", 85, type=int)
    accent_theme = settings.value("accent_theme", "Ciano Tethys", type=str)
    return background, wallpaper, interface_opacity, accent_theme


def apply_saved_stylesheet(app: QApplication) -> None:
    background, wallpaper, interface_opacity, accent_theme = load_preference_bundle()
    app.setStyleSheet(
        application_qss(
            show_background=background,
            wallpaper=wallpaper,
            interface_opacity=interface_opacity,
            accent_theme=accent_theme,
        )
    )


class AppearanceController:
    def __init__(self, window: QMainWindow, background_label: QLabel) -> None:
        self.window = window
        self.background_label = background_label
        self._cache_key: tuple[str, bool, int, int] | None = None

    def apply(self) -> None:
        settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        settings.sync()
        background, wallpaper, interface_opacity, accent_theme = load_preference_bundle()
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(
                application_qss(
                    show_background=background,
                    wallpaper=wallpaper,
                    interface_opacity=interface_opacity,
                    accent_theme=accent_theme,
                )
            )
        for widget in self.window.findChildren(QWidget):
            apply_palette = getattr(widget, "apply_wallpaper_palette", None)
            if callable(apply_palette):
                apply_palette(
                    *wallpaper_palette(wallpaper if background else ""),
                    accent_preset(accent_theme),
                )
        refresh_glows(self.window)
        self.update_background(background, wallpaper)

    def update_background(self, enabled: bool, wallpaper: str) -> None:
        self.background_label.setVisible(enabled)
        if not enabled:
            self._cache_key = None
            return

        cache_key = (wallpaper, enabled, self.window.width(), self.window.height())
        if cache_key == self._cache_key:
            return

        source = QUrl.fromUserInput(wallpaper).toLocalFile() if wallpaper else ""
        pixmap = QPixmap(source or str(DEFAULT_BACKGROUND))
        if pixmap.isNull():
            pixmap = QPixmap(str(DEFAULT_BACKGROUND))
        if pixmap.isNull():
            return
        scaled = pixmap.scaled(
            self.window.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        left = max(0, (scaled.width() - self.window.width()) // 2)
        top = max(0, (scaled.height() - self.window.height()) // 2)
        self.background_label.setGeometry(self.window.rect())
        self.background_label.setPixmap(
            scaled.copy(left, top, self.window.width(), self.window.height())
        )
        self.background_label.lower()
        self._cache_key = cache_key
