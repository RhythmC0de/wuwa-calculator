"""Compact real-time pity tracker UI fed by an authorized local source."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

from PySide6.QtCore import (
    QEasingCurve,
    Property,
    QPropertyAnimation,
    QObject,
    QRectF,
    QThread,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wuwa_calculator.app.security_policy import allows_remote_content
from src.wuwa_calculator.app.styles import wallpaper_palette
EVENT_RESONATOR_BANNER_URL = "https://i.imgur.com/JrRW9Bt.jpeg"
SIGNATURE_WEAPON_BANNER_URL = "https://i.imgur.com/metoowt.jpeg"


@dataclass
class PityState:
    resonator: int | None = None
    weapon: int | None = None
    standard_character: int | None = None
    standard_weapon: int | None = None
    guaranteed: bool | None = None
    five_star_history: list[int] = field(default_factory=list)
    total_registered: int = 0


class PityHistoryImportWorker(QObject):
    imported = Signal(object)
    failed = Signal(str)

    def __init__(self, history_url: str) -> None:
        super().__init__()
        self.history_url = history_url.strip()

    @Slot()
    def run(self) -> None:
        try:
            query = parse_qs(urlsplit(self.history_url).fragment.split("?", 1)[-1])
            params = {key: values[-1] for key, values in query.items() if values}
            host = urlsplit(self.history_url).netloc
            endpoint = f"https://{host}/aki/gacha/record/query"
            records: list[dict[str, object]] = []
            for page in range(1, 21):
                body = {**params, "page": page, "size": 20}
                request = Request(
                    endpoint,
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                    method="POST",
                )
                with urlopen(request, timeout=10) as response:  # nosec B310
                    payload = json.loads(response.read().decode("utf-8"))
                data = payload.get("data", payload) if isinstance(payload, dict) else {}
                page_records = data.get("list", data.get("records", [])) if isinstance(data, dict) else []
                if not isinstance(page_records, list) or not page_records:
                    break
                records.extend(item for item in page_records if isinstance(item, dict))
                if len(page_records) < 20:
                    break
            if not records:
                raise ValueError("Nenhum registro foi retornado pela URL do histórico.")
            self.imported.emit(records)
        except Exception as error:
            self.failed.emit(str(error))


class PityTrackerWorker(QObject):
    """Qt worker endpoint for an authorized local history adapter."""

    new_pull_captured = Signal(list)
    shot_captured = Signal(dict)

    @Slot(list)
    def ingest_items(self, items: list[object]) -> None:
        if items:
            self.new_pull_captured.emit(items)
            self.shot_captured.emit({"items": items})


class _TrackerCard(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pityTrackerCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("pityCardTitle")
        layout.addWidget(title_label)
        self.content_layout = layout


class _BannerArtLabel(QLabel):
    """Banner art clipped to a soft, semi-rounded rectangle."""

    CORNER_RADIUS = 14

    def __init__(
        self,
        parent: QWidget | None = None,
        backdrop: str = "#111521",
        fit_entire: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._source = QPixmap()
        self._backdrop = QColor(backdrop)
        self._fit_entire = fit_entire

    def set_backdrop(self, color: str) -> None:
        self._backdrop = QColor(color)
        self.update()

    def set_art(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self.update()

    def resizeEvent(self, event) -> None:
        mask = QPixmap(self.size())
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.CORNER_RADIUS, self.CORNER_RADIUS)
        painter.fillPath(path, Qt.GlobalColor.white)
        painter.end()
        self.setMask(
            mask.createMaskFromColor(
                QColor(Qt.GlobalColor.transparent),
                Qt.MaskMode.MaskInColor,
            )
        )
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if self._source.isNull() or self.width() <= 0 or self.height() <= 0:
            painter.end()
            return

        mode = (
            Qt.AspectRatioMode.KeepAspectRatio
            if self._fit_entire
            else Qt.AspectRatioMode.KeepAspectRatioByExpanding
        )
        scaled = self._source.scaled(
            self.size(), mode, Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        image_rect = QRectF(x, y, scaled.width(), scaled.height()).adjusted(
            0.5, 0.5, -0.5, -0.5
        )
        path = QPainterPath()
        path.addRoundedRect(image_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        painter.setClipPath(path)
        painter.fillRect(image_rect, self._backdrop)
        painter.drawPixmap(x, y, scaled)
        painter.end()


class _ConveneBannerCard(QFrame):
    """Compact tracker row with a clipped banner thumbnail."""

    def __init__(
        self,
        title: str,
        accent: str,
        fit_entire: bool = False,
        art_size: tuple[int, int] = (64, 64),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("conveneBannerCard")
        self.setFixedHeight(82)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(10)
        backdrop = (
            "#2A1945" if accent == "#A855F7"
            else "#302817" if accent == "#EAB308"
            else "#111521"
        )
        self.art = _BannerArtLabel(self, backdrop, fit_entire)
        self.art.setFixedSize(*art_size)
        shadow = QGraphicsDropShadowEffect(self.art)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 145))
        self.art.setGraphicsEffect(shadow)
        layout.addWidget(self.art)

        self.overlay = QFrame(self)
        self.overlay.setObjectName("conveneBannerOverlay")
        self.overlay.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        parts = title.split(" - ", 1)
        category = parts[1] if len(parts) == 2 else title
        name = parts[0] if len(parts) == 2 else "Standard Convene"
        self.category_label = QLabel(category, self.overlay)
        self.category_label.setObjectName("conveneBannerCategory")
        self.category_label.setStyleSheet(f"color: {accent};")
        overlay_layout.addWidget(self.category_label)
        self.title_label = QLabel(name, self.overlay)
        self.title_label.setObjectName("conveneBannerTitle")
        overlay_layout.addWidget(self.title_label)
        self.pity_label = QLabel("-- / 80", self.overlay)
        self.pity_label.setObjectName("conveneBannerPity")
        overlay_layout.addWidget(self.pity_label)
        self.badge = QLabel(self.overlay)
        self.badge.setObjectName("conveneBannerBadge")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setMinimumWidth(66)
        self.badge.setMaximumWidth(120)
        overlay_layout.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.overlay, 1)

    def set_pity(self, value: int | None) -> None:
        display = value if value is not None else "--"
        self.pity_label.setText(f"{display} / 80")

    def set_badges(self, values: list[str]) -> None:
        self.badge.setText(values[0] if values else "")


class PityTrackerWidget(QFrame):
    """Glassmorphism tracker. Feed authorized pull data through capture_pull."""

    new_pull_captured = Signal(list)
    sync_log_clicked = Signal()
    view_history_clicked = Signal()
    export_data_clicked = Signal()

    def __init__(
        self,
        active_character: str = "qingxiao",
        banner_images: dict[str, object] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pityTracker")
        self.setMinimumWidth(320)
        self.setMaximumWidth(360)
        self.setFixedHeight(440)
        self.setMaximumHeight(480)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.state = PityState()
        self.active_character = active_character.casefold().strip()
        self.banner_images = banner_images or {}
        self.image_network = QNetworkAccessManager(self)
        self._image_replies: dict[str, QNetworkReply] = {}
        self.url_input = QLineEdit(self)
        self.url_input.hide()
        self._import_thread = None
        self._import_worker = None
        self._pulse_value = 0.0
        self._palette_accent = "#A855F7"
        self._build_large_banner_ui()
        self.apply_wallpaper_palette(*wallpaper_palette())
        self._load_visual_assets()
        self._pulse_animation = QPropertyAnimation(self, b"pulseValue", self)
        self._pulse_animation.setDuration(420)
        self._pulse_animation.setStartValue(1.0)
        self._pulse_animation.setEndValue(0.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _build_large_banner_ui(self) -> None:
        self.setStyleSheet(
            "QFrame#pityTracker { background: #0F1118; border: 1px solid #292D38; border-radius: 16px; }"
            "QFrame#conveneBannerCard { background: #161822; border: 1px solid #2B2F3B; border-radius: 12px; }"
            "QLabel#conveneBannerCategory { font-size: 9px; font-weight: 700; }"
            "QLabel#conveneBannerTitle { color: #F5F3FA; font-size: 16px; font-weight: 700; }"
            "QLabel#conveneBannerPity { color: #C8A8FF; font-size: 18px; font-weight: 700; }"
            "QLabel#conveneBannerBadge { color: #B995FF; background: transparent; border: 1px solid #3B2859; border-radius: 16px; padding: 3px 8px; font-size: 9px; font-weight: 700; }"
            "QLabel#pityHeader { color: #D7D4DD; font-size: 13px; font-weight: 700; letter-spacing: 1px; }"
            "QLabel#pityOnline { color: #70C987; font-size: 10px; }"
            "QLabel#pityMeta { color: #A6A4AF; font-size: 9px; }"
            "QLabel#pityStatIcon { color: #C4C0CD; font-size: 18px; }"
            "QLabel#pityStatValue { color: #C4C0CD; font-size: 10px; }"
            "QPushButton#pityIconButton { color: #D9D7DF; background: transparent; border: 0; font-size: 21px; padding: 0; }"
            "QPushButton#pityIconButton:hover { color: #B995FF; }"
            "QPushButton#pityFooter { color: #B995FF; background: #171A22; border: 1px solid #2D303A; border-radius: 10px; padding: 8px; font-size: 11px; font-weight: 700; }"
            "QPushButton#pityFooter:hover { background: #20202D; border-color: #8D61D4; }"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 13, 14, 13)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(5)
        tracker_badge = QLabel("CONVENE TRACKER")
        tracker_badge.setObjectName("pityHeader")
        header.addWidget(tracker_badge)
        online = QLabel("● ONLINE")
        online.setObjectName("pityOnline")
        header.addWidget(online)
        header.addStretch(1)
        sync_button = QPushButton("↻")
        sync_button.setObjectName("pityIconButton")
        sync_button.setFixedSize(28, 28)
        sync_button.setToolTip("Sync Log")
        sync_button.clicked.connect(self._request_sync)
        self.sync_button = sync_button
        history_button = QPushButton("•••")
        history_button.setObjectName("pityIconButton")
        history_button.setFixedSize(28, 28)
        history_button.setToolTip("Histórico completo")
        history_button.clicked.connect(self.view_history_clicked)
        header.addWidget(sync_button)
        header.addWidget(history_button)
        root.addLayout(header)

        self.sync_label = QLabel("◷  Última sincronização por Log: --")
        self.sync_label.setObjectName("pityMeta")
        self.sync_label.hide()

        character_name = self.active_character.replace(" xuanling", "").title()
        self.resonator_card = _ConveneBannerCard(
            f"{character_name} - Event Resonator", "#A855F7"
        )
        self.resonator_value = self.resonator_card.pity_label
        self.resonator_progress = self._make_progress()
        self.guarantee_label = QLabel(self.resonator_card.overlay)
        self.weapon_card = _ConveneBannerCard(
            "Thousandfold Deliverance - Signature Weapon",
            "#EAB308",
            True,
            (64, 64),
        )
        self.weapon_value = self.weapon_card.pity_label
        self.weapon_progress = self._make_progress()
        self.standard_card = _ConveneBannerCard("Standard Convene", "#38BDF8")
        self.standard_character = self.standard_card.pity_label
        self.standard_weapon = QLabel()

        for card in (self.resonator_card, self.weapon_card, self.standard_card):
            root.addWidget(card)

        self.history_row = QHBoxLayout()
        self.footer_stats = QLabel()
        self.footer_stats.hide()
        stats = QHBoxLayout()
        stats.setSpacing(0)
        stat_values = (("◷", "Last Update", "--"), ("◇", "Total de Giros", "--"), ("✧", "Next Pity Milestone", "--"))
        for index, (icon, label, value) in enumerate(stat_values):
            column = QVBoxLayout()
            column.setSpacing(0)
            icon_label = QLabel(icon)
            icon_label.setObjectName("pityStatIcon")
            column.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignLeft)
            name = QLabel(label)
            name.setObjectName("pityMeta")
            column.addWidget(name)
            stat_value = QLabel(value)
            stat_value.setObjectName("pityStatValue")
            column.addWidget(stat_value)
            if label == "Last Update":
                self.last_update_value = stat_value
            elif label == "Total de Giros":
                self.total_pulls_value = stat_value
            else:
                self.next_pity_value = stat_value
            stats.addLayout(column, 1)
            if index < 2:
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setStyleSheet("color: #343741;")
                stats.addWidget(separator)
        root.addLayout(stats)
        footer_button = QPushButton("Ver Histórico Completo  >")
        footer_button.setObjectName("pityFooter")
        footer_button.clicked.connect(self.view_history_clicked)
        root.addWidget(footer_button)
        self._refresh_labels()

    def apply_wallpaper_palette(
        self,
        surface: str,
        panel: str,
        border: str,
        accent: str,
        muted: str,
        theme_accent: str | None = None,
    ) -> None:
        """Apply wallpaper-derived colors to every tracker surface."""
        accent = theme_accent or accent
        self._palette_accent = accent
        self.setStyleSheet(
            self.styleSheet()
            + f"QFrame#pityTracker {{ background: {panel}; border-color: {border}; }}"
            f"QFrame#conveneBannerCard {{ background: {surface}; border-color: {border}; }}"
            f"QLabel#conveneBannerCategory, QLabel#conveneBannerPity, "
            f"QLabel#conveneBannerBadge, QPushButton#pityIconButton, "
            f"QPushButton#pityFooter, QLabel#pityOnline {{ color: {accent}; }}"
            f"QLabel#pityMeta {{ color: {muted}; }}"
            f"QLabel#pityStatValue {{ color: {muted}; }}"
            f"QLabel#conveneBannerBadge {{ border-color: {border}; }}"
            f"QPushButton#pityFooter {{ background: {surface}; border-color: {border}; }}"
        )
        self.resonator_card.category_label.setStyleSheet(f"color: {accent};")
        self.weapon_card.category_label.setStyleSheet(f"color: {accent};")
        self.standard_card.category_label.setStyleSheet(f"color: {accent};")
        for card in (self.resonator_card, self.weapon_card, self.standard_card):
            card.art.set_backdrop(panel)
            effect = card.art.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                shadow_color = QColor(accent)
                shadow_color.setAlpha(160)
                effect.setColor(shadow_color)
        self._refresh_labels()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            "QFrame#pityTracker { background: rgba(15, 17, 26, 224); "
            "border: 1px solid rgba(168, 85, 247, 215); border-radius: 16px; }"
            "QFrame#pityTile { background: rgba(9, 12, 22, 120); "
            "border: 1px solid rgba(6, 182, 212, 130); border-radius: 10px; }"
            "QLabel#pityCardTitle { color: #FFFFFF; font-size: 9px; font-weight: 900; }"
            "QLabel#pityValue { color: #FFFFFF; font-size: 22px; font-weight: 900; "
            "padding: 0; min-height: 27px; }"
            "QLabel#pityResonatorAvatar, QLabel#pityWeaponAvatar { background: rgba(8, 10, 18, 220); "
            "border-radius: 18px; padding: 1px; }"
            "QLabel#pityStandardIcon { color: #7DD3FC; background: rgba(14, 165, 233, 35); "
            "border: 1px solid #38BDF8; border-radius: 18px; padding: 1px; }"
            "QLabel#pityBadge { color: #9DEBFF; background: rgba(6, 182, 212, 35); "
            "border: 1px solid rgba(6, 182, 212, 130); border-radius: 9px; "
            "padding: 4px 8px; font-size: 9px; font-weight: 900; }"
            "QLabel#pitySubtitle { color: #10b981; font-size: 10px; font-weight: 800; }"
            "QLabel#pityMeta { color: #C9C6D9; font-size: 9px; }"
            "QLabel#pityHistory { color: #E7D7FF; font-size: 9px; }"
            "QPushButton#pityIconButton { color: #CFEFFF; background: rgba(9, 20, 35, 180); "
            "border: 1px solid rgba(96, 165, 250, 150); border-radius: 8px; "
            "font-size: 14px; font-weight: 900; padding: 0; }"
            "QPushButton#pityIconButton:hover, QPushButton#pityFooter:hover { "
            "background: rgba(6, 182, 212, 55); border-color: #7DEBFF; }"
            "QPushButton#pityFooter { color: #CFEFFF; background: rgba(9, 20, 35, 180); "
            "border: 1px solid rgba(6, 182, 212, 120); border-radius: 8px; "
            "padding: 6px 8px; font-size: 9px; font-weight: 800; }"
            "QLabel#pityHistoryBadge { color: #F8E7FF; background: rgba(168, 85, 247, 90); "
            "border: 1px solid #A855F7; border-radius: 10px; font-size: 8px; font-weight: 900; }"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 9)
        root.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(5)
        tracker_badge = QLabel("[ CONVENE TRACKER ]")
        tracker_badge.setObjectName("pityBadge")
        header.addWidget(tracker_badge)
        header.addStretch(1)
        sync_button = QPushButton("↻")
        sync_button.setObjectName("pityIconButton")
        sync_button.setFixedSize(28, 28)
        sync_button.setToolTip("Sync Log")
        sync_button.clicked.connect(self._request_sync)
        self.sync_button = sync_button
        export_button = QPushButton("⇩")
        export_button.setObjectName("pityIconButton")
        export_button.setFixedSize(28, 28)
        export_button.setToolTip("Export")
        export_button.clicked.connect(self.export_data_clicked)
        header.addWidget(sync_button)
        header.addWidget(export_button)
        root.addLayout(header)

        subtitle = QLabel("●  Sniffer em Tempo Real: ONLINE")
        subtitle.setObjectName("pitySubtitle")
        root.addWidget(subtitle)

        self.sync_label = QLabel("◷  Última sincronização por Log: --")
        self.sync_label.setObjectName("pityMeta")
        self.sync_label.hide()
        pity_grid = QGridLayout()
        pity_grid.setContentsMargins(0, 0, 0, 0)
        pity_grid.setHorizontalSpacing(6)
        pity_grid.setVerticalSpacing(6)

        self.resonator_card = self._make_pity_tile("RESONATOR", "pityResonatorAvatar")
        self.resonator_avatar = QLabel(self.resonator_card)
        self.resonator_avatar.setObjectName("pityResonatorAvatar")
        self.resonator_avatar.setGeometry(108, 28, 36, 36)
        self.resonator_avatar.setFixedSize(36, 36)
        self.resonator_avatar.setScaledContents(True)
        resonator_value = QLabel(self.resonator_card)
        resonator_value.setObjectName("pityValue")
        self.resonator_value = resonator_value
        self.resonator_value.setGeometry(10, 27, 94, 29)
        self.resonator_progress = self._make_progress()
        self.resonator_progress.setGeometry(10, 61, 94, 5)
        self.guarantee_label = QLabel(self.resonator_card)
        self.guarantee_label.setObjectName("pityMeta")
        self.guarantee_label.setGeometry(10, 70, 130, 16)
        pity_grid.addWidget(self.resonator_card, 0, 0)

        self.weapon_card = self._make_pity_tile("WEAPON", "pityWeaponAvatar")
        self.weapon_avatar = QLabel(self.weapon_card)
        self.weapon_avatar.setObjectName("pityWeaponAvatar")
        self.weapon_avatar.setGeometry(108, 28, 36, 36)
        self.weapon_avatar.setFixedSize(36, 36)
        self.weapon_avatar.setScaledContents(True)
        self.weapon_value = QLabel(self.weapon_card)
        self.weapon_value.setObjectName("pityValue")
        self.weapon_value.setGeometry(10, 27, 94, 29)
        self.weapon_progress = self._make_progress()
        self.weapon_progress.setGeometry(10, 61, 94, 5)
        pity_grid.addWidget(self.weapon_card, 0, 1)

        self.standard_character_card = self._make_pity_tile("STD CHAR", "pityStandardIcon")
        self.standard_character_icon = QLabel("◆", self.standard_character_card)
        self.standard_character_icon.setObjectName("pityStandardIcon")
        self.standard_character_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.standard_character_icon.setGeometry(108, 28, 36, 36)
        self.standard_character_icon.setFixedSize(36, 36)
        self.standard_character_icon.setScaledContents(True)
        self.standard_character = QLabel(self.standard_character_card)
        self.standard_character.setObjectName("pityValue")
        self.standard_character.setGeometry(10, 27, 94, 29)
        pity_grid.addWidget(self.standard_character_card, 1, 0)

        self.standard_weapon_card = self._make_pity_tile("STD WEAPON", "pityStandardIcon")
        self.standard_weapon_icon = QLabel("◆", self.standard_weapon_card)
        self.standard_weapon_icon.setObjectName("pityStandardIcon")
        self.standard_weapon_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.standard_weapon_icon.setGeometry(108, 28, 36, 36)
        self.standard_weapon_icon.setFixedSize(36, 36)
        self.standard_weapon_icon.setScaledContents(True)
        self.standard_weapon = QLabel(self.standard_weapon_card)
        self.standard_weapon.setObjectName("pityValue")
        self.standard_weapon.setGeometry(10, 27, 94, 29)
        pity_grid.addWidget(self.standard_weapon_card, 1, 1)
        root.addLayout(pity_grid)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(5)
        recent_label = QLabel("5★ Recentes")
        recent_label.setObjectName("pityMeta")
        footer_row.addWidget(recent_label)
        self.history_row = QHBoxLayout()
        self.history_row.setSpacing(4)
        footer_row.addLayout(self.history_row)
        footer_row.addStretch(1)
        root.addLayout(footer_row)
        footer_stats = QLabel()
        footer_stats.setObjectName("pityMeta")
        root.addWidget(footer_stats)
        self.footer_stats = footer_stats
        history_button = QPushButton("Ver Histórico Completo  >")
        history_button.setObjectName("pityFooter")
        history_button.clicked.connect(self.view_history_clicked)
        root.addWidget(history_button)
        self._refresh_labels()

    @staticmethod
    def _make_pity_tile(title: str, avatar_name: str) -> QFrame:
        tile = QFrame()
        tile.setObjectName("pityTile")
        tile.setFixedHeight(94)
        title_label = QLabel(title, tile)
        title_label.setObjectName("pityCardTitle")
        title_label.setGeometry(10, 8, 110, 16)
        return tile

    def _load_visual_assets(self) -> None:
        self._load_banner_image(
            EVENT_RESONATOR_BANNER_URL,
            self.resonator_card.art,
        )
        self._load_banner_image(
            SIGNATURE_WEAPON_BANNER_URL,
            self.weapon_card.art,
        )

    def _load_banner_image(self, url: str, target: _BannerArtLabel) -> None:
        if not url or not allows_remote_content(url):
            return
        reply = self.image_network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(lambda: self._finish_banner_image(reply, url, target))

    def _finish_banner_image(
        self,
        reply: QNetworkReply,
        url: str,
        target: _BannerArtLabel,
    ) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(bytes(reply.readAll()))
            if not pixmap.isNull():
                target.set_art(pixmap)
        finally:
            self._image_replies.pop(url, None)

    def _load_image(
        self,
        url: str,
        target: QLabel,
        width: int,
        height: int,
        border_color: str | None = None,
    ) -> None:
        if not url or not allows_remote_content(url):
            return
        reply = self.image_network.get(QNetworkRequest(QUrl(url)))
        self._image_replies[url] = reply
        reply.finished.connect(
            lambda: self._finish_image(reply, url, target, width, height, border_color)
        )

    def _finish_image(
        self,
        reply: QNetworkReply,
        url: str,
        target: QLabel,
        width: int,
        height: int,
        border_color: str | None,
    ) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(bytes(reply.readAll()))
            if not pixmap.isNull():
                target.setPixmap(self._circular_pixmap(pixmap, width, height))
                if border_color:
                    target.setStyleSheet(
                        f"border: 1px solid {border_color}; border-radius: {width // 2}px;"
                    )
        finally:
            self._image_replies.pop(url, None)

    @staticmethod
    def _circular_pixmap(source: QPixmap, width: int, height: int) -> QPixmap:
        scaled = source.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        canvas = QPixmap(width, height)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = QPainterPath()
        path.addEllipse(0, 0, width, height)
        painter.setClipPath(path)
        x = (width - scaled.width()) // 2
        y = (height - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        return canvas

    @staticmethod
    def _make_progress() -> QProgressBar:
        progress = QProgressBar()
        progress.setRange(0, 80)
        progress.setValue(0)
        progress.setTextVisible(False)
        progress.setFixedHeight(5)
        return progress

    pulseValue = Property(float, lambda self: self._pulse_value, lambda self, value: self._set_pulse(value))

    def _set_pulse(self, value: float) -> None:
        self._pulse_value = value
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(8 + value * 22)
            effect.setColor(QColor(6, 182, 212, int(100 + value * 150)))

    def _refresh_labels(self) -> None:
        resonator = self.state.resonator if self.state.resonator is not None else "--"
        weapon = self.state.weapon if self.state.weapon is not None else "--"
        standard_character = (
            self.state.standard_character
            if self.state.standard_character is not None else "--"
        )
        standard_weapon = (
            self.state.standard_weapon
            if self.state.standard_weapon is not None else "--"
        )
        self.resonator_card.set_pity(self.state.resonator)
        self.weapon_card.set_pity(self.state.weapon)
        self.standard_card.set_pity(self.state.standard_character)
        guarantee = (
            "50/50: Garantido" if self.state.guaranteed is True
            else "50/50: Ativo" if self.state.guaranteed is False
            else "50/50: --"
        )
        recent = self.state.five_star_history[-1] if self.state.five_star_history else "--"
        self.resonator_card.set_badges([guarantee, f"5★ Recente: {recent} pulls"])
        self.weapon_card.set_badges([f"5★ Recente: {recent} pulls"])
        self.standard_card.set_badges([f"Arma: {standard_weapon} / 80"])
        self.standard_weapon.setText(f"Arma: {standard_weapon} / 80")
        total = self.state.total_registered or "--"
        self.footer_stats.setText(f"Total registrado no banco: {total} tiros")
        self.total_pulls_value.setText(
            f"{self.state.total_registered:,}" if self.state.total_registered else "--"
        )
        current_pity = self.state.resonator
        next_pity = max(0, 80 - current_pity) if current_pity is not None else None
        self.next_pity_value.setText(
            f"In {next_pity} pulls" if next_pity is not None else "--"
        )
        self.last_update_value.setText(
            "Just now" if self.state.total_registered else "--"
        )
        self._set_progress(self.resonator_progress, self.state.resonator)
        self._set_progress(self.weapon_progress, self.state.weapon)
        self._render_history_avatars()

    def _render_history_avatars(self) -> None:
        while self.history_row.count():
            item = self.history_row.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        history = self.state.five_star_history[-3:]
        if not history:
            empty = QLabel("--")
            empty.setObjectName("pityHistory")
            self.history_row.addWidget(empty)
            return
        for value in reversed(history):
            avatar = QLabel()
            avatar.setObjectName("pityHistoryBadge")
            avatar.setFixedSize(20, 20)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setText(str(value))
            avatar.setToolTip(f"5★ após {value} tiros")
            self.history_row.addWidget(avatar)
        self.history_row.addStretch(1)

    def _request_sync(self) -> None:
        self.sync_log_clicked.emit()
        url, accepted = QInputDialog.getText(
            self,
            "Sincronizar via Log",
            "Cole a URL do histórico de invocações:",
        )
        if accepted and url.strip():
            self.url_input.setText(url.strip())
            self._start_import()

    def _set_progress(self, progress: QProgressBar, value: int | None) -> None:
        current = max(0, min(80, value or 0))
        color = self._palette_accent
        progress.setValue(current)
        progress.setStyleSheet(
            "QProgressBar { background: rgba(255,255,255,18); border: 0; border-radius: 2px; }"
            f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}"
        )

    def _start_import(self) -> None:
        if not self.url_input.text().strip():
            return
        self.sync_button.setEnabled(False)
        self._import_thread = QThread(self)
        self._import_worker = PityHistoryImportWorker(self.url_input.text())
        self._import_worker.moveToThread(self._import_thread)
        self._import_thread.started.connect(self._import_worker.run)
        self._import_worker.imported.connect(self._apply_imported_records)
        self._import_worker.failed.connect(self._import_failed)
        self._import_worker.imported.connect(self._import_thread.quit)
        self._import_worker.failed.connect(self._import_thread.quit)
        self._import_thread.finished.connect(self._clear_import)
        self._import_thread.start()

    def _apply_imported_records(self, records: object) -> None:
        if not isinstance(records, list):
            return
        pity = 0
        five_stars: list[int] = []
        for record in reversed(records):
            pity += 1
            rarity = record.get("quality", record.get("rarity", 0)) if isinstance(record, dict) else 0
            try:
                if int(rarity) >= 5:
                    five_stars.append(pity)
                    pity = 0
            except (TypeError, ValueError):
                continue
        self.state.resonator = pity
        self.state.five_star_history = five_stars[:3]
        self.state.total_registered = len(records)
        self.sync_label.setText("◷  Última sincronização por Log: agora")
        self._refresh_labels()

    def _import_failed(self, message: str) -> None:
        self.sync_label.setText("◷  Falha na sincronização por Log")
        self.sync_label.setToolTip(message)
        self._refresh_labels()

    def _clear_import(self) -> None:
        if self._import_worker is not None:
            self._import_worker.deleteLater()
        if self._import_thread is not None:
            self._import_thread.deleteLater()
        self._import_worker = None
        self._import_thread = None
        self.sync_button.setEnabled(True)

    def capture_pull(self, items: Iterable[object]) -> None:
        """Apply one authorized pull result and notify listeners."""
        item_list = list(items)
        if not item_list:
            return
        self.state.resonator = (self.state.resonator or 0) + len(item_list)
        self.state.total_registered += len(item_list)
        self._refresh_labels()
        self.new_pull_captured.emit(item_list)
        self._pulse_animation.stop()
        self._pulse_animation.start()

    def bind_worker(self, worker: PityTrackerWorker) -> None:
        worker.shot_captured.connect(self.capture_shot)

    def capture_shot(self, shot: dict[str, object]) -> None:
        items = shot.get("items", [])
        if isinstance(items, list):
            self.capture_pull(items)