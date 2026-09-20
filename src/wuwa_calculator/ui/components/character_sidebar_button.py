from PySide6.QtWidgets import (
    QPushButton,
    QToolButton,
    QWidget,
)
from PySide6.QtCore import Signal   


class CharacterSidebarButton(QPushButton):
    close_requested = Signal()

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.close_button = QToolButton(self)
        self.close_button.setObjectName("tabClose")
        self.close_button.setText("×")
        self.close_button.setToolTip("Fechar aba")
        self.close_button.setFixedSize(22, 22)
        self.close_button.clicked.connect(self.close_requested)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.close_button.move(
            self.width() - self.close_button.width() - 5,
            (self.height() - self.close_button.height()) // 2,
        )
