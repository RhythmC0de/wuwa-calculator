"""Visual team builder for the Tethys PySide6 application."""

from __future__ import annotations

import re
import sys
from copy import deepcopy
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QSize, Qt, QRectF, QUrl, Signal
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QLineEdit, QPushButton,
    QScrollArea, QVBoxLayout, QWidget, QFrame,
)

from src.wuwa_calculator.app.components import Card, TitleLabel, apply_glow
from src.wuwa_calculator.app.security_policy import allows_remote_content
from src.wuwa_calculator.data.characters_elements import CHARACTER_ELEMENTS
from src.wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS
from src.wuwa_calculator.data.echoes import ECHOES_DB
from src.wuwa_calculator.data.element_images import CHARACTER_ELEMENT_IMAGE_URLS, ELEMENT_IMAGE_URLS
from src.wuwa_calculator.data.images import CHARACTER_IMAGE_FALLBACKS
from src.wuwa_calculator.data.team_saved_images import TEAM_SAVED_IMAGE_URLS
from src.wuwa_calculator.storage.team_storage import load_teams, save_teams

SLOT_ROLES = ("Main DPS", "Suporte 1", "Suporte 2")


def _read_network_reply(reply: object) -> object:
    if (
        not getattr(reply, "isOpen", lambda: False)()
        or getattr(reply, "error", lambda: QNetworkReply.NetworkError.UnknownNetworkError)()
        != QNetworkReply.NetworkError.NoError
    ):
        return b""
    return getattr(reply, "readAll", lambda: b"")()


def display_name(character_id: str) -> str:
    return character_id.title()


def normalize_character(value: object) -> str:
    folded = re.sub(r"[^a-z0-9]+", "", str(value).casefold())
    return next(
        (
            character_id
            for character_id in KNOWN_CHARACTER_IDS
            if re.sub(r"[^a-z0-9]+", "", character_id.casefold()) == folded
        ),
        "",
    )


