"""Idioma do aplicativo: um valor só, salvo entre execuções.

Quem mostra texto traduzido lê ``language_settings().code`` e se inscreve em
``changed`` para redesenhar quando o usuário trocar. Os códigos são os mesmos
já usados pela interface ("PT-BR", "EN"); o catálogo aceita qualquer caixa.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Signal

SUPPORTED = ("PT-BR", "EN")
DEFAULT = "PT-BR"


def _canonical(code: str) -> str:
    wanted = (code or "").strip().casefold().replace("_", "-")
    return next((item for item in SUPPORTED if item.casefold() == wanted), DEFAULT)


class LanguageSettings(QObject):
    changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("Tethys", "Tethys")
        self._code = _canonical(str(self._settings.value("ui/language", DEFAULT)))

    @property
    def code(self) -> str:
        return self._code

    def set_language(self, code: str) -> None:
        canonical = _canonical(code)
        if canonical == self._code:
            return
        self._code = canonical
        self._settings.setValue("ui/language", canonical)
        self.changed.emit(canonical)


_instance: LanguageSettings | None = None


def language_settings() -> LanguageSettings:
    global _instance
    if _instance is None:
        _instance = LanguageSettings()
    return _instance
