"""Reusable PySide6 presentation components."""

import builtins
import os
import sys
import math
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt, QTimer, QByteArray, QRect, QRectF, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve
from PySide6.QtGui import (
    QPixmap, QPainter, QBrush, QColor, QBitmap, QPainterPath,
    QLinearGradient, QRadialGradient, QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.wuwa_calculator.app.styles import CARD, apply_element_glow, apply_glow
from src.wuwa_calculator.data.characters_elements import CHARACTER_ELEMENTS


_print = builtins.print


def _debug_print(*args: object, **kwargs: object) -> None:
    if os.environ.get("TETHYS_DEBUG_BANNER") == "1":
        _print(*args, **kwargs)


print = _debug_print


ELEMENT_UI_COLORS = {
    "Aero": ("#75E8C5", "rgba(27, 105, 82, 225)"),
    "Fusion": ("#FF9A6B", "rgba(100, 38, 30, 225)"),
    "Glacio": ("#9EDBFF", "rgba(35, 76, 125, 225)"),
    "Havoc": ("#FF79B5", "rgba(96, 30, 66, 225)"),
    "Electro": ("#C7A4FF", "rgba(64, 42, 110, 225)"),
    "Spectro": ("#FFE28A", "rgba(105, 82, 30, 225)"),
}

ELEMENT_NUMBER_COLORS = {
    "Aero": "#F7FEFF",
    "Fusion": "#FFE08A",
    "Glacio": "#E8F7FF",
    "Havoc": "#FFC1DE",
    "Electro": "#F0D7FF",
    "Spectro": "#FFF4B0",
}

_BANNER_RADIUS = 16.0


def _banner_clip_path(width: int, height: int) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, width, height), _BANNER_RADIUS, _BANNER_RADIUS)
    return path


def _apply_rounded_widget_mask(widget: QWidget) -> None:
    mask = QPixmap(widget.size())
    mask.fill(Qt.GlobalColor.transparent)
    painter = QPainter(mask)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.fillPath(_banner_clip_path(widget.width(), widget.height()), Qt.GlobalColor.white)
    painter.end()
    widget.setMask(mask.createMaskFromColor(
        QColor(Qt.GlobalColor.transparent),
        Qt.MaskMode.MaskInColor,
    ))


def _character_element(name: str, element: str | None) -> str:
    if element:
        return element
    return CHARACTER_ELEMENTS.get(name.strip().casefold(), "Spectro")


def _create_rounded_pixmap(pixmap: QPixmap, radius: int = 16) -> QPixmap:
    """Cria um pixmap com cantos arredondados (estilo parenteses ( )) com sombra 3D moderada."""
    print(f"[_create_rounded_pixmap] Aplicando cantos ( ) com sombra 3D moderada")
    
    if pixmap.isNull():
        return pixmap
    
    size = pixmap.size()
    width, height = size.width(), size.height()
    
    # Cria pixmap com tamanho EXATO (960x440)
    result = QPixmap(width, height)
    result.fill(Qt.transparent)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    
    # Cria caminho arredondado (parenteses ( ))
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, width, height), radius, radius)
    
    # Desenha a imagem com cantos recortados
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    # Mantém o clipping ativo também para a sombra e a borda. O traço
    # centrado não pode criar pixels fora dos cantos da moldura.

    # Desenha sombra 3D moderada (não fraca, não forte)
    # Cria gradiente de sombra apenas nas bordas para efeito de profundidade
    shadow_color = QColor(0, 0, 0, 50)  # Aumentado de 25 para 50 (mais visível)
    painter.setPen(Qt.NoPen)
    painter.fillPath(path, shadow_color)
    
    # Desenha borda suave para reforçar o efeito 3D
    pen = painter.pen()
    pen.setColor(QColor(0, 0, 0, 30))
    pen.setWidth(1)
    painter.setPen(pen)
    painter.drawPath(path)
    
    painter.end()
    
    print(f"[_create_rounded_pixmap] Imagem 960x440 com cantos ( ) e sombra 3D criada")
    return result


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None,
                 glow: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        if glow:
            apply_glow(self)


