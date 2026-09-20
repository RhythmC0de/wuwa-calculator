"""Modal wrapper around the settings tab."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QWidget

from wuwa_calculator.ui.tabs.settings_tab import SettingsTab


class SettingsDialog(QDialog):
    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setWindowTitle("Configurações | Tethys")
        self.setModal(True)
        self.setMinimumSize(760, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(SettingsTab(self, host=host), 1)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
