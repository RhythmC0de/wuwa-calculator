"""Fallback interface for unfinished or unavailable application views."""

from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from wuwa_calculator.ui.components.components import Card, TitleLabel


class PlaceholderTab(QWidget):
    """Explain features or dependencies unavailable in a tab."""

    def __init__(
        self, title: str, description: str, parent: QWidget | None = None
    ) -> None:
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
