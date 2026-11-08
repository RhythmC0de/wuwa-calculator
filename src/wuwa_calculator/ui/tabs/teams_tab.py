"""Team persistence and orchestration around reusable team widgets."""

from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import (
    QIcon,
    QPixmap,
)
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from wuwa_calculator.data.characters_elements import CHARACTER_ELEMENTS
from wuwa_calculator.data.echoes import ECHOES_DB
from wuwa_calculator.data.element_images import (
    CHARACTER_ELEMENT_IMAGE_URLS,
    ELEMENT_IMAGE_URLS,
)
from wuwa_calculator.data.images import CHARACTER_IMAGE_FALLBACKS
from wuwa_calculator.data.team_saved_images import TEAM_SAVED_IMAGE_URLS
from wuwa_calculator.infrastructure.security_policy import (
    allows_remote_content,
)
from wuwa_calculator.storage.team_storage import load_teams, save_teams
from wuwa_calculator.ui.components.components import (
    Card,
    TitleLabel,
    apply_glow,
)
from wuwa_calculator.ui.teams.widgets import (
    SLOT_ROLES,
    CharacterBadgeWidget,
    CharacterPicker,
    EchoPicker,
    EchoPreviewIcon,
    TeamCardWidget,
    TeamSlot,
    _read_network_reply,
    apply_badge_reply,
    display_name,
    normalize_character,
)

__all__ = [
    "TeamsTab",
    "CharacterPicker",
    "EchoPicker",
    "TeamSlot",
    "EchoPreviewIcon",
    "CharacterBadgeWidget",
    "TeamCardWidget",
    "display_name",
    "normalize_character",
    "SLOT_ROLES",
]


