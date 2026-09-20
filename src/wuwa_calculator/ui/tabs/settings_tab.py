from __future__ import annotations
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QFormLayout,
    QCheckBox,
    QSlider,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from src.wuwa_calculator.ui.components.components import TitleLabel
from src.wuwa_calculator.ui.components.components import Card
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wuwa_calculator.ui.panels.window import WuwaQtWindow


class SettingsTab(QWidget):
    def __init__(self, parent: QWidget | None = None,
                 host: QWidget | None = None) -> None:
        super().__init__(parent)
        self.host = host
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        appearance_card = Card()
        appearance_layout = QVBoxLayout(appearance_card)
        appearance_layout.setContentsMargins(20, 20, 20, 20)
        appearance_layout.addWidget(TitleLabel("Aparência e janela"))
        appearance_form = QFormLayout()
        appearance_form.setVerticalSpacing(12)

        self.background_box = QCheckBox("Usar imagem de fundo")
        self.background_box.setChecked(True)
        appearance_form.addRow("Fundo", self.background_box)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.setToolTip("Opacidade dos painéis e cards")
        appearance_form.addRow("Opacidade da interface", self.opacity_slider)

        self.accent_box = QComboBox()
        self.accent_box.addItems([
            "Ciano Tethys", "Dourado Sol", "Roxo Nécro", "Vermelho Alerta"
        ])
        appearance_form.addRow("Cor do tema", self.accent_box)

        self.confirm_exit_box = QCheckBox(
            "Confirmar antes de fechar o programa")
        appearance_layout.addLayout(appearance_form)
        layout.addWidget(appearance_card)

        wallpaper_card = Card()
        wallpaper_layout = QVBoxLayout(wallpaper_card)
        wallpaper_layout.setContentsMargins(20, 20, 20, 20)
        wallpaper_layout.addWidget(TitleLabel("Wallpaper personalizado"))
        wallpaper_info = QLabel(
            "Use uma imagem entre 1024 x 640 e 1440 x 900 px, "
            "na proporção 16:10. "
            "O tamanho ideal é 1440 x 900 px para preencher o "
            "programa sem deformar."
        )
        wallpaper_info.setObjectName("muted")
        wallpaper_info.setWordWrap(True)
        wallpaper_layout.addWidget(wallpaper_info)

        self.wallpaper_label = QLabel("Fundo padrão do programa")
        self.wallpaper_label.setObjectName("muted")
        self.wallpaper_label.setWordWrap(True)

        wallpaper_layout.addWidget(self.wallpaper_label)
        wallpaper_actions = QHBoxLayout()
        choose_wallpaper_button = QPushButton("Escolher wallpaper")
        choose_wallpaper_button.clicked.connect(self._choose_wallpaper)
        wallpaper_actions.addWidget(choose_wallpaper_button)
        reset_wallpaper_button = QPushButton("Usar fundo padrão")
        reset_wallpaper_button.clicked.connect(self._reset_wallpaper)
        wallpaper_actions.addWidget(reset_wallpaper_button)
        wallpaper_actions.addStretch(1)
        wallpaper_layout.addLayout(wallpaper_actions)
        layout.addWidget(wallpaper_card)

        data_card = Card()
        data_layout = QVBoxLayout(data_card)
        data_layout.setContentsMargins(20, 20, 20, 20)
        data_layout.addWidget(TitleLabel("Dados da sessão"))
        data_text = QLabel("Remova as abas de personagens "
                           "carregadas sem apagar arquivos salvos.")
        data_text.setObjectName("muted")
        data_layout.addWidget(data_text)
        clear_button = QPushButton("Limpar personagens carregados")
        clear_button.clicked.connect(self._clear_characters)
        data_layout.addWidget(clear_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(data_card)

        actions = QHBoxLayout()
        defaults_button = QPushButton("Restaurar padrões")
        defaults_button.clicked.connect(self._restore_defaults)
        actions.addWidget(defaults_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)

        self.background_box.toggled.connect(self._background_changed)
        self.opacity_slider.valueChanged.connect(self._interface_opacity_changed)
        self.accent_box.currentTextChanged.connect(self._accent_changed)
        self.confirm_exit_box.toggled.connect(self._confirm_exit_changed)
        self._load_preferences()

    @property
    def preferences(self) -> QSettings:
        return QSettings("Tethys", "Tethys")

    def _load_preferences(self) -> None:
        settings = self.preferences
        self.background_box.setChecked(
            settings.value("background", True, type=bool))

        self.opacity_slider.setValue(settings.value("interface_opacity", 85, type=int))
        accent = settings.value("accent_theme", "Ciano Tethys", type=str)
        index = self.accent_box.findText(accent)
        self.accent_box.setCurrentIndex(max(0, index))
        self.confirm_exit_box.setChecked(
            settings.value("confirm_exit", True, type=bool))

        wallpaper = settings.value("wallpaper", "", type=str)
        self._set_wallpaper_label(wallpaper)

    def _choose_wallpaper(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Escolher wallpaper do programa",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp);;Todos os arquivos (*)",
        )
        if not path:
            return
        size = QPixmap(path).size()
        minimum_width, minimum_height = 1024, 640
        maximum_width, maximum_height = 1440, 900
        ratio = size.width() / size.height() if size.height() else 0
        if (
            size.width() < minimum_width
            or size.height() < minimum_height
            or size.width() > maximum_width
            or size.height() > maximum_height
            or abs(ratio - 1.6) > 0.01
        ):
            QMessageBox.warning(
                self,
                "Tamanho de wallpaper inválido",
                "Escolha uma imagem entre 1024 x 640 e 1440 x 900 px, "
                "com proporção 16:10. O tamanho recomendado é 1440 x 900 px.",
            )
            return

        wallpaper = str(QUrl.fromLocalFile(path).toString())
        self.preferences.setValue("wallpaper", wallpaper)
        self.preferences.sync()
        self._set_wallpaper_label(path)
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _reset_wallpaper(self) -> None:
        self.preferences.remove("wallpaper")
        self.preferences.sync()
        self._set_wallpaper_label("")
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _set_wallpaper_label(self, wallpaper: str) -> None:
        self.wallpaper_label.setText(
            f"Wallpaper atual: {wallpaper}"
            if wallpaper
            else "Wallpaper atual: app_background_reference.png"
        )

    def _background_changed(self, enabled: bool) -> None:
        self.preferences.setValue("background", enabled)
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _interface_opacity_changed(self, value: int) -> None:
        self.preferences.setValue("interface_opacity", value)
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _accent_changed(self, accent: str) -> None:
        self.preferences.setValue("accent_theme", accent)
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

    def _confirm_exit_changed(self, enabled: bool) -> None:
        self.preferences.setValue("confirm_exit", enabled)

    def _clear_characters(self) -> None:
        window = self.host or self.window()
        if not isinstance(window, WuwaQtWindow):
            return

        for character_tab in window.character_tabs.values():
            tab_index = window.tabs.indexOf(character_tab)
            if tab_index >= 0:
                window.tabs.removeTab(tab_index)
            character_tab.deleteLater()
        window.character_tabs.clear()

        while window.character_sidebar_layout.count():
            item = window.character_sidebar_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        window.tabs.setCurrentIndex(0)
        window._set_sidebar_active("⌂   Home")

    def _restore_defaults(self) -> None:
        self.preferences.clear()
        self.background_box.setChecked(True)
        self.opacity_slider.setValue(85)
        self.accent_box.setCurrentText("Ciano Tethys")
        self.confirm_exit_box.setChecked(True)
        self._reset_wallpaper()
        window = self.host or self.window()
        if isinstance(window, WuwaQtWindow):
            window.apply_preferences()

