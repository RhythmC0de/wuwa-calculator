"""Native PySide6 Resonator detail screen backed by local character databases."""

# * EDITAVEL: esta tela monta banner, atributos, arma, habilidades e calculo de dano.
# ? O elemento vem de data/characters_elements.py e controla badge, card e glow.

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Any

# PySide6 is provided by the application's runtime environment; keep static
# analyzers from flagging the optional GUI dependency when it is not installed.
from PySide6.QtCore import Qt, QUrl  # type: ignore[import-not-found]  # pylint: disable=import-error
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget,
)

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The application supports direct execution, so local imports depend on the
# path adjustment above.
# pylint: disable=wrong-import-position
from src.wuwa_calculator.app.backend_adapter import calculate_character_damage
from src.wuwa_calculator.app.components import Card, TitleLabel
from src.wuwa_calculator.app.styles import apply_element_glow, apply_glow
from src.wuwa_calculator.data.characters_elements import CHARACTER_ELEMENTS
from src.wuwa_calculator.data.characters_kits import CHARACTER_KITS_DB, MANUAL_CHARACTER_KITS
from src.wuwa_calculator.data.characters_quotes import CHARACTER_QUOTES
from src.wuwa_calculator.data.characters_stats import CHARACTER_STATS_DB
from src.wuwa_calculator.data.images import CHARACTER_IMAGE_FALLBACKS
from src.wuwa_calculator.data.weapons import MANUAL_WEAPONS, _LOCAL_KIT_WEAPON_NAMES
from src.wuwa_calculator.app.security_policy import allows_local_image, allows_remote_content


def _read_network_reply(reply: object) -> bytes:
    if not isinstance(reply, QNetworkReply):
        return b""
    if reply.error() != QNetworkReply.NetworkError.NoError:
        return b""
    return bytes(reply.readAll())


