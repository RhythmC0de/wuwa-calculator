"""Shared pixmap scaling, centering, and alpha masks for Qt artwork."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


def smooth_scaled(
    source: QPixmap, width: int, height: int, aspect: Qt.AspectRatioMode
) -> QPixmap:
    """Scale artwork with the requested aspect policy and smooth filtering."""
    return source.scaled(
        width, height, aspect, Qt.TransformationMode.SmoothTransformation
    )


def transparent_pixmap(size: QSize) -> QPixmap:
    """Create a fully transparent canvas of the requested size."""
    canvas = QPixmap(size)
    canvas.fill(Qt.GlobalColor.transparent)
    return canvas


def draw_centered(
    painter: QPainter, source: QPixmap, width: int, height: int
) -> None:
    """Draw artwork centered within the supplied canvas dimensions."""
    x = (width - source.width()) // 2
    y = (height - source.height()) // 2
    painter.drawPixmap(x, y, source)


def apply_alpha_mask(widget: QWidget, mask: QPixmap) -> None:
    """Use the transparent pixels of a pixmap as the widget's mask."""
    widget.setMask(
        mask.createMaskFromColor(
            QColor(Qt.GlobalColor.transparent), Qt.MaskMode.MaskInColor
        )
    )
