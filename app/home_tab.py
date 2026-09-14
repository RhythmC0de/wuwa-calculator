"""Home tab for Tethys."""

from __future__ import annotations

import builtins
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QByteArray, QObject, QEvent, QThread, QTimer, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components import Card, TitleLabel, WuWaKuroBannerCard
from app.banner_service import fetch_current_banner
from app.styles import apply_glow
from storage.banner_cache import load_cached_banner, save_cached_banner


_print = builtins.print


def _debug_print(*args: object, **kwargs: object) -> None:
    if os.environ.get("TETHYS_DEBUG_BANNER") == "1":
        _print(*args, **kwargs)


print = _debug_print


def _rounded_banner_pixmap(source: QPixmap, width: int, height: int, radius: int = 12) -> QPixmap:
    scaled = source.scaled(
        width, height, Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    canvas = QPixmap(width, height)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, width, height, radius, radius)
    painter.setClipPath(path)
    x = (width - scaled.width()) // 2
    y = (height - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)
    painter.end()
    return canvas


def _full_banner_pixmap(
    source: QPixmap,
    width: int,
    height: int,
    radius: int = 16,
    vertical_offset: int = 0,
) -> QPixmap:
    scaled = source.scaled(
        width, height, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    canvas = QPixmap(width, height)
    canvas.fill(QColor("#0C101E"))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    path = QPainterPath()
    path.addRoundedRect(
        QRectF(0, 0, width, height).adjusted(2, 2, -2, -2),
        max(0, radius - 2),
        max(0, radius - 2),
    )
    painter.setClipPath(path)
    x = (width - scaled.width()) // 2
    centered_y = (height - scaled.height()) // 2
    y = min(0, centered_y + vertical_offset)
    painter.drawPixmap(x, y, scaled)
    painter.end()
    return canvas


def _apply_rounded_image_mask(widget: QLabel, radius: int = 16) -> None:
    mask = QPixmap(widget.size())
    mask.fill(Qt.GlobalColor.transparent)
    painter = QPainter(mask)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(
        QRectF(0, 0, widget.width(), widget.height()).adjusted(2, 2, -2, -2),
        max(0, radius - 2),
        max(0, radius - 2),
    )
    painter.fillPath(path, QColor(Qt.GlobalColor.white))
    painter.end()
    widget.setMask(mask.createMaskFromColor(
        QColor(Qt.GlobalColor.transparent),
        Qt.MaskMode.MaskInColor,
    ))


class BannerWorker(QObject):
    finished = Signal(object)

    def run(self) -> None:
        print("[BannerWorker] Iniciando trabalho...")
        result = fetch_current_banner()
        if isinstance(result, dict):
            save_cached_banner(result)
        print(f"[BannerWorker] Resultado: {type(result)} - {result if not isinstance(result, dict) else 'dict com dados'}")
        self.finished.emit(result)


class CatalogWorker(QObject):
    finished = Signal(object)

    def run(self) -> None:
        from app.wuwa_tracker_adapter import fetch_banner_catalog
        self.finished.emit(fetch_banner_catalog())


class UpcomingBannerCard(QFrame):
    def __init__(self, record: dict[str, object], state: str,
                 compact: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("upcomingBannerPastCard" if compact else "upcomingBannerCard")
        self.setFixedSize(320, 128)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setProperty("hovered", False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        _apply_rounded_image_mask(self, radius=16)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 125))
        self.setGraphicsEffect(shadow)

        image = QLabel(self)
        image.setObjectName("upcomingBannerImage")
        image_margin = 2
        image.setGeometry(
            image_margin,
            image_margin,
            self.width() - image_margin * 2,
            self.height() - image_margin * 2,
        )
        image.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        image.setScaledContents(False)
        image_bytes = record.get("image_bytes", b"")
        pixmap = QPixmap()
        if isinstance(image_bytes, bytes):
            pixmap.loadFromData(QByteArray(image_bytes))
        if not pixmap.isNull():
            image.setPixmap(_full_banner_pixmap(
                pixmap,
                image.width(),
                image.height(),
                radius=14,
                vertical_offset=14,
            ))
        else:
            image.setText("Esperando anúncio oficial")
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        overlay = QFrame(self)
        overlay.setObjectName("upcomingBannerOverlay")
        overlay_width = 180
        overlay.setGeometry(10, self.height() - 50, overlay_width, 40)
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(7, 3, 7, 3)
        overlay_layout.setSpacing(0)

        name = QLabel(str(record.get("name", "Aguardando anúncio oficial")), overlay)
        name.setObjectName("upcomingBannerName")
        overlay_layout.addWidget(name)

        details = QLabel(
            f"Raridade: ★{int(record.get('rarity', 5) or 5)}\n"
            f"{record.get('date_label', 'Data: Próximo banner')}"
        , overlay)
        details.setObjectName("upcomingBannerDetails")
        overlay_layout.addWidget(details)
        image.lower()
        overlay.raise_()

        self.hover_frame = QFrame(self)
        self.hover_frame.setGeometry(0, 0, self.width(), self.height())
        self.hover_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hover_frame.setStyleSheet(
            "QFrame { background: transparent; border: 3px solid #00F5FF; "
            "border-radius: 16px; }"
        )
        self.hover_frame.hide()
        self.hover_frame.raise_()
        image.installEventFilter(self)
        overlay.installEventFilter(self)

    def _set_hovered(self, hovered: bool) -> None:
        self.hover_frame.setVisible(hovered)
        self.setProperty("hovered", hovered)
        self.style().unpolish(self)
        self.style().polish(self)

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.Enter:
            self._set_hovered(True)
        elif event.type() == QEvent.Type.Leave:
            self._set_hovered(False)
        return super().eventFilter(watched, event)

    def enterEvent(self, event) -> None:
        self._set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._set_hovered(False)
        super().leaveEvent(event)


class UpcomingBannersSection(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("upcomingBannersSection")
        self.setFixedHeight(182)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(3)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Banners Anteriores e Futuros")
        title.setObjectName("upcomingBannersTitle")
        heading.addWidget(title)
        subtitle = QLabel("Confira o banner anterior e os próximos banners.")
        subtitle.setObjectName("upcomingBannersSubtitle")
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch(1)
        for symbol in ("<", ">"):
            arrow = QPushButton(symbol)
            arrow.setObjectName("bannerTimelineArrow")
            arrow.setFixedSize(28, 28)
            header.addWidget(arrow)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 4, 0, 0)
        body.setSpacing(20)
        self.past_layout = QVBoxLayout()
        self.past_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        body.addLayout(self.past_layout, 0)
        future_layout = QVBoxLayout()
        future_title = QLabel("PRÓXIMOS BANNERS CONFIRMADOS")
        future_title.setObjectName("bannerTimelineSection")
        future_layout.addWidget(future_title)
        self.future_message = QLabel("Sem próximos banners confirmados.")
        self.future_message.setObjectName("bannerTimelineEmpty")
        future_layout.addWidget(self.future_message, 1, Qt.AlignmentFlag.AlignCenter)
        body.addLayout(future_layout, 1)
        root.addLayout(body, 1)
        self.set_cards([], loading=True)

    def set_cards(self, records: list[dict[str, object]], loading: bool = False) -> None:
        while self.past_layout.count():
            item = self.past_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        past = next((item for item in records if item.get("kind") == "past"), None)
        if past is not None:
            self.past_layout.addWidget(UpcomingBannerCard(past, "PASSADO", compact=True))


class HomeTab(QWidget):
    def __init__(self, preloaded_banner: dict[str, object] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        intro = Card()
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(20, 18, 20, 18)
        intro_layout.addWidget(TitleLabel("Tethys"))
        subtitle = QLabel("Motor de dano local para testar rotações, equipes e execução prática.")
        subtitle.setObjectName("muted")
        intro_layout.addWidget(subtitle)
        root.addWidget(intro)

        cached_banner = load_cached_banner() if preloaded_banner is None else None
        initial_banner = preloaded_banner or cached_banner
        self.banner_data: dict[str, object] | None = initial_banner
        self.banner_thread: QThread | None = None
        self.banner_worker: BannerWorker | None = None
        self.catalog_thread: QThread | None = None
        self.catalog_worker: CatalogWorker | None = None
        self.banner_card: WuWaKuroBannerCard | None = None
        
        # Container temporário para o banner enquanto carrega
        self.banner_placeholder = QFrame()
        self.banner_placeholder.setFixedWidth(960)
        self.banner_placeholder.setFixedHeight(480)
        placeholder_layout = QVBoxLayout(self.banner_placeholder)
        placeholder_layout.setContentsMargins(0, 0, 0, 0)
        placeholder_label = QLabel("Carregando banner...")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setObjectName("muted")
        placeholder_layout.addWidget(placeholder_label)
        self.banner_container = root
        
        # Se já tem banner pré-carregado, mostra imediatamente
        if initial_banner:
            print("[HomeTab] Banner pré-carregado recebido, criando card imediatamente...")
            self._banner_loaded(initial_banner)
            QTimer.singleShot(0, self._start_banner_refresh)
        else:
            # Caso contrário, mostra placeholder e carrega em background
            root.addWidget(self.banner_placeholder)
            QTimer.singleShot(0, self._start_banner_refresh)

        self.timeline_panel = UpcomingBannersSection()
        self.timeline_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        root.addSpacing(8)
        root.addWidget(self.timeline_panel)
        QTimer.singleShot(0, self._start_catalog_refresh)
        root.addStretch(1)

    def set_active(self, active: bool) -> None:
        if self.banner_card is not None:
            self.banner_card.set_active(active)

    def _start_catalog_refresh(self) -> None:
        self.catalog_thread = QThread(self)
        self.catalog_worker = CatalogWorker()
        self.catalog_worker.moveToThread(self.catalog_thread)
        self.catalog_thread.started.connect(self.catalog_worker.run)
        self.catalog_worker.finished.connect(self._catalog_loaded)
        self.catalog_worker.finished.connect(self.catalog_thread.quit)
        self.catalog_thread.finished.connect(self._clear_catalog_worker)
        self.catalog_thread.start()

    @staticmethod
    def _parse_catalog_date(value: object) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except ValueError:
            return None

    def _catalog_loaded(self, data: object) -> None:
        records = data if isinstance(data, list) else []
        now = datetime.now(timezone.utc)
        past_limit = now - timedelta(days=7)
        future_limit = now + timedelta(days=14)
        visible: list[dict[str, object]] = []
        for raw in records:
            if not isinstance(raw, dict):
                continue
            starts_at = self._parse_catalog_date(raw.get("starts_at"))
            ends_at = self._parse_catalog_date(raw.get("ends_at"))
            if ends_at is None:
                continue
            if starts_at is not None and starts_at <= now <= ends_at:
                continue
            if ends_at < now and ends_at >= past_limit:
                record = dict(raw)
                record["kind"] = "past"
                record["date_label"] = f"Data: {ends_at.strftime('%d/%m/%Y')}"
                visible.append(record)
            elif ends_at >= now and starts_at is not None and now < starts_at <= future_limit:
                if raw.get("speculated") or raw.get("isSpeculated"):
                    continue
                record = dict(raw)
                record["kind"] = "future"
                record["name"] = str(raw.get("name", "Personagem"))
                record["date_label"] = f"Data: {starts_at.strftime('%d/%m/%Y')}"
                visible.append(record)

        visible.sort(key=lambda item: str(item.get("ends_at", "")))
        self.timeline_panel.set_cards(visible)

    def _clear_catalog_worker(self) -> None:
        if self.catalog_worker is not None:
            self.catalog_worker.deleteLater()
        if self.catalog_thread is not None:
            self.catalog_thread.deleteLater()
        self.catalog_worker = None
        self.catalog_thread = None

    def _start_banner_refresh(self) -> None:
        print("[HomeTab] Iniciando refresh de banner...")
        self.banner_thread = QThread(self)
        self.banner_worker = BannerWorker()
        self.banner_worker.moveToThread(self.banner_thread)
        self.banner_thread.started.connect(self.banner_worker.run)
        self.banner_worker.finished.connect(self._banner_loaded)
        self.banner_worker.finished.connect(self.banner_thread.quit)
        self.banner_thread.finished.connect(self._clear_banner_worker)
        self.banner_thread.start()
        print("[HomeTab] Thread de banner iniciada")

    def _banner_loaded(self, data: object) -> None:
        print(f"[HomeTab] _banner_loaded chamado. data type: {type(data)}")
        
        if not isinstance(data, dict):
            print("[HomeTab] Banner data não é dict, mantendo placeholder")
            return
        
        self.banner_data = data
        character_name = str(data.get('name', 'Banner'))
        image_bytes = data.get('image_bytes', b'')
        ends_at_str = str(data.get('ends_at', ''))
        
        print(f"[HomeTab] character_name: {character_name}")
        print(f"[HomeTab] image_bytes length: {len(image_bytes) if isinstance(image_bytes, bytes) else 'NÃO É BYTES'}")
        print(f"[HomeTab] ends_at_str: {ends_at_str}")
        
        if not isinstance(image_bytes, bytes) or len(image_bytes) == 0:
            print("[HomeTab] image_bytes vazio, retornando")
            return
        
        try:
            ends_at = datetime.fromisoformat(ends_at_str)
            print(f"[HomeTab] ends_at parseado: {ends_at}")
        except (ValueError, TypeError) as e:
            print(f"[HomeTab] Erro ao parsear data: {e}")
            return

        starts_at = self._parse_catalog_date(data.get("starts_at"))
        if starts_at is None and character_name.casefold() == "jingran":
            starts_at = datetime(2026, 9, 10, 10, tzinfo=timezone.utc)
        
        # Remove o placeholder e cria o novo banner card
        print("[HomeTab] Removendo placeholder...")
        if self.banner_placeholder and self.banner_placeholder.parent():
            self.banner_container.removeWidget(self.banner_placeholder)
            self.banner_placeholder.deleteLater()
            self.banner_placeholder = None

        if self.banner_card is not None:
            self.banner_container.removeWidget(self.banner_card)
            self.banner_card.deleteLater()
            self.banner_card = None
        
        print("[HomeTab] Criando WuWaKuroBannerCard...")
        self.banner_card = WuWaKuroBannerCard(
            character_name=character_name,
            image_bytes=image_bytes,
            end_date=ends_at,
            banner_start=starts_at,
            element=str(data.get("element", "")) or None,
        )
        self.banner_container.insertWidget(1, self.banner_card)
        print("[HomeTab] Banner card criado e inserido no layout")

    def _clear_banner_worker(self) -> None:
        print("[HomeTab] Limpando banner worker...")
        if self.banner_worker is not None:
            self.banner_worker.deleteLater()
        if self.banner_thread is not None:
            self.banner_thread.deleteLater()
        self.banner_worker = None
        self.banner_thread = None
        print("[HomeTab] Banner worker limpo")
