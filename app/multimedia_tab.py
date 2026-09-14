"""Dedicated multimedia workspace for rotation-reference videos."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

# Allow direct execution from the app/ directory while keeping package imports
# as the canonical path used by the Tethys launcher.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.components import Card, TitleLabel
from app.history_video_player import HistoryVideoPlayer


class MultimediaTab(QWidget):
    """Full video workspace kept separate from rotation-history records."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        intro = Card()
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(16, 14, 16, 14)
        intro_layout.addWidget(TitleLabel("Multimídia"))
        description = QLabel(
            "Importe gravações de suas rotações para análise de desempenho, "
            "comparação de dano real e auditoria de habilidades."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        intro_layout.addWidget(description)
        layout.addWidget(intro)

        self.video_player = HistoryVideoPlayer()
        layout.addWidget(self.video_player, 1)

    def closeEvent(self, event) -> None:
        self.video_player.stop_video()
        super().closeEvent(event)
