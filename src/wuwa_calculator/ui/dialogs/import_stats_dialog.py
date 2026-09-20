"""Dialog that imports resonator stats from a screenshot."""

from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wuwa_calculator.ui.tabs.resonator_tab import ResonatorTab
from wuwa_calculator.ui.workers.image_import_worker import (
    ImageCharacterMismatchError,
    ImageImportWorker,
)


class ImportDialog(QDialog):
    def __init__(self, parent: QWidget, character_tab: ResonatorTab) -> None:
        super().__init__(parent)
        self.character_tab = character_tab

        self.setWindowTitle("Importar dados")
        self.resize(500, 400)

        layout = QVBoxLayout(self)
        title = QLabel("Importar dados de uma imagem")
        self.select_button = QPushButton("Selecionar imagem")
        self.select_button.clicked.connect(self.select_image)
        self.status_label = QLabel(
            "Selecione uma screenshot para importar os dados."
        )
        self.status_label.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()

        layout.addWidget(title)
        layout.addWidget(self.select_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        self.ocr_thread: QThread | None = None
        self.ocr_worker: ImageImportWorker | None = None

    def select_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp)",
        )
        if not path:
            return

        self.select_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("Preparando importação...")

        self.ocr_thread = QThread(self)
        self.ocr_worker = ImageImportWorker(path, self.character_tab.current_id)
        self.ocr_worker.moveToThread(self.ocr_thread)
        self.ocr_thread.started.connect(self.ocr_worker.run)
        self.ocr_worker.progress.connect(self.progress_bar.setValue)
        self.ocr_worker.status.connect(self.status_label.setText)
        self.ocr_worker.finished.connect(self._import_finished)
        self.ocr_worker.failed.connect(self._import_failed)
        self.ocr_worker.finished.connect(self.ocr_thread.quit)
        self.ocr_worker.failed.connect(self.ocr_thread.quit)
        self.ocr_thread.finished.connect(self._clear_import_worker)
        self.ocr_thread.start()

    def _import_finished(self, result: dict) -> None:
        self.select_button.setEnabled(True)
        stats = result.get("stats", {})
        if stats:
            self.character_tab.apply_imported_stats(stats)
            message = "Stats extraídos:\n" + "\n".join(
                f"{key}: {value}" for key, value in stats.items()
            )
            self.status_label.setText("Importação concluída.")
            QMessageBox.information(self, "Dados importados", message)
            self.accept()
            return

        message = (
            "Não foi possível encontrar informações na imagem.\n\n"
            "Verifique se a screenshot contém os atributos do personagem."
        )
        self.status_label.setText(message)
        QMessageBox.critical(self, "Nenhum dado encontrado", message)

    def _import_failed(self, error: object) -> None:
        self.select_button.setEnabled(True)
        if isinstance(error, FileNotFoundError):
            message = "Arquivo não encontrado."
            title = "Erro ao importar"
        elif isinstance(error, ImageCharacterMismatchError):
            message = (
                f"Esta imagem pertence a '{error.detected_id}', mas a aba "
                f"aberta é '{error.expected_id}'. Carregue a ID correta "
                "antes de importar esta build card."
            )
            title = "Personagem incompatível"
        elif isinstance(error, (OSError, ValueError)):
            message = (
                "Não foi possível ler a imagem. Verifique se o arquivo é "
                "uma imagem válida e tente novamente."
            )
            title = "Erro ao importar"
        elif isinstance(error, ImportError):
            message = (
                "O recurso de ler imagens não está disponível. "
                "Uma dependência necessária não está instalada."
            )
            title = "Recurso indisponível"
        elif isinstance(error, RuntimeError):
            message = (
                "Não foi possível processar a imagem. Tente novamente "
                "ou utilize outra imagem."
            )
            title = "Erro ao processar"
        else:
            message = (
                "Ocorreu um erro inesperado ao processar a imagem. "
                "Se o problema persistir, reporte o erro."
            )
            title = "Erro inesperado"

        self.status_label.setText(message)
        QMessageBox.critical(self, title, message)

    def _clear_import_worker(self) -> None:
        if self.ocr_worker is not None:
            self.ocr_worker.deleteLater()
        if self.ocr_thread is not None:
            self.ocr_thread.deleteLater()
        self.ocr_worker = None
        self.ocr_thread = None