class TeamsTab(QWidget):
    """Build teams and persist their character and Echo selections."""

    # Widgets retain child controls for their signal/slot lifecycle.
    # pylint: disable=too-many-instance-attributes
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
        # Keep ordered widget construction and painting steps together.
        # pylint: disable=too-many-locals,too-many-statements
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
        self.team_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
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
        for button in (
            self.new_button,
            self.duplicate_button,
            self.delete_button,
        ):
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
        self.status_box.addItems(
            ["Not started", "Wanted", "In progress", "Finished"]
        )
        form.addRow("Nome", self.name_entry)
        form.addRow("Status", self.status_box)
        editor_layout.addLayout(form)
        grid = QGridLayout()
        grid.setSpacing(10)
        for index, role in enumerate(SLOT_ROLES):
            slot = TeamSlot(role)
            slot.clicked.connect(
                lambda _checked=False, item=slot: self.choose_slot(item)
            )
            self.slots.append(slot)
            slot_panel = QWidget()
            slot_layout = QVBoxLayout(slot_panel)
            slot_layout.setContentsMargins(0, 0, 0, 0)
            slot_layout.addWidget(slot)
            echo_button = QPushButton("Echos 0/5")
            echo_button.setObjectName("echoButton")
            echo_button.clicked.connect(
                lambda _checked=False, item=slot: self.configure_echoes(item)
            )
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
                preview_name.setTextInteractionFlags(
                    Qt.TextInteractionFlag.NoTextInteraction
                )
                preview_row.addWidget(preview_icon)
                preview_row.addWidget(preview_name, 1)
                preview_layout.addLayout(preview_row)
                slot_previews.append((preview_icon, preview_name))
            slot_layout.addLayout(preview_layout)
            self.echo_previews.append(slot_previews)
            grid.addWidget(slot_panel, index // 2, index % 2)
        editor_layout.addLayout(grid)
        self.status_label = QLabel(
            "Selecione os personagens para montar a equipe."
        )
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
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, team in enumerate(self.teams):
            members = self._team_members(team)
            card = TeamCardWidget(
                str(team.get("name", "Equipe sem nome")), members
            )
            card.set_selected(index == self.selected_team_index)
            card.clicked.connect(
                lambda team_index=index: self.load_selected_team(team_index)
            )
            self.team_cards_layout.insertWidget(index, card)
            for badge, member in zip(card.badges, members[:3]):
                self._load_badge_image(
                    member.get("char_icon", ""), badge, "char"
                )
                self._load_badge_image(
                    member.get("weapon_icon", ""), badge, "weapon"
                )

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
                weapon_icon = (
                    str(manual_images.get("weapon", "")) or weapon_icon
                )
            fallback = CHARACTER_IMAGE_FALLBACKS.get(character_id, {})
            if isinstance(fallback, dict):
                char_icon = char_icon or str(fallback.get("char", ""))
                weapon_icon = weapon_icon or str(fallback.get("weapon", ""))
            members.append(
                {
                    "character": character_id,
                    "char_icon": char_icon,
                    "weapon_icon": weapon_icon,
                }
            )
        return members

    def _load_badge_image(
        self, source: str, badge: CharacterBadgeWidget, kind: str
    ) -> None:
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
        reply.finished.connect(
            lambda: self._finish_badge_image(reply, badge, kind, source)
        )

    def _finish_badge_image(
        self,
        reply: object,
        badge: CharacterBadgeWidget,
        kind: str,
        source: str,
    ) -> None:
        apply_badge_reply(reply, badge, kind)
        self._image_replies.pop(source, None)

    def load_selected_team(self, index: int) -> None:
        """Load the selected saved team into the editor."""
        if not 0 <= index < len(self.teams):
            return
        self.selected_team_index = index
        self._select_team_card(index)
        team = self.teams[index]
        self.name_entry.setText(str(team.get("name", "")))
        self.status_box.setCurrentText(str(team.get("status", "Not started")))
        values = [
            member["character"]
            for member in self._team_members(team)
            if member.get("character")
        ]
        stored_echoes = team.get("echoes", {})
        self.echoes_by_character = (
            {
                normalize_character(character): [
                    str(echo) for echo in echoes if str(echo) in ECHOES_DB
                ]
                for character, echoes in stored_echoes.items()
                if isinstance(stored_echoes, dict)
                and isinstance(echoes, list)
                and normalize_character(character)
            }
            if isinstance(stored_echoes, dict)
            else {}
        )
        self._set_slots(values)
        self.status_label.setText("Equipe selecionada.")

    def _select_team_card(self, index: int) -> None:
        for card_index in range(self.team_cards_layout.count() - 1):
            item = self.team_cards_layout.itemAt(card_index)
            if item is None:
                continue
            card = item.widget()
            if isinstance(card, TeamCardWidget):
                card.set_selected(card_index == index)

    def new_team(self) -> None:
        """New team."""
        self.selected_team_index = -1
        for index in range(self.team_cards_layout.count() - 1):
            item = self.team_cards_layout.itemAt(index)
            if item is None:
                continue
            card = item.widget()
            if isinstance(card, TeamCardWidget):
                card.set_selected(False)
        self.name_entry.setText("Nova equipe")
        self.status_box.setCurrentIndex(0)
        self.echoes_by_character = {}
        self._set_slots([])
        self.status_label.setText("Nova equipe pronta para montagem.")

    def choose_slot(self, slot: TeamSlot) -> None:
        """Choose slot."""
        picker = CharacterPicker(self)
        if picker.exec() == QDialog.DialogCode.Accepted:
            old_id = slot.character_id
            slot.set_character(picker.selected_id)
            if old_id != slot.character_id:
                old_echoes = self.echoes_by_character.pop(old_id, [])
                if slot.character_id:
                    self.echoes_by_character.setdefault(
                        slot.character_id, old_echoes
                    )
            self._load_slot_avatar(slot)
            self._load_element_preview(slot)
            self._refresh_echo_buttons()
            self._update_synergy()

    def configure_echoes(self, slot: TeamSlot) -> None:
        """Configure echoes."""
        if not slot.character_id:
            self.status_label.setText(
                "Escolha um personagem antes de configurar Echos."
            )
            return
        picker = EchoPicker(
            self, self.echoes_by_character.get(slot.character_id, [])
        )
        if picker.exec() == QDialog.DialogCode.Accepted:
            self.echoes_by_character[slot.character_id] = (
                picker.selected_echoes
            )
            self._refresh_echo_buttons()
            self._update_synergy()

    def _set_slots(self, characters: list[str]) -> None:
        for index, slot in enumerate(self.slots):
            slot.set_character(
                characters[index] if index < len(characters) else ""
            )
            self._load_slot_avatar(slot)
            self._load_element_preview(slot)
        self._refresh_echo_buttons()
        self._update_synergy()

    def _refresh_echo_buttons(self) -> None:
        for index, (slot, button) in enumerate(
            zip(self.slots, self.echo_buttons)
        ):
            count = (
                len(self.echoes_by_character.get(slot.character_id, []))
                if slot.character_id
                else 0
            )
            button.setText(f"Echos {count}/5")
            button.setEnabled(bool(slot.character_id))
            echo_ids = (
                self.echoes_by_character.get(slot.character_id, [])
                if slot.character_id
                else []
            )
            for preview_index, (preview_icon, preview_name) in enumerate(
                self.echo_previews[index]
            ):
                preview_icon.setPixmap(QPixmap())
                preview_icon.setText("○")
                if preview_index >= len(echo_ids):
                    preview_name.setText("Vazio")
                    continue
                echo = ECHOES_DB[echo_ids[preview_index]]
                preview_name.setText(str(echo["name"]))
                self._load_echo_preview(
                    str(echo.get("image", "")), preview_icon
                )

    def _load_echo_preview(self, url: str, target: QLabel) -> None:
        if not url or not allows_remote_content(url):
            return
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(
            lambda: self._finish_echo_preview(reply, target, url)
        )

    def _finish_echo_preview(
        self, reply: object, target: QLabel, url: str
    ) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                target.setText("")
                target.setPixmap(
                    pixmap.scaled(
                        target.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
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
        reply.finished.connect(
            lambda: self._finish_slot_avatar(reply, slot, url)
        )

    def _load_element_preview(self, slot: TeamSlot) -> None:
        target = slot.element_badge
        character_id = slot.character_id
        element = CHARACTER_ELEMENTS.get(character_id, "")
        target.clear()
        target.setText("")
        target.setProperty("element", element)
        target.style().unpolish(target)
        target.style().polish(target)
        url = CHARACTER_ELEMENT_IMAGE_URLS.get(
            character_id
        ) or ELEMENT_IMAGE_URLS.get(element, "")
        if not url or not allows_remote_content(url):
            return
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(
            lambda: self._finish_element_preview(reply, target, element, url)
        )

    def _finish_element_preview(
        self, reply: object, target: QLabel, _element: str, url: str
    ) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                target.setText("")
                target.setPixmap(
                    pixmap.scaled(
                        20,
                        20,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        except (AttributeError, RuntimeError, TypeError):
            pass
        self._image_replies.pop(url, None)

    def _finish_slot_avatar(
        self, reply: object, slot: TeamSlot, url: str
    ) -> None:
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
                target.setPixmap(
                    pixmap.scaled(
                        target.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
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
        self.active_elements.setText(
            "\n".join(
                f"{element}: {count}" for element, count in elements.items()
            )
        )
        repeated = [
            element for element, count in elements.items() if count >= 2
        ]
        bonus = (
            "Afinidade elemental: " + ", ".join(repeated)
            if repeated
            else "Mistura elemental variada"
        )
        self.team_bonus.setText(
            f"{bonus}\n{len(self._current_characters())}/3 slots ocupados"
        )
        sonatas: dict[str, int] = {}
        for echoes in self.echoes_by_character.values():
            for echo_id in echoes:
                sonata = str(ECHOES_DB[echo_id]["sonata"])
                sonatas[sonata] = sonatas.get(sonata, 0) + 1
        active = [
            (
                f"{sonata}: {count}/5 (5 peças)"
                if count >= 5
                else f"{sonata}: {count}/2 (2 peças)"
            )
            for sonata, count in sonatas.items()
            if count >= 2
        ]
        self.sonata_summary.setText(
            "Sonatas: "
            + ("\n".join(active) if active else "nenhum conjunto ativo")
        )

    def save_team(self) -> None:
        """Save team."""
        name = self.name_entry.text().strip() or "Equipe sem nome"
        team = {
            "name": name,
            "status": self.status_box.currentText(),
            "characters": [
                display_name(character_id)
                for character_id in self._current_characters()
            ],
            "echoes": deepcopy(
                {
                    character_id: echoes
                    for character_id, echoes in (
                        self.echoes_by_character.items()
                    )
                    if character_id in self._current_characters()
                }
            ),
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
        """Duplicate team."""
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
        """Delete team."""
        if not 0 <= self.selected_team_index < len(self.teams):
            return
        del self.teams[self.selected_team_index]
        save_teams(self.teams)
        self._refresh_team_list()
        self.new_team()