class TitleLabel(QLabel):
    def __init__(self, text: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("title")
        apply_glow(self, blur=10, opacity=90)


class MetricCard(Card):
    def __init__(self, title: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent, glow=False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        label = QLabel(title.upper())
        label.setObjectName("eyebrow")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("metricValue")
        layout.addWidget(label)
        layout.addWidget(self.value_label)


class DataTable(QTableWidget):
    def __init__(self, headers: Iterable[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        labels = list(headers)
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)

    def replace_rows(self, rows: list[list[str]]) -> None:
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.setItem(row_index,
                             column_index,
                             QTableWidgetItem(str(value)))
        self.resizeColumnsToContents()


def form_row(*widgets: QWidget) -> QHBoxLayout:
    layout = QHBoxLayout()
    layout.setSpacing(8)
    for widget in widgets:
        layout.addWidget(widget, 1)
    return layout


class WuWaKuroBannerCard(QFrame):
    """Banner card com moldura e imagem em perfeita harmonia para Wuthering Waves."""
    
    def __init__(self, character_name: str, image_bytes: bytes, end_date: datetime,
                 banner_start: datetime | None = None, element: str | None = None,
                 parent=None):
        super().__init__(parent)
        print(f"[WuWaKuroBannerCard] Inicializando com character_name={character_name}, image_bytes={len(image_bytes) if isinstance(image_bytes, bytes) else 'INVÁLIDO'} bytes")
        self.end_date = end_date
        self.banner_start = banner_start
        self.element = _character_element(character_name, element)
        self.element_color, element_background = ELEMENT_UI_COLORS.get(
            self.element, ELEMENT_UI_COLORS["Spectro"]
        )
        self.element_background = element_background.replace(", 225)", ", 195)")
        self.element_border = self.element_color
        self.number_color = ELEMENT_NUMBER_COLORS.get(self.element, "#FFFFFF")
        self.banner_width = 960
        
        self.setObjectName("KuroHomeSection")
        self.setFixedWidth(960)
        self.setFixedHeight(440)
        self.setStyleSheet("background: transparent;")
        
        # Layout vertical principal da seção
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        
        # --- 1. CONTAINER DA IMAGEM E MOLDURA UNIFICADOS (Overlay Perfeito) ---
        self.img_container = QFrame(self)
        self.img_container.setFixedSize(960, 440)
        self.img_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        _apply_rounded_widget_mask(self.img_container)
        self.img_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)
        
        container_layout = QVBoxLayout(self.img_container)
        container_layout.setContentsMargins(0, 0, 0, 0) # Margem rigorosamente zerada para colar nas bordas
        container_layout.setSpacing(0)
        
        self.img_label = QLabel(self.img_container)
        self.img_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Cola no canto superior esquerdo
        self.img_label.setScaledContents(False)  # Não escalona automaticamente
        self.img_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)
        self.img_label.setFixedSize(960, 440)
        container_layout.addWidget(self.img_label)
        
        # --- HOLOGRAM OVERLAY (Efeito prismatico animado) ---
        self.hologram_overlay = QLabel(self.img_container)
        self.hologram_overlay.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.hologram_overlay.setFixedSize(960, 440)
        self.hologram_overlay.setStyleSheet("background: transparent;")
        self.hologram_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hologram_overlay.setGeometry(0, 0, 960, 440)
        self._apply_hologram_mask()
        self.hologram_overlay.raise_()

        self.countdown_label = QLabel(self.img_container)
        self.countdown_label.setFixedHeight(40)
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: %s;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: bold;
                background-color: %s;
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid %s;
            }
        """ % (self.element_color, self.element_background, self.element_color))
        apply_element_glow(self.countdown_label, self.element, blur=8.0, opacity=110)
        self._position_countdown()
        self.countdown_label.raise_()
        
        # Cria o efeito holografico prismatico
        self.hologram_phase = 0.0
        self._create_hologram_effect()
        
        # Timer para animar o holograma continuamente
        self.hologram_timer = QTimer(self)
        self.hologram_timer.timeout.connect(self._update_hologram)
        self.hologram_timer.start(50)
        
        self.load_image_from_bytes(image_bytes, character_name)
        
        main_layout.addWidget(self.img_container)
        
        # Timer em tempo real segundo a segundo
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_realtime_clock)
        self.timer.start(1000)
        self.refresh_realtime_clock()
        print(f"[WuWaKuroBannerCard] [OK] Inicializacao completa!")

    def _position_countdown(self) -> None:
        margin = 12
        x = max(margin, self.banner_width - self.countdown_label.width() - margin)
        self.countdown_label.move(x, margin)

    def load_image_from_bytes(self, image_bytes: bytes, fallback_name: str):
        """Carrega imagem a partir de bytes já carregados em memória."""
        print(f"[WuWaKuroBannerCard] load_image_from_bytes chamado com {len(image_bytes)} bytes")
        try:
            if not image_bytes or len(image_bytes) == 0:
                raise ValueError("image_bytes vazio")
            
            print(f"[WuWaKuroBannerCard] Criando QPixmap...")
            pixmap = QPixmap()
            loaded = pixmap.loadFromData(QByteArray(image_bytes))
            print(f"[WuWaKuroBannerCard] Pixmap.loadFromData retornou: {loaded}")
            print(f"[WuWaKuroBannerCard] Pixmap isNull: {pixmap.isNull()}, size: {pixmap.size()}")
            
            if not pixmap.isNull():
                # Redimensiona preservando TODO o conteúdo (sem cortar)
                # Container: 960x440
                # Estratégia: SEMPRE escala por ALTURA (440px) - nunca corta topo/bottom
                # Se largura > 960, faz crop APENAS nas laterais
                print(f"[WuWaKuroBannerCard] Escalando pixmap de {pixmap.size()} para altura 440px...")
                
                # Escala por altura mantendo proporção (preserva tudo vertical)
                scaled_pixmap = pixmap.scaledToHeight(
                    440, 
                    Qt.SmoothTransformation
                )
                print(f"[WuWaKuroBannerCard] Após scaledToHeight(440): {scaled_pixmap.size()}")
                
                # Se largura > 960, faz crop APENAS nas laterais (centro)
                if scaled_pixmap.width() > 960:
                    crop_x = (scaled_pixmap.width() - 960) // 2
                    print(f"[WuWaKuroBannerCard] Cortando {crop_x}px de cada lado (esquerda/direita)...")
                    scaled_pixmap = scaled_pixmap.copy(crop_x, 0, 960, 440)
                    print(f"[WuWaKuroBannerCard] Tamanho após crop: {scaled_pixmap.size()}")
                else:
                    # Largura < 960: mantém aspecto correto, sem esticar
                    print(f"[WuWaKuroBannerCard] Imagem cabe perfeitamente (largura {scaled_pixmap.width()} < 960)")

                self.banner_width = scaled_pixmap.width()
                self.setFixedWidth(self.banner_width)
                self.img_container.setFixedSize(self.banner_width, 440)
                self.img_label.setFixedSize(self.banner_width, 440)
                self.hologram_overlay.setFixedSize(self.banner_width, 440)
                self.hologram_overlay.setGeometry(0, 0, self.banner_width, 440)
                _apply_rounded_widget_mask(self.img_container)
                self._position_countdown()
                self._apply_hologram_mask()
                self._update_hologram()
                
                # Aplica cantos arredondados com sombra suave usando QPainterPath
                print(f"[WuWaKuroBannerCard] Aplicando cantos arredondados estilo parentese )...")
                rounded_pixmap = _create_rounded_pixmap(scaled_pixmap, radius=16)
                print(f"[WuWaKuroBannerCard] Pixmap pronto para exibição (960x440 com border-radius)...")
                self.img_label.setPixmap(rounded_pixmap)
                print(f"[WuWaKuroBannerCard] Pixmap setado no label...")
                if self.img_label.pixmap():
                    print(f"[WuWaKuroBannerCard] Label pixmap size: {self.img_label.pixmap().size()}")
                else:
                    print(f"[WuWaKuroBannerCard] [ERROR] Label pixmap eh None!")
                print(f"[WuWaKuroBannerCard] [OK] Imagem carregada com sucesso (SEM RECORTES)!")
                return
        except Exception as e:
            print(f"[WuWaKuroBannerCard] [ERROR] Falha ao carregar arte do banner: {e}")
            import traceback
            traceback.print_exc()
            
        self.img_label.setText(f"[{fallback_name}] - Arte Indisponível")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("color: #d4af37; font-size: 15px; font-weight: bold; background-color: #1a1829; border-radius: 14px;")

    def _create_hologram_effect(self) -> None:
        self._update_hologram()

    def _apply_hologram_mask(self) -> None:
        mask = QPixmap(self.banner_width, 440)
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = _banner_clip_path(self.banner_width, 440)
        painter.fillPath(path, Qt.GlobalColor.white)
        painter.end()
        self.hologram_overlay.setMask(
            mask.createMaskFromColor(
                QColor(Qt.GlobalColor.transparent),
                Qt.MaskMode.MaskInColor,
            )
        )

    def _update_hologram(self) -> None:
        overlay = QPixmap(self.banner_width, 440)
        overlay.fill(Qt.GlobalColor.transparent)

        painter = QPainter(overlay)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        clip_path = _banner_clip_path(self.banner_width, 440)
        painter.setClipPath(clip_path)

        shift = -900.0 + (2400.0 * self.hologram_phase)
        prism = QLinearGradient(-235 + shift, 0, 225 + shift, 440)
        prism.setColorAt(0.20, QColor(255, 70, 120, 0))
        prism.setColorAt(0.34, QColor(255, 70, 120, 31))
        prism.setColorAt(0.41, QColor(255, 220, 80, 38))
        prism.setColorAt(0.47, QColor(110, 245, 150, 30))
        prism.setColorAt(0.53, QColor(90, 240, 255, 43))
        prism.setColorAt(0.59, QColor(70, 130, 255, 32))
        prism.setColorAt(0.65, QColor(150, 100, 255, 31))
        prism.setColorAt(0.72, QColor(255, 70, 180, 0))
        painter.fillRect(0, 0, self.banner_width, 440, prism)

        highlight = QLinearGradient(-105 + shift, 0, 45 + shift, 440)
        highlight.setColorAt(0.44, QColor(255, 255, 255, 0))
        highlight.setColorAt(0.50, QColor(255, 255, 255, 36))
        highlight.setColorAt(0.56, QColor(255, 255, 255, 0))
        painter.fillRect(0, 0, self.banner_width, 440, highlight)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)

        border_gradient = QLinearGradient(0, 0, self.banner_width, 440)
        border_gradient.setColorAt(0.00, QColor(70, 235, 255, 135))
        border_gradient.setColorAt(0.30, QColor(190, 110, 255, 105))
        border_gradient.setColorAt(0.56, QColor(212, 175, 55, 145))
        border_gradient.setColorAt(0.78, QColor(255, 70, 180, 115))
        border_gradient.setColorAt(1.00, QColor(70, 235, 255, 135))

        painter.setPen(QPen(QBrush(border_gradient), 2.5))
        painter.drawPath(_banner_clip_path(self.banner_width, 440))
        painter.setPen(QPen(QBrush(border_gradient), 0.8))
        inner_path = QPainterPath()
        inner_path.addRoundedRect(
            QRectF(5.0, 5.0, self.banner_width - 10, 430), 12, 12
        )
        painter.drawPath(inner_path)

        particle_positions = (
            (0.08, 0.08, 3), (0.21, 0.94, 2), (0.36, 0.06, 2),
            (0.51, 0.91, 3), (0.67, 0.07, 2), (0.82, 0.95, 2),
            (0.94, 0.28, 3), (0.06, 0.67, 2), (0.29, 0.18, 2),
            (0.74, 0.81, 2),
        )
        particle_colors = (
            QColor(75, 235, 255, 180), QColor(255, 95, 190, 165),
            QColor(255, 220, 100, 175), QColor(170, 125, 255, 160),
        )
        for index, (x_ratio, y_ratio, radius) in enumerate(particle_positions):
            drift = math.sin(self.hologram_phase * math.tau + index) * 4.0
            x = x_ratio * self.banner_width + drift
            y = y_ratio * 440 + math.cos(self.hologram_phase * math.tau + index) * 3.0
            glow = QRadialGradient(x, y, radius * 4.5)
            color = particle_colors[index % len(particle_colors)]
            glow.setColorAt(0.0, color)
            glow.setColorAt(0.35, QColor(color.red(), color.green(), color.blue(), 70))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QRectF(x - radius * 4.5, y - radius * 4.5, radius * 9, radius * 9))
            painter.setBrush(QBrush(QColor(255, 255, 255, 190)))
            painter.drawEllipse(QRectF(x - radius * 0.7, y - radius * 0.7, radius * 1.4, radius * 1.4))

        painter.end()

        self.hologram_overlay.setPixmap(overlay)
        self.hologram_phase = (self.hologram_phase + 0.0085) % 1.0

    def refresh_realtime_clock(self):
        """Atualiza o contador em tempo real a cada segundo."""
        now = datetime.now(timezone.utc)
        remaining = self.end_date - now
        total_seconds = int(remaining.total_seconds())
        
        if total_seconds <= 0:
            self.countdown_label.setText("🔴 Convene Encerrado")
            self.countdown_label.setStyleSheet("color: #ff4d4d; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; background: transparent;")
            self.timer.stop()
            return
            
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            countdown_text = f"{days} dias"
        else:
            countdown_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.countdown_label.setText(
            f"Termina em: <span style='color:{self.number_color};'>"
            f"{countdown_text}</span>"
        )
        self.countdown_label.adjustSize()
        self.countdown_label.setFixedHeight(40)
        self._position_countdown()

    def set_active(self, active: bool) -> None:
        """Pause visual effects while the Home tab is outside the viewport."""
        if active:
            if not self.hologram_timer.isActive():
                self.hologram_timer.start(50)
            if self.end_date > datetime.now(timezone.utc) and not self.timer.isActive():
                self.timer.start(1000)
            return
        self.hologram_timer.stop()
        self.timer.stop()