class CharacterPicker(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Selecionar personagem")
        self.setMinimumSize(420, 520)
        self.selected_id = ""
        layout = QVBoxLayout(self)
        layout.addWidget(TitleLabel("Escolha um personagem"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrar por nome ou ID")
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.setObjectName("characterPicker")
        layout.addWidget(self.list, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        clear_button = buttons.addButton("Remover slot", QDialogButtonBox.ButtonRole.DestructiveRole)
        choose_button = buttons.addButton("Selecionar", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.rejected.connect(self.reject)
        clear_button.clicked.connect(self._clear)
        choose_button.clicked.connect(self._choose)
        self.list.itemDoubleClicked.connect(lambda _item: self._choose())
        self.search.textChanged.connect(self._filter)
        layout.addWidget(buttons)
        self._populate()

    def _populate(self) -> None:
        for character_id in sorted(KNOWN_CHARACTER_IDS):
            item = QListWidgetItem(
                f"{display_name(character_id)}  ·  "
                f"{CHARACTER_ELEMENTS.get(character_id, 'Elemento')}"
            )
            item.setData(Qt.ItemDataRole.UserRole, character_id)
            self.list.addItem(item)

    def _filter(self, text: str) -> None:
        needle = text.casefold().strip()
        for index in range(self.list.count()):
            item = self.list.item(index)
            item.setHidden(needle not in item.text().casefold())

    def _choose(self) -> None:
        item = self.list.currentItem()
        if item is not None:
            self.selected_id = str(item.data(Qt.ItemDataRole.UserRole))
            self.accept()

    def _clear(self) -> None:
        self.selected_id = ""
        self.accept()


class EchoPicker(QDialog):
    def __init__(self, parent: QWidget, selected: list[str]) -> None:
        super().__init__(parent)
        self.setWindowTitle("Echos do personagem")
        self.setMinimumWidth(520)
        self.selectors: list[QComboBox] = []
        self.network = QNetworkAccessManager(self)
        self._image_replies: dict[str, object] = {}
        layout = QVBoxLayout(self)
        layout.addWidget(TitleLabel("Pré-seleção de Echos · 5 slots"))
        form = QFormLayout()
        options = [("", "Vazio", "")] + [
            (
                echo_id,
                f"{data['icon']}  {data['name']}  · Custo {data['cost']}  · "
                f"{data['element']} / {data['sonata']}",
                str(data.get("image", "")),
            )
            for echo_id, data in sorted(ECHOES_DB.items(), key=lambda item: str(item[1]["name"]))
        ]
        for index in range(5):
            combo = QComboBox()
            for echo_id, label, image_url in options:
                combo.addItem(label, echo_id)
                if image_url and allows_remote_content(image_url):
                    self._load_echo_icon(combo, combo.count() - 1, image_url)
            if index < len(selected):
                current = combo.findData(selected[index])
                combo.setCurrentIndex(max(0, current))
            self.selectors.append(combo)
            form.addRow(f"Echo {index + 1}", combo)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_echo_icon(self, combo: QComboBox, index: int, url: str) -> None:
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(lambda: self._finish_echo_icon(reply, combo, index, url))

    def _finish_echo_icon(self, reply: object, combo: QComboBox, index: int, url: str) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                combo.setItemIcon(index, QIcon(pixmap.scaled(QSize(32, 32), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(url, None)

    @property
    def selected_echoes(self) -> list[str]:
        return [str(combo.currentData()) for combo in self.selectors if combo.currentData()]


class TeamSlot(QPushButton):
    def __init__(self, role: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.role = role
        self.character_id = ""
        self.setObjectName("teamSlot")
        self.setMinimumSize(190, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.element_badge = QLabel(self)
        self.element_badge.setObjectName("teamElementIcon")
        self.element_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.element_badge.setFixedSize(20, 20)
        self.element_label = QLabel(self)
        self.element_label.setStyleSheet("color: #F2F0FF; background: transparent; font-size: 11px;")
        self.element_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.set_character("")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_element_row()

    def _position_element_row(self) -> None:
        self.element_label.adjustSize()
        row_width = self.element_badge.width() + 4 + self.element_label.width()
        row_x = max(0, (self.width() - row_width) // 2)
        row_y = self.height() - max(self.element_badge.height(), self.element_label.height()) - 14
        self.element_badge.move(row_x, row_y)
        self.element_label.move(row_x + self.element_badge.width() + 4, row_y)

    def set_character(self, character_id: str) -> None:
        self.character_id = character_id
        if not character_id:
            self.setText(f"+\n{self.role}\nVazio")
            self.setProperty("element", "")
            self.element_badge.hide()
            self.element_label.hide()
        else:
            element = CHARACTER_ELEMENTS.get(character_id, "")
            self.setProperty("element", element)
            self.setText(f"{display_name(character_id)}\n{self.role}")
            self.element_label.setText(element)
            self.element_badge.setProperty("element", element)
            self.element_badge.show()
            self.element_label.show()
            self.element_badge.style().unpolish(self.element_badge)
            self.element_badge.style().polish(self.element_badge)
            self._position_element_row()
        self.style().unpolish(self)
        self.style().polish(self)


class EchoPreviewIcon(QLabel):
    """Renderiza o preview do Echo dentro de uma máscara circular."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source_pixmap = QPixmap()

    def setPixmap(self, pixmap: QPixmap) -> None:
        self._source_pixmap = pixmap
        super().setPixmap(QPixmap())
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        icon_rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.setPen(QPen(QColor("#9AA3B2"), 1))
        painter.setBrush(QBrush(QColor("#202633")))
        painter.drawEllipse(icon_rect)

        if not self._source_pixmap.isNull():
            fitted = self._source_pixmap.scaled(
                int(icon_rect.width()),
                int(icon_rect.height()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            image_x = int(icon_rect.x() + (icon_rect.width() - fitted.width()) / 2)
            image_y = int(icon_rect.y() + (icon_rect.height() - fitted.height()) / 2)
            clip_path = QPainterPath()
            clip_path.addEllipse(icon_rect)
            painter.save()
            painter.setClipPath(clip_path)
            painter.drawPixmap(image_x, image_y, fitted)
            painter.restore()
            return

        empty_size = min(icon_rect.width(), icon_rect.height()) * 0.38
        empty_rect = QRectF(
            (self.width() - empty_size) / 2,
            (self.height() - empty_size) / 2,
            empty_size,
            empty_size,
        )
        painter.setPen(QPen(QColor("#E6EDF7"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(empty_rect)


class CharacterBadgeWidget(QWidget):
    """Badge circular de personagem com ícone de arma sobreposto."""

    def __init__(self, char_icon_path: str | None = None,
                 weapon_icon_path: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.char_pixmap = QPixmap(char_icon_path) if char_icon_path else QPixmap()
        self.weapon_pixmap = QPixmap(weapon_icon_path) if weapon_icon_path else QPixmap()
        self.setFixedSize(64, 64)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_pixmaps(self, char_pixmap: QPixmap | None = None,
                    weapon_pixmap: QPixmap | None = None) -> None:
        if char_pixmap is not None:
            self.char_pixmap = char_pixmap
        if weapon_pixmap is not None:
            self.weapon_pixmap = weapon_pixmap
        self.update()

    def set_icons(self, char_path: str | None, weapon_path: str | None) -> None:
        self.char_pixmap = QPixmap(char_path) if char_path else QPixmap()
        self.weapon_pixmap = QPixmap(weapon_path) if weapon_path else QPixmap()
        self.update()

    @staticmethod
    def _fit_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        return pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        avatar_rect = QRectF(2, 2, 56, 56)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(avatar_rect)

        if not self.char_pixmap.isNull():
            avatar_path = QPainterPath()
            avatar_path.addEllipse(avatar_rect)
            fitted_avatar = self._fit_pixmap(self.char_pixmap, 56)
            avatar_x = int(2 + (56 - fitted_avatar.width()) / 2)
            avatar_y = int(2 + (56 - fitted_avatar.height()) / 2)
            painter.save()
            painter.setClipPath(avatar_path)
            painter.drawPixmap(avatar_x, avatar_y, fitted_avatar)
            painter.restore()

        if not self.weapon_pixmap.isNull():
            weapon_rect = QRectF(37, 37, 22, 22)
            painter.setPen(QPen(QColor("#FFA500"), 2))
            painter.setBrush(QBrush(QColor("#1A1A1A")))
            painter.drawEllipse(weapon_rect)
            weapon_path = QPainterPath()
            weapon_path.addEllipse(weapon_rect)
            fitted_weapon = self._fit_pixmap(self.weapon_pixmap, 18)
            weapon_x = int(37 + (22 - fitted_weapon.width()) / 2)
            weapon_y = int(37 + (22 - fitted_weapon.height()) / 2)
            painter.save()
            painter.setClipPath(weapon_path)
            painter.drawPixmap(weapon_x, weapon_y, fitted_weapon)
            painter.restore()


class TeamCardWidget(QFrame):
    """Card visual de uma equipe salva, clicável para selecionar a equipe."""

    clicked = Signal()

    def __init__(self, team_name: str, members: list[dict[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("teamSavedCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#teamSavedCard {
                background-color: #2B2B2B;
                border: 1px solid #3A3A3A;
                border-radius: 16px;
            }
            QFrame#teamSavedCard:hover, QFrame#teamSavedCard[selected="true"] {
                background-color: #323232;
                border: 1px solid #FFA500;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)
        title = QLabel(team_name)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #E0E0E0; font-size: 15px; font-weight: 600;")
        layout.addWidget(title)

        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)
        badges_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badges: list[CharacterBadgeWidget] = []
        for member in members[:3]:
            badge = CharacterBadgeWidget(
                char_icon_path=member.get("char_icon"),
                weapon_icon_path=member.get("weapon_icon"),
            )
            self.badges.append(badge)
            badges_layout.addWidget(badge)
        layout.addLayout(badges_layout)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        self.setCursor(
            Qt.CursorShape.ArrowCursor if selected else Qt.CursorShape.PointingHandCursor
        )
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class TeamsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.teams = load_teams()
        self.selected_team_index = -1
        self.slots: list[TeamSlot] = []
        self.echo_buttons: list[QPushButton] = []
        self.echo_previews: list[list[tuple[QLabel, QLabel]]] = []
        self.echoes_by_character: dict[str, list[str]] = {}
        self.network = QNetworkAccessManager(self)
        self._image_replies: dict[str, object] = {}
        self._build_ui()
        self._refresh_team_list()
        self.new_team()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        sidebar = Card()
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 14, 14, 14)
        side_layout.addWidget(TitleLabel("Equipes salvas"))
        self.team_scroll = QScrollArea()
        self.team_scroll.setObjectName("teamSavedScroll")
        self.team_scroll.setWidgetResizable(True)
        self.team_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.team_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.team_cards_container = QWidget()
        self.team_cards_layout = QVBoxLayout(self.team_cards_container)
        self.team_cards_layout.setContentsMargins(2, 2, 2, 2)
        self.team_cards_layout.setSpacing(8)
        self.team_cards_layout.addStretch(1)
        self.team_scroll.setWidget(self.team_cards_container)
        side_layout.addWidget(self.team_scroll, 1)
        actions = QHBoxLayout()
        self.new_button = QPushButton("+ Nova")
        self.duplicate_button = QPushButton("Duplicar")
        self.delete_button = QPushButton("Excluir")
        self.new_button.clicked.connect(self.new_team)
        self.duplicate_button.clicked.connect(self.duplicate_team)
        self.delete_button.clicked.connect(self.delete_team)
        for button in (self.new_button, self.duplicate_button, self.delete_button):
            apply_glow(button, blur=12, opacity=100)
            actions.addWidget(button)
        side_layout.addLayout(actions)
        root.addWidget(sidebar, 1)

        editor = Card()
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(18, 16, 18, 18)
        editor_layout.addWidget(TitleLabel("Montagem de equipe"))
        form = QFormLayout()
        self.name_entry = QLineEdit()
        self.status_box = QComboBox()
        self.status_box.addItems(["Not started", "Wanted", "In progress", "Finished"])
        form.addRow("Nome", self.name_entry)
        form.addRow("Status", self.status_box)
        editor_layout.addLayout(form)
        grid = QGridLayout()
        grid.setSpacing(10)
        for index, role in enumerate(SLOT_ROLES):
            slot = TeamSlot(role)
            slot.clicked.connect(lambda _checked=False, item=slot: self.choose_slot(item))
            self.slots.append(slot)
            slot_panel = QWidget()
            slot_layout = QVBoxLayout(slot_panel)
            slot_layout.setContentsMargins(0, 0, 0, 0)
            slot_layout.addWidget(slot)
            echo_button = QPushButton("Echos 0/5")
            echo_button.setObjectName("echoButton")
            echo_button.clicked.connect(lambda _checked=False, item=slot: self.configure_echoes(item))
            self.echo_buttons.append(echo_button)
            slot_layout.addWidget(echo_button)
            preview_layout = QVBoxLayout()
            preview_layout.setContentsMargins(0, 0, 0, 0)
            preview_layout.setSpacing(1)
            slot_previews: list[tuple[QLabel, QLabel]] = []
            for _ in range(5):
                preview_row = QHBoxLayout()
                preview_row.setSpacing(4)
                preview_icon = EchoPreviewIcon()
                preview_icon.setText("○")
                preview_icon.setObjectName("echoPreviewIcon")
                preview_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                preview_icon.setFixedSize(22, 22)
                preview_name = QLabel("Vazio")
                preview_name.setObjectName("echoPreviewName")
                preview_name.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                preview_row.addWidget(preview_icon)
                preview_row.addWidget(preview_name, 1)
                preview_layout.addLayout(preview_row)
                slot_previews.append((preview_icon, preview_name))
            slot_layout.addLayout(preview_layout)
            self.echo_previews.append(slot_previews)
            grid.addWidget(slot_panel, index // 2, index % 2)
        editor_layout.addLayout(grid)
        self.status_label = QLabel("Selecione os personagens para montar a equipe.")
        self.status_label.setObjectName("muted")
        editor_layout.addWidget(self.status_label)
        self.save_button = QPushButton("Salvar equipe")
        self.save_button.clicked.connect(self.save_team)
        apply_glow(self.save_button, blur=18)
        editor_layout.addWidget(self.save_button)
        root.addWidget(editor, 2)

        synergy = Card()
        synergy_layout = QVBoxLayout(synergy)
        synergy_layout.setContentsMargins(16, 16, 16, 16)
        synergy_layout.addWidget(TitleLabel("Sinergia"))
        synergy_layout.addWidget(QLabel("Elementos ativos"))
        self.active_elements = QLabel("Nenhum elemento ativo")
        self.active_elements.setWordWrap(True)
        synergy_layout.addWidget(self.active_elements)
        synergy_layout.addSpacing(12)
        synergy_layout.addWidget(QLabel("Resumo"))
        self.team_bonus = QLabel("Bônus de equipe: aguardando composição")
        self.team_bonus.setWordWrap(True)
        synergy_layout.addWidget(self.team_bonus)
        self.sonata_summary = QLabel("Sonatas: nenhuma ativa")
        self.sonata_summary.setWordWrap(True)
        synergy_layout.addWidget(self.sonata_summary)
        synergy_layout.addStretch(1)
        root.addWidget(synergy, 1)

    def _refresh_team_list(self) -> None:
        while self.team_cards_layout.count() > 1:
            item = self.team_cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, team in enumerate(self.teams):
            members = self._team_members(team)
            card = TeamCardWidget(str(team.get("name", "Equipe sem nome")), members)
            card.set_selected(index == self.selected_team_index)
            card.clicked.connect(lambda team_index=index: self.load_selected_team(team_index))
            self.team_cards_layout.insertWidget(index, card)
            for badge, member in zip(card.badges, members[:3]):
                self._load_badge_image(member.get("char_icon", ""), badge, "char")
                self._load_badge_image(member.get("weapon_icon", ""), badge, "weapon")

    def _team_members(self, team: dict[str, object]) -> list[dict[str, str]]:
        raw_members = team.get("members", team.get("characters", []))
        if not isinstance(raw_members, list):
            return []
        members: list[dict[str, str]] = []
        for raw_member in raw_members[:3]:
            if isinstance(raw_member, dict):
                character_id = normalize_character(
                    raw_member.get("character", raw_member.get("name", ""))
                )
                char_icon = str(raw_member.get("char_icon", ""))
                weapon_icon = str(raw_member.get("weapon_icon", ""))
            else:
                character_id = normalize_character(raw_member)
                char_icon = ""
                weapon_icon = ""
            manual_images = TEAM_SAVED_IMAGE_URLS.get(character_id, {})
            if isinstance(manual_images, dict):
                char_icon = str(manual_images.get("char", "")) or char_icon
                weapon_icon = str(manual_images.get("weapon", "")) or weapon_icon
            fallback = CHARACTER_IMAGE_FALLBACKS.get(character_id, {})
            if isinstance(fallback, dict):
                char_icon = char_icon or str(fallback.get("char", ""))
                weapon_icon = weapon_icon or str(fallback.get("weapon", ""))
            members.append({
                "character": character_id,
                "char_icon": char_icon,
                "weapon_icon": weapon_icon,
            })
        return members

    def _load_badge_image(self, source: str, badge: CharacterBadgeWidget, kind: str) -> None:
        if not source:
            return
        local_pixmap = QPixmap(source)
        if not local_pixmap.isNull():
            if kind == "char":
                badge.set_pixmaps(char_pixmap=local_pixmap)
            else:
                badge.set_pixmaps(weapon_pixmap=local_pixmap)
            return
        if not allows_remote_content(source):
            return
        reply = self.network.get(QNetworkRequest(QUrl(source)))
        self._image_replies[source] = reply
        reply.finished.connect(lambda: self._finish_badge_image(reply, badge, kind, source))

    def _finish_badge_image(self, reply: object, badge: CharacterBadgeWidget,
                            kind: str, source: str) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                if kind == "char":
                    badge.set_pixmaps(char_pixmap=pixmap)
                else:
                    badge.set_pixmaps(weapon_pixmap=pixmap)
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(source, None)

    def load_selected_team(self, index: int) -> None:
        if not 0 <= index < len(self.teams):
            return
        self.selected_team_index = index
        self._select_team_card(index)
        team = self.teams[index]
        self.name_entry.setText(str(team.get("name", "")))
        self.status_box.setCurrentText(str(team.get("status", "Not started")))
        values = [member["character"] for member in self._team_members(team) if member.get("character")]
        stored_echoes = team.get("echoes", {})
        self.echoes_by_character = {
            normalize_character(character): [str(echo) for echo in echoes if str(echo) in ECHOES_DB]
            for character, echoes in stored_echoes.items()
            if isinstance(stored_echoes, dict) and isinstance(echoes, list) and normalize_character(character)
        } if isinstance(stored_echoes, dict) else {}
        self._set_slots(values)
        self.status_label.setText("Equipe selecionada.")

    def _select_team_card(self, index: int) -> None:
        for card_index in range(self.team_cards_layout.count() - 1):
            card = self.team_cards_layout.itemAt(card_index).widget()
            if isinstance(card, TeamCardWidget):
                card.set_selected(card_index == index)

    def new_team(self) -> None:
        self.selected_team_index = -1
        for index in range(self.team_cards_layout.count() - 1):
            card = self.team_cards_layout.itemAt(index).widget()
            if isinstance(card, TeamCardWidget):
                card.set_selected(False)
        self.name_entry.setText("Nova equipe")
        self.status_box.setCurrentIndex(0)
        self.echoes_by_character = {}
        self._set_slots([])
        self.status_label.setText("Nova equipe pronta para montagem.")

    def choose_slot(self, slot: TeamSlot) -> None:
        picker = CharacterPicker(self)
        if picker.exec() == QDialog.DialogCode.Accepted:
            old_id = slot.character_id
            slot.set_character(picker.selected_id)
            if old_id != slot.character_id:
                old_echoes = self.echoes_by_character.pop(old_id, [])
                if slot.character_id:
                    self.echoes_by_character.setdefault(slot.character_id, old_echoes)
            self._load_slot_avatar(slot)
            self._load_element_preview(slot)
            self._refresh_echo_buttons()
            self._update_synergy()

    def configure_echoes(self, slot: TeamSlot) -> None:
        if not slot.character_id:
            self.status_label.setText("Escolha um personagem antes de configurar Echos.")
            return
        picker = EchoPicker(self, self.echoes_by_character.get(slot.character_id, []))
        if picker.exec() == QDialog.DialogCode.Accepted:
            self.echoes_by_character[slot.character_id] = picker.selected_echoes
            self._refresh_echo_buttons()
            self._update_synergy()

    def _set_slots(self, characters: list[str]) -> None:
        for index, slot in enumerate(self.slots):
            slot.set_character(characters[index] if index < len(characters) else "")
            self._load_slot_avatar(slot)
            self._load_element_preview(slot)
        self._refresh_echo_buttons()
        self._update_synergy()

    def _refresh_echo_buttons(self) -> None:
        for index, (slot, button) in enumerate(zip(self.slots, self.echo_buttons)):
            count = len(self.echoes_by_character.get(slot.character_id, [])) if slot.character_id else 0
            button.setText(f"Echos {count}/5")
            button.setEnabled(bool(slot.character_id))
            echo_ids = self.echoes_by_character.get(slot.character_id, []) if slot.character_id else []
            for preview_index, (preview_icon, preview_name) in enumerate(self.echo_previews[index]):
                preview_icon.setPixmap(QPixmap())
                preview_icon.setText("○")
                if preview_index >= len(echo_ids):
                    preview_name.setText("Vazio")
                    continue
                echo = ECHOES_DB[echo_ids[preview_index]]
                preview_name.setText(str(echo["name"]))
                self._load_echo_preview(str(echo.get("image", "")), preview_icon)

    def _load_echo_preview(self, url: str, target: QLabel) -> None:
        if not url or not allows_remote_content(url):
            return
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(lambda: self._finish_echo_preview(reply, target, url))

    def _finish_echo_preview(self, reply: object, target: QLabel, url: str) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                target.setText("")
                target.setPixmap(pixmap.scaled(target.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(url, None)

    def _load_slot_avatar(self, slot: TeamSlot) -> None:
        character_id = slot.character_id
        image = CHARACTER_IMAGE_FALLBACKS.get(character_id, {})
        url = str(image.get("char", "")) if isinstance(image, dict) else ""
        if not url or not allows_remote_content(url):
            slot.setIcon(QIcon())
            return
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(lambda: self._finish_slot_avatar(reply, slot, url))

    def _load_element_preview(self, slot: TeamSlot) -> None:
        index = self.slots.index(slot)
        target = slot.element_badge
        character_id = slot.character_id
        element = CHARACTER_ELEMENTS.get(character_id, "")
        target.clear()
        target.setText("")
        target.setProperty("element", element)
        target.style().unpolish(target)
        target.style().polish(target)
        url = CHARACTER_ELEMENT_IMAGE_URLS.get(character_id) or ELEMENT_IMAGE_URLS.get(element, "")
        if not url or not allows_remote_content(url):
            return
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(lambda: self._finish_element_preview(reply, target, element, url))

    def _finish_element_preview(self, reply: object, target: QLabel, element: str, url: str) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                target.setText("")
                target.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(url, None)

    def _finish_slot_avatar(self, reply: object, slot: TeamSlot, url: str) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                slot.setIcon(QIcon(pixmap))
                slot.setIconSize(QSize(64, 64))
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(url, None)

    def _load_avatar(self, character_id: str, target: QLabel) -> None:
        image = CHARACTER_IMAGE_FALLBACKS.get(character_id, {})
        url = str(image.get("char", "")) if isinstance(image, dict) else ""
        if not url or not allows_remote_content(url):
            return
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(lambda: self._finish_avatar(reply, target, url))

    def _finish_avatar(self, reply: object, target: QLabel, url: str) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                target.setPixmap(pixmap.scaled(target.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                target.setText("")
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(url, None)

    def _current_characters(self) -> list[str]:
        return [slot.character_id for slot in self.slots if slot.character_id]

    def _update_synergy(self) -> None:
        elements: dict[str, int] = {}
        for character_id in self._current_characters():
            element = CHARACTER_ELEMENTS.get(character_id, "Desconhecido")
            elements[element] = elements.get(element, 0) + 1
        if not elements:
            self.active_elements.setText("Nenhum elemento ativo")
            self.team_bonus.setText("Bônus de equipe: aguardando composição")
            self.sonata_summary.setText("Sonatas: nenhuma ativa")
            return
        self.active_elements.setText("\n".join(f"{element}: {count}" for element, count in elements.items()))
        repeated = [element for element, count in elements.items() if count >= 2]
        bonus = "Afinidade elemental: " + ", ".join(repeated) if repeated else "Mistura elemental variada"
        self.team_bonus.setText(f"{bonus}\n{len(self._current_characters())}/3 slots ocupados")
        sonatas: dict[str, int] = {}
        for echoes in self.echoes_by_character.values():
            for echo_id in echoes:
                sonata = str(ECHOES_DB[echo_id]["sonata"])
                sonatas[sonata] = sonatas.get(sonata, 0) + 1
        active = [f"{sonata}: {count}/5 (5 peças)" if count >= 5 else f"{sonata}: {count}/2 (2 peças)" for sonata, count in sonatas.items() if count >= 2]
        self.sonata_summary.setText("Sonatas: " + ("\n".join(active) if active else "nenhum conjunto ativo"))

    def save_team(self) -> None:
        name = self.name_entry.text().strip() or "Equipe sem nome"
        team = {
            "name": name,
            "status": self.status_box.currentText(),
            "characters": [display_name(character_id) for character_id in self._current_characters()],
            "echoes": deepcopy({character_id: echoes for character_id, echoes in self.echoes_by_character.items() if character_id in self._current_characters()}),
        }
        if 0 <= self.selected_team_index < len(self.teams):
            self.teams[self.selected_team_index] = team
        else:
            self.teams.append(team)
            self.selected_team_index = len(self.teams) - 1
        save_teams(self.teams)
        self._refresh_team_list()
        self._select_team_card(self.selected_team_index)
        self.status_label.setText(f"Equipe '{name}' atualizada.")

    def duplicate_team(self) -> None:
        if not 0 <= self.selected_team_index < len(self.teams):
            self.status_label.setText("Selecione uma equipe para duplicar.")
            return
        source = dict(self.teams[self.selected_team_index])
        source["name"] = f"{source.get('name', 'Equipe')} (cópia)"
        self.teams.append(source)
        save_teams(self.teams)
        self._refresh_team_list()
        self._select_team_card(len(self.teams) - 1)

    def delete_team(self) -> None:
        if not 0 <= self.selected_team_index < len(self.teams):
            return
        del self.teams[self.selected_team_index]
        save_teams(self.teams)
        self._refresh_team_list()
        self.new_team()