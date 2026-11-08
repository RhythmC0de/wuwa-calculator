"""Visual team builder for the Tethys PySide6 application."""

from __future__ import annotations

import re

from PySide6.QtCore import QRectF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wuwa_calculator.data.characters_elements import CHARACTER_ELEMENTS
from wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS
from wuwa_calculator.data.echoes import ECHOES_DB
from wuwa_calculator.infrastructure.security_policy import (
    allows_remote_content,
)
from wuwa_calculator.ui.components.components import (
    TitleLabel,
)
from wuwa_calculator.ui.network import read_reply_bytes as _read_network_reply

SLOT_ROLES = ("Main DPS", "Suporte 1", "Suporte 2")


def display_name(character_id: str) -> str:
    """Return the display label for a canonical character ID."""
    return character_id.title()


def normalize_character(value: object) -> str:
    """Normalize character."""
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
    """Search and select a character for a team slot."""

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
        clear_button = buttons.addButton(
            "Remover slot", QDialogButtonBox.ButtonRole.DestructiveRole
        )
        choose_button = buttons.addButton(
            "Selecionar", QDialogButtonBox.ButtonRole.AcceptRole
        )
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
    """Select Echo equipment and its associated bonuses."""

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
                (
                    f"{data['icon']}  {data['name']}  · Custo {data['cost']} "
                    f" · {data['element']} / {data['sonata']}"
                ),
                str(data.get("image", "")),
            )
            for echo_id, data in sorted(
                ECHOES_DB.items(), key=lambda item: str(item[1]["name"])
            )
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
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_echo_icon(self, combo: QComboBox, index: int, url: str) -> None:
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(
            lambda: self._finish_echo_icon(reply, combo, index, url)
        )

    def _finish_echo_icon(
        self, reply: object, combo: QComboBox, index: int, url: str
    ) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                combo.setItemIcon(
                    index,
                    QIcon(
                        pixmap.scaled(
                            QSize(32, 32),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    ),
                )
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(url, None)

    @property
    def selected_echoes(self) -> list[str]:
        """Return the selected echoes."""
        return [
            str(combo.currentData())
            for combo in self.selectors
            if combo.currentData()
        ]


class TeamSlot(QPushButton):
    """Represent a character assigned to one team role."""

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
        self.element_label.setStyleSheet(
            "color: #F2F0FF; background: transparent; font-size: 11px;"
        )
        self.element_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self.set_character("")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_element_row()

    def _position_element_row(self) -> None:
        self.element_label.adjustSize()
        row_width = self.element_badge.width() + 4 + self.element_label.width()
        row_x = max(0, (self.width() - row_width) // 2)
        row_y = (
            self.height()
            - max(self.element_badge.height(), self.element_label.height())
            - 14
        )
        self.element_badge.move(row_x, row_y)
        self.element_label.move(row_x + self.element_badge.width() + 4, row_y)

    def set_character(self, character_id: str) -> None:
        """Set character."""
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

    def paintEvent(self, _event) -> None:
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
            image_x = int(
                icon_rect.x() + (icon_rect.width() - fitted.width()) / 2
            )
            image_y = int(
                icon_rect.y() + (icon_rect.height() - fitted.height()) / 2
            )
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

    def __init__(
        self,
        char_icon_path: str | None = None,
        weapon_icon_path: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.char_pixmap = (
            QPixmap(char_icon_path) if char_icon_path else QPixmap()
        )
        self.weapon_pixmap = (
            QPixmap(weapon_icon_path) if weapon_icon_path else QPixmap()
        )
        self.setFixedSize(64, 64)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_pixmaps(
        self,
        char_pixmap: QPixmap | None = None,
        weapon_pixmap: QPixmap | None = None,
    ) -> None:
        """Replace the supplied character and weapon artwork."""
        if char_pixmap is not None:
            self.char_pixmap = char_pixmap
        if weapon_pixmap is not None:
            self.weapon_pixmap = weapon_pixmap
        self.update()

    def set_icons(
        self, char_path: str | None, weapon_path: str | None
    ) -> None:
        """Load character and weapon artwork from the supplied paths."""
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

    def paintEvent(self, _event) -> None:
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

    def __init__(
        self,
        team_name: str,
        members: list[dict[str, str]],
        parent: QWidget | None = None,
    ) -> None:
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
        title.setStyleSheet(
            "color: #E0E0E0; font-size: 15px; font-weight: 600;"
        )
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
        """Update the card selection state and refresh its style."""
        self.setProperty("selected", "true" if selected else "false")
        self.setCursor(
            Qt.CursorShape.ArrowCursor
            if selected
            else Qt.CursorShape.PointingHandCursor
        )
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


def apply_badge_reply(
    reply: object, badge: CharacterBadgeWidget, kind: str
) -> None:
    """Decode artwork and replace the character or weapon in a team badge."""
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
