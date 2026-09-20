"""About dialog for Tethys System."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wuwa_calculator.ui.components.components import TitleLabel

VERSION = "1.4.0"


def _readme_path() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    for name in ("README.md", "README.txt"):
        candidate = repo_root / name
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parents[2] / "README.txt"


class AboutDialog(QDialog):
    VERSION = VERSION

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setWindowTitle("Sobre | Tethys System")
        self.setModal(True)
        self.setMinimumSize(560, 430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(TitleLabel("Tethys System"))

        description = QLabel(
            "O Tethys System é o terminal central de Black Shores: "
            "um sistema dedicado a observar, analisar e compreender o Lamento. "
            "Nesta aplicação, seus cálculos são usados para estudar personagens, "
            "equipes, rotações e dano em Wuthering Waves."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        info = QLabel(
            f"Versão: {self.VERSION}\n"
            "Sistema: Tethys System\n"
            "Licença: MIT"
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        notes = QLabel(
            "Assim como o terminal de Black Shores, o Tethys System organiza "
            "informações para interpretar eventos complexos. Os dados do jogo "
            "são usados localmente para apoiar análises e simulações. "
            "Consulte o README para conhecer o sistema e seus recursos."
        )
        notes.setObjectName("muted")
        notes.setWordWrap(True)
        layout.addWidget(notes)
        layout.addStretch(1)

        actions = QHBoxLayout()
        readme_button = QPushButton("Abrir README")
        readme_button.clicked.connect(self._open_readme)
        actions.addWidget(readme_button)
        copy_button = QPushButton("Copiar diagnóstico")
        copy_button.clicked.connect(self._copy_diagnostic)
        actions.addWidget(copy_button)
        actions.addStretch(1)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def _open_readme(self) -> None:
        readme = _readme_path()
        if readme.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(readme)))
            return
        QMessageBox.information(
            self,
            "README não encontrado",
            "O arquivo README não foi encontrado.",
        )

    def _copy_diagnostic(self) -> None:
        diagnostic = (
            f"Tethys System {self.VERSION}\n"
            f"Diretório: {Path.cwd()}"
        )
        QApplication.clipboard().setText(diagnostic)
        QMessageBox.information(
            self,
            "Diagnóstico copiado",
            "As informações foram copiadas para a área de transferência.",
        )
