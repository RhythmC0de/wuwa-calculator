"""PySide6 application entry point."""

from __future__ import annotations

import sys
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.ffmpeg=false")

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QObject, QSettings, Qt, QThread, QUrl, Signal
from PySide6.QtGui import (
    QDesktopServices, QIcon, QPixmap, QResizeEvent, QPainter, QPainterPath
    )
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog,
    QFormLayout, QFrame, QGraphicsBlurEffect, QHBoxLayout, QFileDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QSlider, QTabWidget, QToolButton, QVBoxLayout,
    QWidget,
    QMenu,
)

from src.wuwa_calculator.app.components import Card, TitleLabel
from src.wuwa_calculator.app.resonator_tab import ResonatorTab
from src.wuwa_calculator.app.styles import (
    accent_preset,
    application_qss,
    refresh_glows,
    wallpaper_palette,
)

ELEMENT_NAV_COLORS = {
    "Aero": ("#145A4A", "#72E6C0", "#E8FFF8", "#1E8068"),
    "Glacio": ("#285A78", "#82D8FF", "#E4F8FF", "#397A9D"),
    "Electro": ("#49356F", "#B78CFF", "#F0E8FF", "#644B91"),
    "Fusion": ("#713D2C", "#FF8A65", "#FFF0E8", "#975039"),
    "Havoc": ("#642C43", "#E85D75", "#FFE8EE", "#873B58"),
    "Spectro": ("#665522", "#FFD76A", "#FFF8D6", "#87702D"),
}
from src.wuwa_calculator.data.characters_elements import CHARACTER_ELEMENTS
from src.wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS

# Altere para um arquivo .ico ou .png quando quiser personalizar o modal.
TETHYS_CLOSE_ICON_PATH: str | None = None

# Ícone customizado para o popup de fechar (local em Assets ou URL remota)
# Deixe como arquivo local para melhor performance
TETHYS_CLOSE_ICON_URL: str | None = None
TETHYS_CLOSE_ICON_LOCAL: str | None = str(
    Path(__file__).resolve().parent.parent / "Assets" / "close_icon.png"
)


