"""Recognize character attributes from OCR text and build-card images."""

# captura os stats de uma imagem usando OCR + regex
# para capturar os stats, a imagem precisa estar
# em escala de cinza e com contraste/nitidez aumentados
from __future__ import annotations

import argparse
import functools
import json
import logging
import os
import re
import sys
from pathlib import Path

from wuwa_calculator.services.characters.identity import (
    normalize_character_id,
    normalized_id_map,
)
from wuwa_calculator.services.image.image_processing import prepare_for_ocr
from wuwa_calculator.services.ocr.layout import (
    FLAT_MINIMUMS,
    TextLine,
    clean_number,
    find_totals,
)

log = logging.getLogger(__name__)

SEP = r"\s*[:=]?\s*"
NUMBER = r"([\d.,]+)"
PERCENT = r"\s*%?"

ELEMENTS = (
    "Electro",
    "Spectro",
    "Havoc",
    "Fusion",
    "Glacio",
    "Aero",
)

ELEMENT_PATTERN = "(?:" + "|".join(ELEMENTS) + ")"


@functools.lru_cache(maxsize=1)
def _require_ocr_engine():
    """Cria o PaddleOCR sob demanda (import e modelos custam segundos/centenas
    de MB)."""
    # Variáveis só são ajustadas quando o OCR é realmente usado, não no import.
    os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "0")
    os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
    try:
        # Load this optional/heavy dependency only when the action runs.
        # pylint: disable-next=import-outside-toplevel
        from paddleocr import PaddleOCR
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PaddleOCR ou uma dependência não está instalado. "
            'Instale o extra com `python -m pip install -e ".[ocr]"` '
            "em um ambiente Python compatível com PaddlePaddle. "
            "O ambiente atual usa Python "
            f"{sys.version_info.major}.{sys.version_info.minor}."
        ) from exc
    return PaddleOCR(lang="en")


