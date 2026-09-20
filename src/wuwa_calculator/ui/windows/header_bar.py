"""Top search/import bar of the main window."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from wuwa_calculator.ui.components.components import Card, TitleLabel


class HeaderBar(Card):
    search_submitted = Signal()
    import_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.addWidget(TitleLabel("Tethys System"))
        layout.addStretch(1)

        self.character_id_entry = QLineEdit()
        self.character_id_entry.setPlaceholderText(
            "Digite o nome do(a) personagem..."
        )
        self.character_id_entry.setFixedWidth(210)
        self.character_id_entry.returnPressed.connect(self.search_submitted)

        self.character_load_button = QPushButton("Buscar")
        self.character_load_button.setObjectName("primaryAction")
        self.character_load_button.clicked.connect(self.search_submitted)

        self.import_button = QPushButton("Carregar Stats")
        self.import_button.setObjectName("primaryAction")
        self.import_button.clicked.connect(self.import_clicked)

        self.character_status = QLabel("")
        self.character_status.setObjectName("onlineStatus")

        layout.addWidget(self.character_id_entry)
        layout.addWidget(self.character_load_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.character_status)

    def query(self) -> str:
        return self.character_id_entry.text()

    def set_status(self, text: str) -> None:
        self.character_status.setText(text)
