"""Read image text with the native engine (``damage_analyzer.read_text``).

The engine runs in a separate process (``infrastructure.text_reading``).
Returns lines in the format ``layout.find_totals`` expects. If the engine
cannot be used (not built, old API or no ``models/ocr/ppocrv5_det.onnx``),
returns ``None`` and the caller uses the other reader.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from wuwa_calculator.services.ocr.layout import TextLine

log = logging.getLogger(__name__)

_warned: set[str] = set()


def _warn_once(message: str) -> None:
    if message not in _warned:
        _warned.add(message)
        log.warning("%s", message)


def is_enabled() -> bool:
    """TETHYS_STATS_OCR=paddle turns the native reader off for stats."""
    return os.environ.get("TETHYS_STATS_OCR", "").strip().lower() != "paddle"


def read_lines(
    path: str | Path, *, enhance: bool = False
) -> list[TextLine] | None:
    """Lines read by the native engine, or None when it is unavailable."""
    if not is_enabled():
        return None
    # Pure-Python module (no Qt); imported here to keep startup light.
    # pylint: disable-next=import-outside-toplevel
    from wuwa_calculator.infrastructure import text_reading

    try:
        raw = text_reading.read_lines_isolated(path, enhance=enhance)
    except text_reading.EngineUnavailableError as error:
        _warn_once(f"engine nativa indisponível para ler stats: {error}")
        return None
    except RuntimeError as error:
        _warn_once(f"engine nativa falhou ao ler a imagem: {error}")
        return None

    return [
        TextLine(
            str(item["text"]),
            float(item["confidence"]),
            float(item["x"]),
            float(item["y"]),
            float(item["width"]),
            float(item["height"]),
        )
        for item in raw
    ]