class ResonatorTab(QWidget):
    """Two-column character detail view using only bundled local data."""

    def __init__(self, parent: QWidget | None = None, initial_id: str | None = None) -> None:
        super().__init__(parent)
        self.current_id = ""
        self.language = "PT-BR"
        self.network = QNetworkAccessManager(self)
        self._image_replies: dict[str, object] = {}
        self._element_glow_widgets: list[tuple[QWidget, float, int]] = []
        self._build_ui()
        self.current_id = initial_id or "suisui"
        self._render_character(self.current_id)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.top_banner_card = QFrame()
        self.top_banner_card.setObjectName("topBanner")
        self.top_banner_card.setFixedHeight(170)
        self.top_banner_card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.top_banner_card.setStyleSheet(
            "QFrame#topBanner {"
            "border: 1px solid #6FEAFF;"
            "border-radius: 10px;"
            "background: transparent;"
            "}"
        )
        self._element_glow_widgets.append((self.top_banner_card, 30, 125))
        banner_layout = QHBoxLayout(self.top_banner_card)
        banner_layout.setContentsMargins(42, 10, 42, 10)
        banner_layout.setSpacing(10)
        self.character_image = QLabel("Sem imagem")
        self.character_image.setObjectName("bannerPortrait")
        self.character_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.character_image.setFixedSize(105, 105)
        banner_layout.addWidget(self.character_image, 0, Qt.AlignmentFlag.AlignVCenter)
        banner_identity = QVBoxLayout()
        banner_identity.setSpacing(4)
        self.character_name = QLabel("--")
        self.character_name.setObjectName("bannerName")
        self.element_badge = QLabel("Elemento: --")
        self.element_badge.setObjectName("bannerBadge")
        self.rarity_label = QLabel("★★★★★")
        self.rarity_label.setObjectName("bannerRarity")
        banner_identity.addWidget(self.character_name)
        banner_identity.addSpacing(8)
        banner_identity.addWidget(self.element_badge)
        banner_identity.addWidget(self.rarity_label)
        banner_identity.addStretch(1)
        banner_layout.addLayout(banner_identity, 1)
        self.character_quote = QLabel("")
        self.character_quote.setObjectName("bannerQuote")
        self.character_quote.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.character_quote.setWordWrap(True)
        self.character_quote.setMinimumWidth(240)
        self.character_quote.setMaximumWidth(300)
        banner_layout.addWidget(self.character_quote, 1)
        columns = QHBoxLayout()
        columns.setSpacing(14)

        left = Card()
        self._element_glow_widgets.append((left, 24, 180))
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.addWidget(TitleLabel("Resonator / Detalhes"))

        self.controls = QTabWidget()
        attributes = QWidget()
        attributes_layout = QGridLayout(attributes)
        attributes_layout.setContentsMargins(8, 8, 8, 8)
        attributes_layout.setHorizontalSpacing(6)
        attributes_layout.setVerticalSpacing(14)
        attributes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stat_labels: dict[str, QLineEdit] = {}
        attribute_hints = {
            "Base HP": ("♥", "Vida base do personagem"),
            "Base ATK": ("⚔", "Ataque base do personagem"),
            "Base DEF": ("⬡", "Defesa base do personagem"),
            "Crit Rate": ("✦", "Taxa de Acerto Crítico"),
            "Crit DMG": ("✦", "Dano Crítico"),
            "Max Energy": ("ϟ", "Energia máxima"),
        }
        for row, key in enumerate(("Base HP", "Base ATK", "Base DEF", "Crit Rate", "Crit DMG", "Max Energy")):
            value = QLineEdit("--")
            value.setObjectName("resonatorStat")
            value.setFixedWidth(170)
            self.stat_labels[key] = value
            icon, hint = attribute_hints[key]
            attributes_layout.addWidget(QLabel(icon), row, 0)
            attributes_layout.addWidget(QLabel(f"<b>{key}</b>"), row, 1)
            attributes_layout.addWidget(value, row, 2)
            attributes_layout.addWidget(QLabel(hint), row, 3)
        self.element_box = QComboBox()
        self.element_box.addItems(["Aero", "Glacio", "Electro", "Fusion", "Havoc", "Spectro"])
        attributes_layout.addWidget(QLabel("◉"), 6, 0)
        attributes_layout.addWidget(QLabel("<b>Elemento</b>"), 6, 1)
        attributes_layout.addWidget(self.element_box, 6, 2, 1, 1)
        attributes_layout.addWidget(QLabel("Elemento do personagem"), 6, 3)
        self.skill_type_box = QComboBox()
        self.skill_type_box.addItems(["Basic Attack", "Resonance Skill", "Forte Circuit", "Resonance Liberation"])
        attributes_layout.addWidget(QLabel("✣"), 7, 0)
        attributes_layout.addWidget(QLabel("<b>Tipo de Habilidade</b>"), 7, 1)
        attributes_layout.addWidget(self.skill_type_box, 7, 2, 1, 1)
        attributes_layout.addWidget(QLabel("Habilidade principal"), 7, 3)
        attributes_layout.setColumnStretch(3, 1)
        self.controls.addTab(attributes, "Atributos Base")

        weapon = QWidget()
        weapon_layout = QVBoxLayout(weapon)
        self.weapon_name = QLabel("--")
        self.weapon_name.setObjectName("metricValue")
        self.weapon_text = QLabel("--")
        self.weapon_text.setWordWrap(True)
        self.weapon_text.setTextFormat(Qt.TextFormat.RichText)
        self.weapon_passive_text = ""
        language_row = QHBoxLayout()
        language_row.addWidget(QLabel("Idioma"))
        self.language_box = QComboBox()
        self.language_box.addItems(["PT-BR", "EN"])
        language_row.addWidget(self.language_box)
        language_row.addStretch(1)
        weapon_layout.addLayout(language_row)
        weapon_layout.addWidget(self.weapon_name)
        self.weapon_image = QLabel("Sem imagem")
        self.weapon_image.setObjectName("portrait")
        self.weapon_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weapon_image.setMinimumSize(0, 0)
        self.weapon_image.setMaximumSize(320, 220)
        self.weapon_image.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        weapon_layout.addWidget(self.weapon_image)
        weapon_layout.addWidget(self.weapon_text)
        weapon_layout.addStretch(1)
        self.controls.addTab(weapon, "Arma ativa")
        supports = QWidget()
        supports_layout = QFormLayout(supports)
        self.supports_entry = QLineEdit("Nenhum suporte configurado")
        self.supports_bonus_entry = QLineEdit("0%")
        self.supports_passive_entry = QLineEdit("Nenhuma passiva de suporte configurada")
        supports_layout.addRow(QLabel("Composição de suportes"), self.supports_entry)
        supports_layout.addRow(QLabel("Bônus de suporte"), self.supports_bonus_entry)
        supports_layout.addRow(QLabel("Passivas de suporte"), self.supports_passive_entry)
        self.controls.addTab(supports, "Equipe Suportes")

        build = QWidget()
        build_layout = QFormLayout(build)
        self.echoes_entry = QLineEdit("Nenhum Echo configurado")
        self.echoes_bonus_entry = QLineEdit("0%")
        self.echoes_passive_entry = QLineEdit("Nenhuma passiva de Echo configurada")
        build_layout.addRow(QLabel("Echos equipados"), self.echoes_entry)
        build_layout.addRow(QLabel("Bônus dos Echos"), self.echoes_bonus_entry)
        build_layout.addRow(QLabel("Passivas dos Echos"), self.echoes_passive_entry)
        self.controls.addTab(build, "Build Echos")

        markers = QWidget()
        markers_layout = QVBoxLayout(markers)
        marker_text = QLabel("Marcadores temporais, condições e eventos da rotação.")
        marker_text.setObjectName("muted")
        marker_text.setWordWrap(True)
        markers_layout.addWidget(marker_text)
        markers_layout.addStretch(1)
        self.controls.addTab(markers, "Marcadores")
        self._build_damage_tab()
        self.controls.tabBar().hide()
        tab_switcher = QWidget()
        tab_grid = QGridLayout(tab_switcher)
        tab_grid.setContentsMargins(0, 0, 0, 4)
        tab_grid.setHorizontalSpacing(6)
        tab_grid.setVerticalSpacing(6)
        for index in range(self.controls.count()):
            tab_button = QPushButton(self.controls.tabText(index))
            tab_button.setObjectName("resonatorTabButton")
            tab_button.clicked.connect(
                lambda _checked=False, tab_index=index: self.controls.setCurrentIndex(tab_index)
            )
            row, column = divmod(index, 3)
            tab_grid.addWidget(tab_button, row, column)
        self.controls.currentChanged.connect(self._refresh_control_tab_buttons)
        self._control_tab_buttons = list(tab_switcher.findChildren(QPushButton))
        self._refresh_control_tab_buttons(0)
        left_layout.addWidget(tab_switcher)
        left_layout.addWidget(self.controls, 1)
        columns.addWidget(left, 1)

        right = QVBoxLayout()
        right.setSpacing(14)
        right.addWidget(self.top_banner_card, 0)
        kit = Card()
        self._element_glow_widgets.append((kit, 24, 180))
        kit_layout = QVBoxLayout(kit)
        kit_layout.setContentsMargins(16, 16, 16, 16)
        kit_layout.addWidget(TitleLabel("KIT / HABILIDADES"))
        self.kit_scroll = QScrollArea()
        self.kit_scroll.setWidgetResizable(True)
        self.kit_container = QWidget()
        self.kit_layout = QVBoxLayout(self.kit_container)
        self.kit_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.kit_scroll.setWidget(self.kit_container)
        kit_layout.addWidget(self.kit_scroll, 1)
        right.addWidget(kit, 2)
        columns.addLayout(right, 1)
        root.addLayout(columns, 1)

        self.language_box.currentTextChanged.connect(self._set_language)
        self.element_box.currentTextChanged.connect(
            self._element_changed
        )

    def _refresh_control_tab_buttons(self, active_index: int) -> None:
        for index, button in enumerate(self._control_tab_buttons):
            button.setProperty("active", index == active_index)
            button.style().unpolish(button)
            button.style().polish(button)

    def _element_changed(self, element: str) -> None:
        self.element_badge.setText(f"{self._element_icon(element)} {element}")
        self.element_badge.setProperty("element", element)
        self.element_badge.style().unpolish(self.element_badge)
        self.element_badge.style().polish(self.element_badge)
        for widget, blur, opacity in self._element_glow_widgets:
            apply_element_glow(widget, element, blur=blur, opacity=opacity)
        apply_element_glow(self.character_image, element, blur=12, opacity=85)
        apply_element_glow(self.weapon_image, element, blur=10, opacity=70)

    @staticmethod
    def _element_icon(element: str) -> str:
        return {
            "Aero": "◈",
            "Glacio": "❄",
            "Electro": "✦",
            "Fusion": "♢",
            "Havoc": "◉",
            "Spectro": "✧",
        }.get(element, "✧")

    def _build_damage_tab(self) -> None:
        tab = QWidget()
        outer_layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        layout.addWidget(TitleLabel("Cálculo de dano"))
        formula_box = QFrame()
        formula_box.setObjectName("damageFormulaBox")
        formula_layout = QVBoxLayout(formula_box)
        formula_layout.setContentsMargins(12, 8, 12, 8)
        formula = QLabel(
            "Dano = (ATK Total x Mod. Habilidade) x (1 + soma dos bônus) "
            "x Mult. Crítico x Fator de Defesa x Fator de Resistência"
        )
        formula.setObjectName("damageFormula")
        formula.setWordWrap(True)
        formula_layout.addWidget(formula)
        layout.addWidget(formula_box)

        self.damage_fields: dict[str, QDoubleSpinBox | QSpinBox] = {}
        groups = (
            ("ATACANTE", (
                ("attack_total", "ATK Total", 1500.0, 0.0, 99999.0),
                ("skill_modifier", "Mod. Habilidade (%)", 120.0, 0.0, 99999.0),
                ("damage_bonus", "Soma Bônus de Dano (%)", 20.0, 0.0, 99999.0),
                ("crit_multiplier", "Mult. Crítico", 2.5, 0.0, 999.0),
            )),
            ("INIMIGO / DEFESA", (
                ("defense_factor", "Fator de Defesa", 0.8, 0.0, 10.0),
                ("resistance_factor", "Fator de Resistência", 1.0, 0.0, 10.0),
            )),
            ("DURAÇÃO & EXECUÇÃO", (
                ("duration", "Duração (s)", 10.0, 0.1, 99999.0),
                ("hits", "Hits", 1, 1, 999),
                ("casts", "Casts", 1, 1, 999),
            )),
        )
        groups_layout = QGridLayout()
        groups_layout.setHorizontalSpacing(10)
        groups_layout.setVerticalSpacing(10)
        for group_index, (title, definitions) in enumerate(groups):
            group = QFrame()
            group.setObjectName("damageInputGroup")
            group_layout = QGridLayout(group)
            group_layout.setContentsMargins(10, 8, 10, 10)
            group_layout.setHorizontalSpacing(8)
            group_layout.setVerticalSpacing(5)
            heading = QLabel(title)
            heading.setObjectName("damageGroupTitle")
            group_layout.addWidget(heading, 0, 0, 1, 2)
            for row, (key, field_label, value, minimum, maximum) in enumerate(definitions, 1):
                label = QLabel(field_label)
                label.setObjectName("damageInputLabel")
                group_layout.addWidget(label, row, 0)
                field = QSpinBox() if key in {"hits", "casts"} else QDoubleSpinBox()
                field.setRange(minimum, maximum)
                field.setValue(value)
                if isinstance(field, QDoubleSpinBox):
                    field.setDecimals(2)
                field.setObjectName("damageInput")
                self.damage_fields[key] = field
                group_layout.addWidget(field, row, 1)
            groups_layout.addWidget(group, group_index // 2, group_index % 2)
        layout.addLayout(groups_layout)

        self.calculate_button = QPushButton("⚡  Calcular dano desta ID")
        self.calculate_button.setObjectName("damageCalculateButton")
        self.calculate_button.clicked.connect(self.calculate_character_damage)
        apply_glow(self.calculate_button, blur=18)
        layout.addWidget(self.calculate_button)

        results = QHBoxLayout()
        self.damage_stat_labels: dict[str, QLabel] = {}
        for key, title in (("hit", "DANO BASE / HIT"), ("total", "DANO TOTAL"), ("dps", "DPS ESTIMADO")):
            card = QFrame()
            card.setObjectName("damageOutputCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 9, 12, 9)
            title_label = QLabel(title)
            title_label.setObjectName("damageOutputTitle")
            value_label = QLabel("--")
            value_label.setObjectName("damageOutputValue")
            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            self.damage_stat_labels[key] = value_label
            results.addWidget(card)
        layout.addLayout(results)

        self.damage_result = QLabel("Dano: -- | Total: -- | DPS: --")
        self.damage_result.setVisible(False)
        layout.addWidget(self.damage_result)
        self.damage_details = QLabel("Execute o cálculo para ver a composição completa usada.")
        self.damage_details.setWordWrap(True)
        self.damage_details.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.damage_details)
        layout.addStretch(1)
        self.controls.addTab(tab, "Relatorio DPS")

    def calculate_character_damage(self) -> None:
        values = {key: field.value() for key, field in self.damage_fields.items()}
        result = calculate_character_damage(**values)
        self.damage_stat_labels["hit"].setText(f"{result.damage_per_hit:,.0f}")
        self.damage_stat_labels["total"].setText(f"{result.total_damage:,.0f}")
        self.damage_stat_labels["dps"].setText(f"{result.dps:,.0f}")
        self.damage_result.setText(
            f"Dano: {result.damage_per_hit:,.2f} | "
            f"Total: {result.total_damage:,.2f} | DPS: {result.dps:,.2f}"
        )
        skill_factor = values["skill_modifier"] / 100.0
        bonus_multiplier = 1.0 + values["damage_bonus"] / 100.0
        base_value = values["attack_total"] * skill_factor
        after_bonus = base_value * bonus_multiplier
        after_critical = after_bonus * values["crit_multiplier"]
        after_defense = after_critical * values["defense_factor"]
        escape = html.escape
        kit = CHARACTER_KITS_DB.get(self.current_id) or MANUAL_CHARACTER_KITS.get(self.current_id) or {}
        kit_passive = str(kit.get("weapon_passive", "Passiva não cadastrada"))
        weapon_passive = self.weapon_passive_text or kit_passive
        self.damage_details.setText(
            "<b>Modelo utilizado</b><br>"
            "Dano = (ATK Total x Mod. Habilidade) x (1 + soma dos bônus) x "
            "Mult. Crítico x Fator de Defesa x Fator de Resistência<br><br>"
            f"<b>Composição usada</b><br>Personagem: {escape(self.character_name.text())} "
            f"(ID: {escape(self.current_id)})<br>"
            f"Elemento: {escape(self.element_box.currentText())}<br>"
            f"Habilidade: {escape(self.skill_type_box.currentText())}<br>"
            f"Arma: {escape(self.weapon_name.text())}<br>"
            f"Passiva da arma: {escape(weapon_passive)}<br>"
            f"Suportes: {escape(self.supports_entry.text())}<br>"
            f"Bônus de suporte: {escape(self.supports_bonus_entry.text())}<br>"
            f"Passivas de suporte: {escape(self.supports_passive_entry.text())}<br>"
            f"Echos: {escape(self.echoes_entry.text())}<br>"
            f"Bônus dos Echos: {escape(self.echoes_bonus_entry.text())}<br>"
            f"Passivas dos Echos: {escape(self.echoes_passive_entry.text())}<br><br>"
            "<b>Etapas numéricas</b><br>"
            f"ATK Total: {values['attack_total']:,.2f}<br>"
            f"Mod. Habilidade: {values['skill_modifier']:,.2f}% (fator {skill_factor:,.4f})<br>"
            f"ATK x habilidade: {base_value:,.2f}<br>"
            f"Bônus somados: {values['damage_bonus']:,.2f}% (multiplicador {bonus_multiplier:,.4f})<br>"
            f"Após bônus: {after_bonus:,.2f}<br>"
            f"Mult. Crítico: {values['crit_multiplier']:,.4f} -> {after_critical:,.2f}<br>"
            f"Fator de Defesa: {values['defense_factor']:,.4f} -> {after_defense:,.2f}<br>"
            f"Fator de Resistência: {values['resistance_factor']:,.4f} -> {result.damage_per_hit:,.2f}<br>"
            f"Hits: {values['hits']} | Casts: {values['casts']} | Duração: {values['duration']:,.2f}s<br>"
            f"Total calculado: {result.total_damage:,.2f} | DPS: {result.dps:,.2f}"
        )

    def _render_character(self, character_id: str) -> None:
        display_name = character_id.title()
        self.character_name.setText(display_name)
        element = CHARACTER_ELEMENTS.get(character_id)
        if element:
            self.element_box.setCurrentText(element)
        current_element = self.element_box.currentText()
        self.element_badge.setText(f"{self._element_icon(current_element)} {current_element}")
        self.element_badge.setProperty("element", current_element)
        self.element_badge.style().unpolish(self.element_badge)
        self.element_badge.style().polish(self.element_badge)
        apply_element_glow(self.character_image, current_element, blur=12, opacity=85)
        apply_element_glow(self.weapon_image, current_element, blur=10, opacity=70)
        quotes = CHARACTER_QUOTES.get(character_id, ())
        self.character_quote.setText(" / ".join(quotes))
        stats = CHARACTER_STATS_DB.get(character_id, {})
        for key, label in self.stat_labels.items():
            label.setText(str(stats.get(key, "--")))

        kit = CHARACTER_KITS_DB.get(character_id) or MANUAL_CHARACTER_KITS.get(character_id) or {}
        team_buffs = kit.get("team_buffs", []) if isinstance(kit, dict) else []
        personal_buffs = kit.get("personal_buffs", []) if isinstance(kit, dict) else []
        if team_buffs:
            self.supports_bonus_entry.setText(", ".join(f"{name}: {value}%" for name, value in team_buffs))
        if personal_buffs:
            self.supports_passive_entry.setText(", ".join(f"{name}: {value}%" for name, value in personal_buffs))
        weapon_name = str(_LOCAL_KIT_WEAPON_NAMES.get(character_id, kit.get("weapon_name", "Arma não cadastrada")))
        manual_weapon = MANUAL_WEAPONS.get(character_id, {})
        self.weapon_name.setText(str(manual_weapon.get("name", weapon_name)))
        self._render_weapon(manual_weapon, kit)
        self._render_kit(kit)
        fallback = CHARACTER_IMAGE_FALLBACKS.get(character_id, {})
        self._load_image(str(fallback.get("char", "")), self.character_image, "Sem imagem")
        self._load_image(str(fallback.get("weapon", "")), self.weapon_image, "Sem imagem")

    def apply_imported_stats(self, stats: dict[str, float]) -> None:
        """Aplica na aba os atributos reconhecidos de uma imagem."""
        field_map = {
            "hp": "Base HP",
            "atk": "Base ATK",
            "def": "Base DEF",
            "crit_rate": "Crit Rate",
            "crit_dmg": "Crit DMG",
        }
        percent_fields = {"Crit Rate", "Crit DMG"}
        for source_key, field_key in field_map.items():
            value = stats.get(source_key)
            if value is None:
                continue
            suffix = "%" if field_key in percent_fields else ""
            self.stat_labels[field_key].setText(f"{value:g}{suffix}")

        attack = stats.get("atk")
        if attack is not None and "attack_total" in self.damage_fields:
            self.damage_fields["attack_total"].setValue(attack)

    @staticmethod
    def _clean_display_text(text: str) -> str:
        return re.sub(r"#+\s*", "", str(text)).strip()

    @classmethod
    def _styled_text(cls, text: str, skill_name: bool = False) -> str:
        clean = cls._clean_display_text(text)
        escaped = html.escape(clean).replace("\n", "<br>")
        if re.search(r"\b\d+(?:[.,]\d+)?\s*s(?:egundos?)?\b", clean, re.IGNORECASE):
            return escaped
        if skill_name:
            return f'<span style="color:#D9B56D"><b>{escaped}</b></span>'
        escaped = re.sub(
            r"(?<!\w)(\d+(?:[.,]\d+)?%)",
            r'<span style="color:#D9B56D"><b>\1</b></span>',
            escaped,
        )
        escaped = re.sub(
            r"\b(HP|ATK|DEF|Crit Rate|Crit DMG|Bônus|Passiva|Echos?|Aero|Glacio|Electro|Fusion|Havoc|Spectro)\b",
            r'<span style="color:#D946EF"><b>\1</b></span>',
            escaped,
            flags=re.IGNORECASE,
        )
        return escaped

    @classmethod
    def _format_skill_description(cls, text: str) -> str:
        """Converte descricoes longas em linhas HTML compactas e destacadas."""
        if re.search(r"<(?:font|b|i|br)\b", text, re.IGNORECASE):
            return text
        paragraphs = [
            " ".join(line.strip() for line in paragraph.splitlines())
            for paragraph in re.split(r"\n\s*\n", text)
            if paragraph.strip()
        ]
        formatted: list[str] = []
        for paragraph in paragraphs:
            escaped = html.escape(paragraph)
            escaped = re.sub(
                r"(?<!\w)(\d+(?:[.,]\d+)?%?(?:s)?)",
                r'<font color="#eab308"><b>\1</b></font>',
                escaped,
            )
            escaped = re.sub(
                r"\b(Dano Voltaico|ATQ Pesado|ATQ Básico|Habilidade de Ressonância|Liberação de Ressonância|Ascendência|Majestade|Proeza|Coroa de Vontades)\b",
                r'<font color="#a855f7"><b>\1</b></font>',
                escaped,
                flags=re.IGNORECASE,
            )
            formatted.append(f"• {escaped}<br>")
        return "".join(formatted)

    def _render_weapon(self, manual: dict[str, Any], kit: dict[str, Any]) -> None:
        if manual:
            text = str(manual.get(self.language, manual.get("EN", "")))
        else:
            text = str(kit.get("weapon_passive", "Passiva não cadastrada"))
        self.weapon_passive_text = self._clean_display_text(text)
        self.weapon_text.setText(self._styled_text(text))

    def _render_kit(self, kit: dict[str, Any]) -> None:
        while self.kit_layout.count():
            item = self.kit_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._element_glow_widgets = self._element_glow_widgets[:3]
        skills = kit.get("skills", []) if isinstance(kit, dict) else []
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            card = QFrame()
            card.setObjectName("skillCard")
            self._element_glow_widgets.append((card, 14, 90))
            apply_element_glow(card, self.element_box.currentText(), blur=14, opacity=90)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            icon = QLabel(("⚔", "◉", "❧", "✦", "♣")[self.kit_layout.count() % 5])
            icon.setObjectName("skillIcon")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon)
            text_layout = QVBoxLayout()
            title = QLabel(self._styled_text(str(skill.get("name", "Habilidade")), skill_name=True))
            title.setObjectName("skillTitle")
            description = str(skill.get("description", "Sem descrição"))
            description = self._format_skill_description(description)
            body = QLabel(
                description
                if re.search(r"<(?:font|b|i|br)\b", description, re.IGNORECASE)
                else self._styled_text(description)
            )
            if re.search(r"<(?:font|b|i|br)\b", description, re.IGNORECASE):
                body.setTextFormat(Qt.TextFormat.RichText)
            body.setWordWrap(True)
            text_layout.addWidget(title)
            text_layout.addWidget(body)
            card_layout.addLayout(text_layout, 1)
            number = QLabel(str(self.kit_layout.count() + 1))
            number.setObjectName("skillNumber")
            number.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(number)
            self.kit_layout.addWidget(card)

    def _set_language(self, language: str) -> None:
        self.language = language
        if self.current_id:
            kit = CHARACTER_KITS_DB.get(self.current_id) or MANUAL_CHARACTER_KITS.get(self.current_id) or {}
            self._render_weapon(MANUAL_WEAPONS.get(self.current_id, {}), kit)

    def _load_image(self, url: str, target: QLabel, fallback: str) -> None:
        if not url:
            target.setText(fallback)
            return
        if url.startswith(("http://", "https://")):
            if not allows_remote_content(url):
                target.setText(fallback)
                return
            reply = self.network.get(QNetworkRequest(QUrl(url)))
            self._image_replies[url] = reply
            reply.finished.connect(lambda: self._finish_image(reply, target, fallback, url))
            return
        if not allows_local_image(url):
            target.setText(fallback)
            return
        pixmap = QPixmap(url)
        if pixmap.isNull():
            target.setText(fallback)
            return
        target.setPixmap(self._prepare_pixmap(pixmap, target))

    def _finish_image(self, reply: object, target: QLabel, fallback: str, url: str) -> None:
        try:
            data = _read_network_reply(reply)
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if pixmap.isNull():
                target.setText(fallback)
            else:
                prepared = self._prepare_pixmap(pixmap, target)
                if target is self.weapon_image:
                    target.setFixedSize(prepared.size())
                target.setPixmap(prepared)
        except (AttributeError, RuntimeError, TypeError):
            target.setText(fallback)
        self._image_replies.pop(url, None)

    def _prepare_pixmap(self, pixmap: QPixmap, target: QLabel) -> QPixmap:
        size = target.maximumSize() if target is self.weapon_image else target.size()
        scaled = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return self._remove_edge_background(scaled)

    @staticmethod
    def _remove_edge_background(pixmap: QPixmap) -> QPixmap:
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        width = image.width()
        height = image.height()
        if width == 0 or height == 0:
            return pixmap

        corners = [
            image.pixelColor(0, 0),
            image.pixelColor(width - 1, 0),
            image.pixelColor(0, height - 1),
            image.pixelColor(width - 1, height - 1),
        ]
        background = tuple(
            sum(getattr(color, channel)() for color in corners) // len(corners)
            for channel in ("red", "green", "blue")
        )
        if all(color.alpha() < 16 for color in corners):
            return pixmap

        threshold = 24
        pending = [(x, y) for x, y in (
            *((x, 0) for x in range(width)),
            *((x, height - 1) for x in range(width)),
            *((0, y) for y in range(height)),
            *((width - 1, y) for y in range(height)),
        )]
        visited: set[tuple[int, int]] = set()
        while pending:
            x, y = pending.pop()
            if (x, y) in visited:
                continue
            visited.add((x, y))
            color = image.pixelColor(x, y)
            if color.alpha() < 16 or max(
                abs(color.red() - background[0]),
                abs(color.green() - background[1]),
                abs(color.blue() - background[2]),
            ) > threshold:
                continue
            color.setAlpha(0)
            image.setPixelColor(x, y, color)
            pending.extend((neighbor_x, neighbor_y) for neighbor_x, neighbor_y in (
                (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)
            ) if 0 <= neighbor_x < width and 0 <= neighbor_y < height)

        return QPixmap.fromImage(image)
