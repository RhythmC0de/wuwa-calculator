import sys
from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QWidget,
)

from src.wuwa_calculator.ui.components.components import Card, TitleLabel


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