STAT_PATTERNS: dict[str, re.Pattern[str]] = {
    "atk": re.compile(rf"\bATK\b{SEP}{NUMBER}", re.IGNORECASE),
    "hp": re.compile(rf"\bHP\b{SEP}{NUMBER}", re.IGNORECASE),
    "def": re.compile(rf"\bDEF\b{SEP}{NUMBER}", re.IGNORECASE),
    "crit_rate": re.compile(
        rf"\bCrit(?:ical)?\.?\s*(?:R(?:ate|ote)|Taxa)\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
    "crit_dmg": re.compile(
        rf"\bCrit(?:ical)?\.?\s*(?:DMG|Damage|Dano)\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
    "energy_regen": re.compile(
        rf"\b(?:Energy\s*Regen|Energy\s*Recharge|Recarga\s*de\s*Energia)\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
    "elemental_dmg": re.compile(
        rf"\b{ELEMENT_PATTERN}\b"
        rf"\s*DMG\s*(?:Bonus)?\s*{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
    "heavy_atk_dmg": re.compile(
        rf"\bHeavy\s*Attack\s*DMG\s*(?:Bonus)?\s*\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
    "liberation_dmg": re.compile(
        rf"\b(?:Resonance\s*)?Liberation\s*DMG\s*(?:Bonus)?\s*\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
    "basic_atk_dmg": re.compile(
        rf"\bBasic\s*Attack\s*DMG\s*(?:Bonus)?\s*\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
    "healing_bonus": re.compile(
        rf"\bHealing\s*Bonus{SEP}{NUMBER}\s*{PERCENT}", re.IGNORECASE
    ),
    "skill_dmg": re.compile(
        rf"\b(?:Resonance\s*)?Skill\s*DMG\s*(?:Bonus)?\s*\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE,
    ),
}


def extract_text_from_paddle_result(result) -> str:
    """Normaliza a saída do PaddleOCR 3.x para um texto único."""
    lines: list[str] = []

    if not isinstance(result, list):
        result = [result]
    for page in result:
        data = getattr(page, "json", page)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                continue
        if not isinstance(data, dict):
            continue
        # algumas versões colocam tudo em "res"
        data = data.get("res", data)
        if not isinstance(data, dict):
            continue
        texts = data.get("rec_texts") or data.get("rec_text") or []
        if isinstance(texts, str):
            texts = [texts]
        for text in texts:
            if text is not None:
                cleaned = str(text).strip()
                if cleaned:
                    lines.append(cleaned)
    return "\n".join(lines)


def lines_from_paddle_result(result) -> list[TextLine]:
    """Linhas com caixa (centro e tamanho)
    a partir da saída do PaddleOCR 3.x."""
    # Keep validation intermediates explicit in this parsing pipeline.
    # pylint: disable=too-many-locals
    lines: list[TextLine] = []
    if not isinstance(result, list):
        result = [result]
    for page in result:
        data = getattr(page, "json", page)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                continue
        if not isinstance(data, dict):
            continue
        data = data.get("res", data)
        if not isinstance(data, dict):
            continue
        texts = data.get("rec_texts") or []
        scores = data.get("rec_scores") or []
        boxes = data.get("rec_boxes")
        if boxes is None:
            boxes = data.get("rec_polys")
        if boxes is None or len(boxes) != len(texts):
            continue
        for index, text in enumerate(texts):
            try:
                box = boxes[index]
                if len(box) == 4 and not hasattr(box[0], "__len__"):
                    x0, y0, x1, y1 = (float(v) for v in box)
                else:
                    xs = [float(point[0]) for point in box]
                    ys = [float(point[1]) for point in box]
                    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            except (TypeError, ValueError, IndexError):
                continue
            confidence = float(scores[index]) if index < len(scores) else 0.0
            lines.append(
                TextLine(
                    str(text).strip(),
                    confidence,
                    (x0 + x1) / 2,
                    (y0 + y1) / 2,
                    x1 - x0,
                    y1 - y0,
                )
            )
    return lines


_normalise_character = normalize_character_id


def _normalised_ids() -> dict[str, str]:
    return normalized_id_map()


def identify_character(text: str) -> str | None:
    """Identifica o personagem pelo nome lido no topo da build card."""
    candidates = text.splitlines()[:8]
    normalised_ids = _normalised_ids()
    for candidate in candidates:
        normalised = _normalise_character(candidate)
        if normalised in normalised_ids:
            return normalised_ids[normalised]
        for normalised_id, character_id in normalised_ids.items():
            if normalised_id and normalised_id in normalised:
                return character_id
    text_normalised = _normalise_character(text)
    for normalised_id, character_id in normalised_ids.items():
        if normalised_id and normalised_id in text_normalised:
            return character_id
    return None


def extract_stats_from_text(text: str) -> dict[str, float]:
    """Texto bruto do OCR → dicionário de atributos."""
    text = re.sub(r"(?i)crit\s*[.:,;]?\s*(dmg|damage|dano)", r"Crit DMG", text)
    text = re.sub(r"(?i)crit\s*[.:,;]?\s*(rate|rote|taxa)", r"Crit Rate", text)
    stats: dict[str, float] = {}
    for key, pattern in STAT_PATTERNS.items():
        match = pattern.search(text)
        if not match:
            continue
        value = clean_number(match.group(1))
        if value is not None:
            stats[key] = value
    # Sem posição não dá para separar o painel de totais dos Echos. Um cartão
    # só com Echos tem ATK 150, HP 430 etc.; se nenhum dos três stats base
    # parece um total, descarta tudo em vez de gravar valores de Echo.
    if not any(
        stats.get(key, 0.0) >= minimum
        for key, minimum in FLAT_MINIMUMS.items()
    ):
        return {}
    return stats


def extract_stats_from_image(path: str | Path) -> dict[str, float]:
    """Imagem → PaddleOCR → texto → dicionário de stats."""
    stats, _ = extract_image_data(path)
    return stats


def extract_image_data(
    path: str | Path,
) -> tuple[dict[str, float], str | None]:
    """Imagem → texto, atributos reconhecidos e personagem identificado."""
    path = Path(path)
    engine = _require_ocr_engine()
    result = engine.predict(str(path))
    text = extract_text_from_paddle_result(result)
    totals = find_totals(lines_from_paddle_result(result))
    if totals is not None:
        return totals, identify_character(text)
    stats = extract_stats_from_text(text)
    if len(stats) < 3:
        try:
            # Load this optional/heavy dependency only when the action runs.
            # pylint: disable-next=import-outside-toplevel
            import numpy as np

            prepared = prepare_for_ocr(path, width=1920)
            enhanced_result = engine.predict(np.asarray(prepared))
            enhanced_text = extract_text_from_paddle_result(enhanced_result)
            enhanced_totals = find_totals(
                lines_from_paddle_result(enhanced_result)
            )
            if enhanced_totals is not None:
                return enhanced_totals, identify_character(
                    "\n".join(part for part in (text, enhanced_text) if part)
                )
            text = "\n".join(part for part in (text, enhanced_text) if part)
        except (OSError, RuntimeError, ValueError) as exc:
            log.debug("segunda passada de OCR falhou: %s", type(exc).__name__)
    log.debug("OCR: %d linhas lidas", text.count("\n") + 1)
    return extract_stats_from_text(text), identify_character(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extrai stats de uma build card via OCR."
    )
    parser.add_argument("image", help="Caminho da imagem a processar.")
    args = parser.parse_args()

    try:
        cli_stats, detected_character = extract_image_data(args.image)
        print(f"Personagem detectado: {detected_character}")
        print(f"Stats: {cli_stats}")
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
