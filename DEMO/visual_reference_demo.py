"""Standalone visual reference demo for the Wuwa Damage Lab UI."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QWidget,
)


ROOT = Path(__file__).resolve().parent
CHARACTER_URL = "https://rackoon.com.br/images/wuwa/resonators/suisui-sprite-sm.webp"


class ReferenceDemo(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Wuwa Damage Lab | PySide6")
        self.setFixedSize(1208, 767)
        self.network = QNetworkAccessManager(self)
        self._build_ui()
        self._load_character()

    def _build_ui(self) -> None:
        self.setStyleSheet(self._qss())
        shell = QWidget()
        self.setCentralWidget(shell)
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("topHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 14, 22, 14)
        brand = QLabel("◈  Wuwa\n    Damage Lab")
        brand.setObjectName("brand")
        header_layout.addWidget(brand)
        header_layout.addStretch(1)
        header_layout.addWidget(QLabel("Character ID"))
        entry = QLineEdit("suisui")
        entry.setFixedWidth(170)
        header_layout.addWidget(entry)
        load = QPushButton("Carregar Personagem")
        load.setObjectName("primary")
        header_layout.addWidget(load)
        status = QLabel("●  Suisui carregado")
        status.setObjectName("online")
        header_layout.addWidget(status)
        shell_layout.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        sidebar = self._sidebar()
        body.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 12)
        content_layout.setSpacing(12)
        content_layout.addWidget(self._crumbs())
        content_layout.addWidget(self._banner())

        columns = QHBoxLayout()
        columns.setSpacing(14)
        columns.addWidget(self._attributes(), 1)
        columns.addWidget(self._skills(), 1)
        content_layout.addLayout(columns, 1)
        body.addWidget(content, 1)
        shell_layout.addLayout(body, 1)
        shell_layout.addWidget(self._footer())

    def _sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(184)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 22, 14, 18)
        layout.setSpacing(10)
        for text in ("⌂   Home", "♣   Teams", "◷   Histórico", "◆   Suisui", "▣   Fontes de dados"):
            button = QPushButton(text)
            button.setObjectName("navActive" if "Suisui" in text else "nav")
            layout.addWidget(button)
        layout.addSpacing(22)
        for text in ("⚙   Configurações", "ⓘ   Sobre"):
            button = QPushButton(text)
            button.setObjectName("nav")
            layout.addWidget(button)
        layout.addStretch(1)
        return sidebar

    @staticmethod
    def _crumbs() -> QLabel:
        label = QLabel("⌂   ›   <b>Suisui</b>")
        label.setObjectName("crumbs")
        return label

    def _banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("banner")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(18, 10, 24, 10)
        portrait = QLabel("Suisui")
        portrait.setObjectName("portrait")
        portrait.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        portrait.setFixedWidth(180)
        self.portrait = portrait
        layout.addWidget(portrait)
        identity = QVBoxLayout()
        identity.setSpacing(3)
        name = QLabel("Suisui")
        name.setObjectName("heroName")
        identity.addWidget(name)
        identity.addWidget(QLabel("ID: suisui"))
        badge = QLabel("◈  Aero     ★ ★ ★ ★ ★")
        badge.setObjectName("badge")
        identity.addWidget(badge)
        identity.addStretch(1)
        layout.addLayout(identity, 1)
        quote = QLabel('"O céu não é o limite."')
        quote.setObjectName("quote")
        quote.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(quote, 1)
        return banner

    @staticmethod
    def _section_title(icon: str, title: str) -> QLabel:
        label = QLabel(f"{icon}  {title}")
        label.setObjectName("sectionTitle")
        return label

    def _attributes(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.addWidget(self._section_title("▥", "Resonator / Detalhes"))
        tabs = QHBoxLayout()
        for index, text in enumerate(("▥  Atributos Base", "⚔  Arma ativa", "♣  Equipe Suportes", "⬡  Build Echos", "◇  Marcadores")):
            button = QPushButton(text)
            button.setObjectName("tabActive" if index == 0 else "tab")
            tabs.addWidget(button)
        layout.addLayout(tabs)
        values = (("♥", "Base HP", "16,712.5", "Vida base do personagem"), ("⚔", "Base ATK", "287.5", "Ataque base do personagem"), ("⬡", "Base DEF", "1,100", "Defesa base do personagem"), ("✦", "Crit Rate", "5%", "Taxa de Acerto Crítico"), ("✦", "Crit DMG", "150%", "Dano Crítico"), ("ϟ", "Max Energy", "0", "Energia máxima"))
        for icon, label, value, hint in values:
            row = QHBoxLayout()
            row.addWidget(QLabel(icon), 0)
            row.addWidget(QLabel(f"<b>{label}</b>"), 1)
            field = QLineEdit(value)
            field.setFixedWidth(170)
            row.addWidget(field)
            row.addWidget(QLabel(hint), 1)
            layout.addLayout(row)
        layout.addStretch(1)
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(QPushButton("↻  Restaurar Padrão"))
        apply = QPushButton("✓  Aplicar Alterações")
        apply.setObjectName("primary")
        actions.addWidget(apply)
        layout.addLayout(actions)
        return panel

    @staticmethod
    def _skills() -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.addWidget(ReferenceDemo._section_title("▮", "Kit / Habilidades"))
        skills = (("⚔", "Basic Attack", "Performs a series of attacks and builds the resources used by SuiSui's Stances."), ("◉", "Resonance Skill", "Switches stance and builds Cloud Breath or Floral Epistle according to the current state."), ("❧", "Forte Circuit", "Cloud Breath builds from Zephyr attacks. At 120, Awakening Spring becomes castable and resets Floral Epistle."), ("✦", "Resonance Liberation", "Consumes the available resource to enter the empowered stance and enables the next rotation sequence."), ("♣", "Intro / Outro", "Applies the active team effect and transfers the appropriate stance-based buff."))
        for index, (icon, name, description) in enumerate(skills, 1):
            card = QFrame()
            card.setObjectName("skillCard")
            card_layout = QHBoxLayout(card)
            icon_label = QLabel(icon)
            icon_label.setObjectName("skillIcon")
            card_layout.addWidget(icon_label)
            text = QVBoxLayout()
            title = QLabel(name)
            title.setObjectName("skillTitle")
            text.addWidget(title)
            body = QLabel(description)
            body.setWordWrap(True)
            text.addWidget(body)
            card_layout.addLayout(text, 1)
            number = QLabel(str(index))
            number.setObjectName("skillNumber")
            card_layout.addWidget(number)
            layout.addWidget(card)
        layout.addStretch(1)
        return panel

    @staticmethod
    def _footer() -> QFrame:
        footer = QFrame()
        footer.setObjectName("footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(18, 8, 18, 8)
        layout.addWidget(QLabel("▣  Banco de dados"))
        online = QLabel("●  Online")
        online.setObjectName("online")
        layout.addWidget(online)
        layout.addStretch(1)
        layout.addWidget(QLabel("Última atualização: 10/09/2026 21:12     ⓘ"))
        return footer

    def _load_character(self) -> None:
        reply = self.network.get(QNetworkRequest(QUrl(CHARACTER_URL)))
        reply.finished.connect(lambda: self._finish_character(reply))

    def _finish_character(self, reply: object) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(reply.readAll())
            if not pixmap.isNull():
                self.portrait.setPixmap(pixmap.scaled(170, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except (AttributeError, RuntimeError):
            pass

    @staticmethod
    def _qss() -> str:
        return """
        QMainWindow, QWidget { background: #080B18; color: #F2F0FF; font-family: 'Bahnschrift', 'Segoe UI'; font-size: 12px; }
        QFrame#topHeader { background: #0D1122; border-bottom: 1px solid #262C4F; }
        QFrame#sidebar { background: #0C1020; border-right: 1px solid #202744; }
        QFrame#footer { background: #0D1222; border-top: 1px solid #242A48; }
        QFrame#banner { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #263B7A,stop:.5 #17244A,stop:1 #131B3A); border: 1px solid #7547D9; border-radius: 8px; }
        QFrame#panel { background: #0F1428; border: 1px solid #394071; border-radius: 8px; }
        QLabel#brand { color: #F4F0FF; font-size: 16px; font-weight: 800; }
        QLabel#crumbs { color: #A8A8D5; font-size: 13px; }
        QLabel#sectionTitle { color: #F5F1FF; font-size: 16px; font-weight: 800; }
        QLabel#heroName { color: #FFFFFF; font-size: 28px; font-weight: 900; }
        QLabel#badge { color: #FFD76A; font-size: 15px; font-weight: 700; }
        QLabel#quote { color: #F0E8FF; font-size: 13px; font-style: italic; }
        QLabel#online { color: #D946EF; font-weight: 700; }
        QPushButton { background: #161D39; color: #EDEAFF; border: 1px solid #343D6D; border-radius: 7px; padding: 8px 10px; }
        QPushButton:hover { background: #24265A; border-color: #A855F7; }
        QPushButton#primary { background: #7438E6; border-color: #B77CFF; color: #FFFFFF; font-weight: 800; }
        QPushButton#nav, QPushButton#navActive { text-align: left; border: 0; padding: 10px; }
        QPushButton#navActive { background: #48209A; border-radius: 7px; color: #FFFFFF; font-weight: 800; }
        QPushButton#tab, QPushButton#tabActive { padding: 8px 7px; font-size: 10px; }
        QPushButton#tabActive { background: #7535E5; border-color: #B77CFF; color: #FFFFFF; font-weight: 800; }
        QLineEdit, QComboBox { background: #0A1022; color: #FFFFFF; border: 1px solid #394574; border-radius: 6px; padding: 7px; }
        QLineEdit:focus, QComboBox:focus { border-color: #D946EF; }
        QFrame#skillCard { background: #171E38; border: 1px solid #323D70; border-radius: 8px; }
        QLabel#skillIcon { background: #242A5A; color: #FFFFFF; border: 1px solid #5D5CE8; border-radius: 7px; padding: 12px; font-size: 22px; }
        QLabel#skillTitle { color: #DDBBFF; font-weight: 800; }
        QLabel#skillNumber { background: #3D477A; color: #FFFFFF; border-radius: 5px; padding: 8px; font-size: 15px; font-weight: 800; }
        """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReferenceDemo()
    window.show()
    raise SystemExit(app.exec())
