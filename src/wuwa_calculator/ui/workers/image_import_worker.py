"""OCR import of character stats, isolated from window layout."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ImageCharacterMismatchError(ValueError):
    def __init__(self, detected_id: str, expected_id: str) -> None:
        super().__init__(
            f"A imagem foi identificada como '{detected_id}', "
            f"mas a aba aberta é '{expected_id}'."
        )
        self.detected_id = detected_id
        self.expected_id = expected_id


class ImageImportWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(dict)
    failed = Signal(object)

    def __init__(self, path: str, target_id: str) -> None:
        super().__init__()
        self.path = path
        self.target_id = target_id

    def run(self) -> None:
        try:
            self.status.emit(
                "Baixando componentes para identificar atributos..."
            )
            self.progress.emit(15)
            from wuwa_calculator.services.ocr.service import extract_image_data

            self.progress.emit(35)
            self.status.emit("Carregando dados de status e atributos...")
            self.progress.emit(50)
            self.status.emit("Aplicando leitura de kits e habilidades...")
            self.progress.emit(70)
            stats, detected_id = extract_image_data(self.path)
            if detected_id is not None and detected_id != self.target_id:
                raise ImageCharacterMismatchError(detected_id, self.target_id)
            self.status.emit("Finalizando atributos, bônus e status...")
            self.progress.emit(100)
            self.finished.emit({"stats": stats, "character_id": detected_id})
        except Exception as error:  # pylint: disable=broad-except
            self.failed.emit(error)
