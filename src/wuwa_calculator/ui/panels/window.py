import re
import unicodedata
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPixmap, QResizeEvent
# PySide6 exposes these widget classes dynamically; pylint cannot resolve them
# from the package metadata and incorrectly reports E0611 for valid imports.
# pylint: disable=no-name-in-module
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
# pylint: enable=no-name-in-module

from src.wuwa_calculator.data.characters_elements import CHARACTER_ELEMENTS
from src.wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS
from src.wuwa_calculator.ui.components.components import Card
from src.wuwa_calculator.ui.dialogs.about_dialog import AboutDialog
from src.wuwa_calculator.ui.dialogs.import_stats_dialog import ImportDialog
from src.wuwa_calculator.ui.dialogs.settings_dialog import SettingsDialog
from src.wuwa_calculator.ui.dialogs.close_dialog import TETHYS_CLOSE_ICON_LOCAL, TETHYS_CLOSE_ICON_PATH, TETHYS_CLOSE_ICON_URL, TethysCloseDialog
from src.wuwa_calculator.ui.tabs.placeholder_tab import PlaceholderTab
from src.wuwa_calculator.ui.tabs.resonator_tab import ResonatorTab
from src.wuwa_calculator.ui.components.components import TitleLabel
from src.wuwa_calculator.ui.components.character_sidebar_button import CharacterSidebarButton
from src.wuwa_calculator.ui.styles.styles import (
    accent_preset,
    application_qss,
    refresh_glows,
    wallpaper_palette,
)


ELEMENT_NAV_COLORS = {
    "Aero": ("#163d4a", "#4cc9f0", "#d9f7ff", "#1f5668"),
    "Glacio": ("#163b52", "#72d2ff", "#e1f7ff", "#205d7d"),
    "Electro": ("#33204f", "#b084ff", "#f1e6ff", "#4d2d73"),
    "Fusion": ("#4b251d", "#ff8a65", "#fff0e8", "#713628"),
    "Havoc": ("#401d35", "#e56bba", "#ffe8f7", "#652d54"),
    "Spectro": ("#443b18", "#e8d66b", "#fffbe0", "#665a22"),
}


class WuwaQtWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.preferences = QSettings("Tethys", "Tethys")
        self.setWindowTitle("Tethys System")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setFixedSize(1440, 900)
        self.background_label = QLabel(self)
        self.background_label.setObjectName("appBackground")
        self.background_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        acrylic_blur = QGraphicsBlurEffect(self.background_label)
        acrylic_blur.setBlurRadius(18)
        self.background_label.setGraphicsEffect(acrylic_blur)
        self.background_label.lower()
        self._background_cache_key: tuple[str, bool, int, int] | None = None

        shell = QWidget()
        shell.setObjectName("appShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(12, 10, 12, 12)
        shell_layout.setSpacing(10)

        header = Card()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.addWidget(TitleLabel("Tethys System"))
        header_layout.addStretch(1)

        self.character_id_entry = QLineEdit()
        self.character_id_entry.setPlaceholderText("Digite o nome do(a) personagem...")
        self.character_id_entry.setFixedWidth(210)

        self.character_load_button = QPushButton("Buscar")
        self.character_load_button.setObjectName("primaryAction")

        self.import_button = QPushButton("Carregar Stats")
        self.import_button.setObjectName("primaryAction")

        header_layout.addWidget(self.character_id_entry)
        header_layout.addWidget(self.character_load_button)
        header_layout.addWidget(self.import_button)

        self.character_status = QLabel("")
        self.character_status.setObjectName("onlineStatus")

        header_layout.addWidget(self.character_status)
        shell_layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")
        tabs.tabBar().hide()
        
        def build_home() -> QWidget:
            from src.wuwa_calculator.ui.tabs.home_tab import HomeTab
            return HomeTab()

        def build_teams() -> QWidget:
            from src.wuwa_calculator.ui.tabs.teams_tab import TeamsTab
            return TeamsTab()

        def build_history() -> QWidget:
            from src.wuwa_calculator.ui.tabs.history_tab import HistoryTab
            return HistoryTab()

        def build_multimedia() -> QWidget:
            from src.wuwa_calculator.ui.tabs.multimedia_tab import MultimediaTab
            return MultimediaTab()

        self._tab_factories = (
            build_home,
            build_teams,
            build_history,
            build_multimedia,
            lambda: PlaceholderTab(
                "Fontes de dados",
                "Tela preparada para exibir fontes, "
                "cache e estado das integrações."),
        )
        self._tab_titles = ("Home", "Teams", "Histórico", "Mapeamento de Frequências", "Fontes de dados")
        self._tab_widgets: dict[int, QWidget] = {}
        self._active_main_index: int | None = None
        self.tabs = tabs
        for title in self._tab_titles:
            tabs.addTab(QWidget(), title)
        multimedia_tab = build_multimedia()
        tabs.removeTab(3)
        tabs.insertTab(3, multimedia_tab, self._tab_titles[3])
        self._tab_widgets[3] = multimedia_tab
        tabs.currentChanged.connect(self._handle_main_tab_changed)
        self._handle_main_tab_changed(0)

        self.character_tabs: dict[str, ResonatorTab] = {}
        self.character_open_order: list[str] = []
        self.sidebar_buttons: dict[str, QPushButton] = {}
        self.character_sidebar_rows: dict[str, QWidget] = {}

        workspace = QHBoxLayout()
        workspace.setContentsMargins(0, 0, 0, 0)
        workspace.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(184)

        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(14, 18, 14, 18)
        self.sidebar_layout.setSpacing(8)
        for index, label in enumerate(("⌂   Home",
                                       "♣   Teams",
                                       "◷   Histórico",
                                       "⌁   Frequências")):
            self._add_sidebar_button(self.sidebar_layout, label, index)
        self.sidebar_layout.addSpacing(10)
        self.character_sidebar_layout = QVBoxLayout()
        self.character_sidebar_layout.setSpacing(8)
        self.sidebar_layout.addLayout(self.character_sidebar_layout)
        self.sidebar_layout.addSpacing(10)
        self.sidebar_layout.addStretch(1)

        settings_button = self._add_sidebar_button(
            self.sidebar_layout, "⚙   Configurações", None)
        settings_button.clicked.connect(self.open_settings)
        about_button = self._add_sidebar_button(
            self.sidebar_layout, "ⓘ   Sobre", None)

        about_button.clicked.connect(self.open_about)
        workspace.addWidget(sidebar)
        workspace.addWidget(tabs, 1)
        shell_layout.addLayout(workspace, 1)

        self._set_sidebar_active("Home")
        self.setCentralWidget(shell)
        self._update_background(
            self.preferences.value("background", True, type=bool),
            self.preferences.value("wallpaper", "", type=str),
        )
        self.character_load_button.clicked.connect(
            self.open_character_tab)
        self.character_id_entry.returnPressed.connect(
            self.open_character_tab)
        self.import_button.clicked.connect(self.open_import_dialog)
        self.apply_preferences()

    def apply_preferences(self) -> None:
        self.preferences.sync()
        background = self.preferences.value("background", True, type=bool)
        wallpaper = self.preferences.value("wallpaper", "", type=str)
        interface_opacity = self.preferences.value("interface_opacity", 85, type=int)
        accent_theme = self.preferences.value("accent_theme", "Ciano Tethys", type=str)
        app = QApplication.instance()

        if app is not None:
            app.setStyleSheet(application_qss(
                show_background=background,
                wallpaper=wallpaper,
                interface_opacity=interface_opacity,
                accent_theme=accent_theme,
            ))
        for widget in self.findChildren(QWidget):
            apply_palette = getattr(widget, "apply_wallpaper_palette", None)
            if callable(apply_palette):
                apply_palette(
                    *wallpaper_palette(wallpaper if background else ""),
                    accent_preset(accent_theme),
                )
        refresh_glows(self)
        self._update_background(background, wallpaper)

    def _update_background(self, enabled: bool, wallpaper: str) -> None:
        self.background_label.setVisible(enabled)
        if not enabled:
            self._background_cache_key = None
            return

        cache_key = (wallpaper, enabled, self.width(), self.height())
        if cache_key == self._background_cache_key:
            return

        source = (
            QUrl.fromUserInput(wallpaper).toLocalFile()
            if wallpaper else "")
        project_root = Path(__file__).resolve().parent.parent
        default_background = (
            project_root / "Assets" / "app_background_reference.png")
        pixmap = QPixmap(source or str(default_background))

        if pixmap.isNull():
            pixmap = QPixmap(str(default_background))
        if pixmap.isNull():
            return
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        left = max(0, (scaled.width() - self.width()) // 2)
        top = max(0, (scaled.height() - self.height()) // 2)
        self.background_label.setGeometry(self.rect())
        self.background_label.setPixmap(
            scaled.copy(left, top, self.width(), self.height()))
        self.background_label.lower()
        self._background_cache_key = cache_key

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_background(
            self.preferences.value("background", True, type=bool),
            self.preferences.value("wallpaper", "", type=str),
        )

    def closeEvent(self, event) -> None:
        if self.preferences.value("confirm_exit", True, type=bool):
            if not TethysCloseDialog.confirm_close(
                icon_path=TETHYS_CLOSE_ICON_PATH,
                icon_url=TETHYS_CLOSE_ICON_URL,
                icon_local=TETHYS_CLOSE_ICON_LOCAL,
                parent=self,
            ):
                event.ignore()
                return
        event.accept()

    def _add_sidebar_button(
        self,
        layout: QVBoxLayout,
        label: str,
        tab_index: int | None,
        element: str | None = None,
    ) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("nav")
        if element:
            button.setProperty("element", element)
            background, border, text, hover = ELEMENT_NAV_COLORS.get(
                element, ELEMENT_NAV_COLORS["Spectro"]
            )
            button.setStyleSheet(
                f"QPushButton {{ background: {background}; color: {text}; "
                f"border: 1px solid {border}; border-radius: 7px; padding: 10px; }}"
                f"QPushButton:hover {{ background: {hover}; border: 1px solid {border}; }}"
            )
        if tab_index is not None:
            button.clicked.connect(
                lambda: self._select_main_tab(tab_index, label))
            self.sidebar_buttons[label] = button
        layout.addWidget(button)
        return button

    def open_settings(self) -> None:
        SettingsDialog(self).exec()

    def open_about(self) -> None:
        AboutDialog(self).exec()

    def open_import_dialog(self) -> None:
        character_tab = self.tabs.currentWidget()
        if not isinstance(character_tab, ResonatorTab):
            QMessageBox.information(
                self,
                "Personagem não carregado",
                "Carregue uma ID de personagem antes de importar a imagem.",
            )
            return
        ImportDialog(self, character_tab).exec()
    
    def _select_main_tab(self, index: int, label: str) -> None:
        self.tabs.setCurrentIndex(index)
        self._set_sidebar_active(label)

    def _ensure_main_tab(self, index: int) -> None:
        if index < 0 or index >= len(self._tab_factories):
            return
        if index in self._tab_widgets:
            return
        factory = self._tab_factories[index]
        widget = factory()
        old_widget = self.tabs.widget(index)
        self._tab_widgets[index] = widget
        self.tabs.blockSignals(True)
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, widget, self._tab_titles[index])
        self.tabs.blockSignals(False)
        if old_widget is not None:
            old_widget.deleteLater()
        self.tabs.setCurrentIndex(index)

    def _handle_main_tab_changed(self, index: int) -> None:
        current_widget = self.tabs.widget(index)
        if isinstance(current_widget, ResonatorTab):
            previous_index = self._active_main_index
            if previous_index is not None and previous_index != index:
                previous_widget = self.tabs.widget(previous_index)
                if previous_widget is not None:
                    if hasattr(previous_widget, "set_active"):
                        previous_widget.set_active(False)
                    previous_widget.setUpdatesEnabled(False)
            current_widget.setUpdatesEnabled(True)
            current_widget.show()
            current_widget.update()
            self._active_main_index = index
            return
        previous_index = self._active_main_index
        if previous_index is not None and previous_index != index:
            previous_widget = self._tab_widgets.get(previous_index)
            if previous_widget is not None:
                if hasattr(previous_widget, "set_active"):
                    previous_widget.set_active(False)
                previous_widget.setUpdatesEnabled(False)
        self._ensure_main_tab(index)
        current_widget = self._tab_widgets.get(index)
        if current_widget is not None:
            current_widget.setUpdatesEnabled(True)
            if hasattr(current_widget, "set_active"):
                current_widget.set_active(True)
            current_widget.show()
            current_widget.update()
        self._active_main_index = index

    def _set_sidebar_active(self, active_label: str) -> None:
        for label, button in self.sidebar_buttons.items():
            button.setObjectName("navActive"
                                 if label == active_label else "nav")
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _add_character_sidebar_button(
        self,
        character_id: str,
        label: str,
        element: str | None,
    ) -> None:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        button = CharacterSidebarButton(label)
        button.setObjectName("nav")
        if element:
            button.setProperty("element", element)
            background, border, text, hover = ELEMENT_NAV_COLORS.get(
                element, ELEMENT_NAV_COLORS["Spectro"]
            )
            button.setStyleSheet(
                f"QPushButton {{ background: {background}; color: {text}; "
                f"border: 1px solid {border}; border-radius: 7px; padding: 10px; "
                f"padding-right: 32px; }}"
                f"QPushButton:hover {{ background: {hover}; border: 1px solid {border}; }}"
            )
        row_layout.addWidget(button)
        self.sidebar_buttons[label] = button
        button.clicked.connect(
            lambda: self._select_character_tab(character_id, label))
        button.close_requested.connect(
            lambda: self._close_character_tab(character_id))
        self.character_sidebar_rows[character_id] = row
        self.character_sidebar_layout.addWidget(row)

    def _select_character_tab(self, character_id: str, label: str) -> None:
        character_tab = self.character_tabs.get(character_id)
        if character_tab is None:
            return
        self.tabs.setCurrentWidget(character_tab)
        self._set_sidebar_active(label)

    def _close_character_tab(self, character_id: str) -> None:
        character_tab = self.character_tabs.pop(character_id, None)
        row = self.character_sidebar_rows.pop(character_id, None)
        if character_tab is None:
            return

        label = (
            f"{self._element_icon(CHARACTER_ELEMENTS.get(character_id))}   "
            f"{character_id.title()}"
        )
        self.sidebar_buttons.pop(label, None)
        was_current = self.tabs.currentWidget() is character_tab
        history_index = self.character_open_order.index(character_id)
        if history_index == 0:
            previous_character_id = (
                self.character_open_order[1]
                if len(self.character_open_order) > 1 else None
            )
        else:
            previous_character_id = self.character_open_order[history_index - 1]
        self.character_open_order.remove(character_id)
        tab_index = self.tabs.indexOf(character_tab)
        if tab_index >= 0:
            self.tabs.removeTab(tab_index)
        character_tab.deleteLater()
        if row is not None:
            row.deleteLater()

        if was_current:
            previous_tab = self.character_tabs.get(previous_character_id)
            if previous_tab is not None:
                self.tabs.setCurrentWidget(previous_tab)
                previous_label = (
                    f"{self._element_icon(CHARACTER_ELEMENTS.get(previous_character_id))}   "
                    f"{previous_character_id.title()}"
                )
                self._set_sidebar_active(previous_label)
            else:
                self.tabs.setCurrentIndex(0)
                self._set_sidebar_active("Home")
            return

        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, ResonatorTab):
            current_id = current_widget.current_id
            self._set_sidebar_active(
                f"{self._element_icon(CHARACTER_ELEMENTS.get(current_id))}   "
                f"{current_id.title()}"
            )
        else:
            current_index = self.tabs.currentIndex()
            if 0 <= current_index < len(self._tab_titles):
                self._set_sidebar_active(self._tab_titles[current_index])

    @staticmethod
    def _normalize_character_id(value: str) -> str:
        folded = "".join(
            char for char in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", "", folded)

    @staticmethod
    def _element_icon(element: str | None) -> str:
        return {
            "Aero": "◈",
            "Glacio": "❄",
            "Electro": "✦",
            "Fusion": "♢",
            "Havoc": "◉",
            "Spectro": "✧",
        }.get(str(element), "◆")

    def open_character_tab(self) -> None:
        target = self._normalize_character_id(self.character_id_entry.text())
        character_id = next((item for item in KNOWN_CHARACTER_IDS
                             if self._normalize_character_id(item)
                             == target), None)
        if character_id is None:
            self.character_status.setText("ID inválida")
            return

        character_tab = self.character_tabs.get(character_id)
        if character_tab is None:
            character_tab = ResonatorTab(initial_id=character_id)
            self.character_tabs[character_id] = character_tab
            self.character_open_order.append(character_id)
            sources_index = self.tabs.count() - 1
            self.tabs.insertTab(sources_index,
                                character_tab,
                                character_id.title())
            label = character_id.title()
            element = CHARACTER_ELEMENTS.get(character_id)
            self.tabs.setTabText(
                sources_index,
                f"{self._element_icon(element)} {label}",
            )
            self._add_character_sidebar_button(
                character_id,
                f"{self._element_icon(element)}   {label}",
                element,
            )

        self.tabs.setCurrentWidget(character_tab)
        self._set_sidebar_active(
            f"{self._element_icon(CHARACTER_ELEMENTS.get(character_id))}   {character_id.title()}")
        self.character_status.clear()