class PlaceholderTab(QWidget):
    def __init__(self, title: str,
                 description: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        card = Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.addWidget(TitleLabel(title))
        text = QLabel(description)
        text.setObjectName("muted")
        card_layout.addWidget(text)
        card_layout.addStretch(1)
        layout.addWidget(card)


class CharacterSidebarButton(QPushButton):
    close_requested = Signal()

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.close_button = QToolButton(self)
        self.close_button.setObjectName("tabClose")
        self.close_button.setText("×")
        self.close_button.setToolTip("Fechar aba")
        self.close_button.setFixedSize(22, 22)
        self.close_button.clicked.connect(self.close_requested)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.close_button.move(
            self.width() - self.close_button.width() - 5,
            (self.height() - self.close_button.height()) // 2,
        )


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


class SettingsDialog(QDialog):
    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setWindowTitle("Configurações | Tethys")
        self.setModal(True)
        self.setMinimumSize(760, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(SettingsTab(self, host=host), 1)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)


class AboutDialog(QDialog):
    VERSION = "1.4.0"

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setWindowTitle("Sobre | Tethys System")
        self.setModal(True)
        self.setMinimumSize(560, 430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(TitleLabel("Tethys System"))

        description = QLabel(
            "O Tethys System é o terminal central de Black Shores: "
            "um sistema dedicado a observar, analisar e compreender o Lamento. "
            "Nesta aplicação, seus cálculos são usados para estudar personagens, "
            "equipes, rotações e dano em Wuthering Waves."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        info = QLabel(
            f"Versão: {self.VERSION}\n"
            "Sistema: Tethys System\n"
            "Licença: MIT"
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        notes = QLabel(
            "Assim como o terminal de Black Shores, o Tethys System organiza "
            "informações para interpretar eventos complexos. Os dados do jogo "
            "são usados localmente para apoiar análises e simulações. "
            "Consulte o README para conhecer o sistema e seus recursos."
        )
        notes.setObjectName("muted")
        notes.setWordWrap(True)
        layout.addWidget(notes)
        layout.addStretch(1)

        actions = QHBoxLayout()
        readme_button = QPushButton("Abrir README")
        readme_button.clicked.connect(self._open_readme)
        actions.addWidget(readme_button)
        copy_button = QPushButton("Copiar diagnóstico")
        copy_button.clicked.connect(self._copy_diagnostic)
        actions.addWidget(copy_button)
        actions.addStretch(1)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def _open_readme(self) -> None:
        readme = Path(__file__).resolve().parent.parent / "README.txt"
        if readme.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(readme)))
            return
        QMessageBox.information(
            self, "README não encontrado",
            "O arquivo README.txt não foi encontrado.")

    def _copy_diagnostic(self) -> None:
        diagnostic = (
            f"Tethys System {self.VERSION}\n"
            f"Diretório: {Path.cwd()}"
        )
        QApplication.clipboard().setText(diagnostic)
        QMessageBox.information(self, "Diagnóstico copiado",
                                """As informações foram copiadas
                                para a área de transferência.""")


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
        
        # Tenta usar arquivo local primeiro, depois URL, depois ícone padrão
        icon_loaded = False
        
        if icon_local:
            print(f"[Dialog] Tentando arquivo local: {icon_local}")
            try:
                local_path = Path(icon_local)
                if local_path.exists():
                    icon_pixmap = QPixmap(str(local_path))
                    if not icon_pixmap.isNull():
                        # Redimensiona para ícone pequeno (64x64 mantendo proporção)
                        icon_pixmap = icon_pixmap.scaled(
                            64, 64,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        
                        # Cria máscara circular perfeita
                        circular = QPixmap(64, 64)
                        circular.fill(Qt.transparent)
                        
                        painter = QPainter(circular)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                        
                        # Desenha círculo com clipping
                        path = QPainterPath()
                        path.addEllipse(0, 0, 64, 64)
                        painter.setClipPath(path)
                        painter.drawPixmap(0, 0, icon_pixmap)
                        painter.end()
                        
                        self.setIconPixmap(circular)
                        print(f"[Dialog] Ícone local circular 64x64 carregado com sucesso")
                        icon_loaded = True
                else:
                    print(f"[Dialog] Arquivo local não encontrado: {local_path}")
            except Exception as e:
                print(f"[Dialog] Erro ao carregar arquivo local: {e}")
        
        if not icon_loaded:
            self.setIcon(QMessageBox.Icon.Warning)
            print("[Dialog] Ícone local indisponível; usando ícone padrão")
        
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
        """Baixa uma imagem de um URL, redimensiona para ícone CIRCULAR e retorna como QPixmap."""
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
                    # Redimensiona para ícone (64x64)
                    icon_pixmap = pixmap.scaled(
                        64, 64,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    
                    # Cria máscara circular perfeita
                    circular = QPixmap(64, 64)
                    circular.fill(Qt.transparent)
                    
                    painter = QPainter(circular)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    
                    # Desenha círculo com clipping
                    path = QPainterPath()
                    path.addEllipse(0, 0, 64, 64)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, icon_pixmap)
                    painter.end()
                    
                    print(f"[Dialog._fetch_icon_from_url] Ícone circular 64x64 criado")
                    return circular
            return None
        except Exception as e:
            print(f"[Dialog._fetch_icon_from_url] Erro: {e}")
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


class ImageCharacterMismatchError(ValueError):
    def __init__(self, detected_id: str, expected_id: str) -> None:
        super().__init__(
            f"A imagem foi identificada como '{detected_id}', "
            f"mas a aba aberta é '{expected_id}'."
        )
        self.detected_id = detected_id
        self.expected_id = expected_id


class ImageImportWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(dict)
    failed = Signal(object)

    def __init__(self, path: str, target_id: str) -> None:
        super().__init__()
        self.path = path
        self.target_id = target_id

    def run(self) -> None:
        try:
            self.status.emit(
                "Baixando componentes para identificar atributos..."
            )
            self.progress.emit(15)
            from src.wuwa_calculator.utils.ocr import (  # pylint: disable=import-outside-toplevel
                extract_image_data,
            )

            self.progress.emit(35)
            self.status.emit("Carregando dados de status e atributos...")
            self.progress.emit(50)
            self.status.emit("Aplicando leitura de kits e habilidades...")
            self.progress.emit(70)
            stats, detected_id = extract_image_data(self.path)
            if detected_id is not None and detected_id != self.target_id:
                raise ImageCharacterMismatchError(
                    detected_id, self.target_id
                )
            self.status.emit("Finalizando atributos, bônus e status...")
            self.progress.emit(100)
            self.finished.emit({"stats": stats, "character_id": detected_id})
        except Exception as error:  # pylint: disable=broad-except
            self.failed.emit(error)


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
            from src.wuwa_calculator.app.home_tab import HomeTab
            return HomeTab()

        def build_teams() -> QWidget:
            from src.wuwa_calculator.app.teams_tab import TeamsTab
            return TeamsTab()

        def build_history() -> QWidget:
            from src.wuwa_calculator.app.history_tab import HistoryTab
            return HistoryTab()

        def build_multimedia() -> QWidget:
            from src.wuwa_calculator.app.multimedia_tab import MultimediaTab
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


class ImportDialog(QDialog):
    def __init__(self, parent: QWidget, character_tab: ResonatorTab):
        super().__init__(parent)
        self.character_tab = character_tab

        self.setWindowTitle("Importar dados")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        title = QLabel("Importar dados de uma imagem")

        self.select_button = QPushButton("Selecionar imagem")
        self.select_button.clicked.connect(self.select_image)

        self.status_label = QLabel(
            "Selecione uma screenshot para importar os dados."
        )
        self.status_label.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()

        layout.addWidget(title)
        layout.addWidget(self.select_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        self.ocr_thread: QThread | None = None
        self.ocr_worker: ImageImportWorker | None = None

    def select_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp)"
        )

        if not path:
            return

        self.select_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("Preparando importação...")

        self.ocr_thread = QThread(self)
        self.ocr_worker = ImageImportWorker(path, self.character_tab.current_id)
        self.ocr_worker.moveToThread(self.ocr_thread)
        self.ocr_thread.started.connect(self.ocr_worker.run)
        self.ocr_worker.progress.connect(self.progress_bar.setValue)
        self.ocr_worker.status.connect(self.status_label.setText)
        self.ocr_worker.finished.connect(self._import_finished)
        self.ocr_worker.failed.connect(self._import_failed)
        self.ocr_worker.finished.connect(self.ocr_thread.quit)
        self.ocr_worker.failed.connect(self.ocr_thread.quit)
        self.ocr_thread.finished.connect(self._clear_import_worker)
        self.ocr_thread.start()

    def _import_finished(self, result: dict) -> None:
        self.select_button.setEnabled(True)
        stats = result.get("stats", {})
        if stats:
            self.character_tab.apply_imported_stats(stats)
            message = "Stats extraídos:\n" + "\n".join(
                f"{key}: {value}" for key, value in stats.items())
            self.status_label.setText("Importação concluída.")
            QMessageBox.information(self, "Dados importados", message)
            self.accept()
            return

        message = (
            "Não foi possível encontrar informações na imagem.\n\n"
            "Verifique se a screenshot contém os atributos do personagem."
        )
        self.status_label.setText(message)
        QMessageBox.critical(self, "Nenhum dado encontrado", message)

    def _import_failed(self, error: object) -> None:
        self.select_button.setEnabled(True)
        if isinstance(error, FileNotFoundError):
            message = "Arquivo não encontrado."
            title = "Erro ao importar"
        elif isinstance(error, ImageCharacterMismatchError):
            message = (
                f"Esta imagem pertence a '{error.detected_id}', mas a aba "
                f"aberta é '{error.expected_id}'. Carregue a ID correta "
                "antes de importar esta build card."
            )
            title = "Personagem incompatível"
        elif isinstance(error, (OSError, ValueError)):
            message = (
                "Não foi possível ler a imagem. Verifique se o arquivo é "
                "uma imagem válida e tente novamente."
            )
            title = "Erro ao importar"
        elif isinstance(error, ImportError):
            message = (
                "O recurso de ler imagens não está disponível. "
                "Uma dependência necessária não está instalada."
            )
            title = "Recurso indisponível"
        elif isinstance(error, RuntimeError):
            message = (
                "Não foi possível processar a imagem. Tente novamente "
                "ou utilize outra imagem."
            )
            title = "Erro ao processar"
        else:
            message = (
                "Ocorreu um erro inesperado ao processar a imagem. "
                "Se o problema persistir, reporte o erro."
            )
            title = "Erro inesperado"

        print(f"[Importação] {type(error).__name__}: {error}")
        self.status_label.setText(message)
        QMessageBox.critical(self, title, message)

    def _clear_import_worker(self) -> None:
        if self.ocr_worker is not None:
            self.ocr_worker.deleteLater()
        if self.ocr_thread is not None:
            self.ocr_thread.deleteLater()
        self.ocr_worker = None
        self.ocr_thread = None


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    settings = QSettings("Tethys", "Tethys")
    background = settings.value("background", True, type=bool)
    wallpaper = settings.value("wallpaper", "", type=str)
    interface_opacity = settings.value("interface_opacity", 85, type=int)
    accent_theme = settings.value("accent_theme", "Ciano Tethys", type=str)
    app.setStyleSheet(application_qss(
        show_background=background,
        wallpaper=wallpaper,
        interface_opacity=interface_opacity,
        accent_theme=accent_theme,
    ))
    window = WuwaQtWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
