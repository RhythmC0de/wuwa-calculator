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
import unicodedata
from pathlib import Path

from wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS
from wuwa_calculator.services.characters.identity import normalize_character_id, normalized_id_map
from wuwa_calculator.services.image.image_processing import prepare_for_ocr

log = logging.getLogger(__name__)

SEP = r"\s*[:=]?\s*"
NUMBER = r"([\d.,]+)"
PERCENT = r"\s*%?"

ELEMENTS = (
    "Electro", "Spectro",
    "Havoc", "Fusion",
    "Glacio", "Aero",)

ELEMENT_PATTERN = "|".join(ELEMENTS)

_engine = None


def _require_ocr_engine():
    """Cria o PaddleOCR sob demanda (import e modelos custam segundos/centenas de MB)."""
    global _engine  # pylint: disable=global-statement
    if _engine is not None:
        return _engine
    # Variáveis só são ajustadas quando o OCR é realmente usado, não no import.
    os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "0")
    os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
    try:
        from paddleocr import PaddleOCR
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PaddleOCR não está instalado. Instale as dependências do projeto "
            "com `pip install -r requirements.txt` e tente novamente."
        ) from exc
    _engine = PaddleOCR(lang="en")
    return _engine


STAT_PATTERNS: dict[str, re.Pattern[str]] = {
    "atk": re.compile(
        rf"\bATK\b{SEP}{NUMBER}",
        re.IGNORECASE
        ),
    "hp": re.compile(
        rf"\bHP\b{SEP}{NUMBER}", re.IGNORECASE
        ),
    "def": re.compile(
        rf"\bDEF\b{SEP}{NUMBER}", re.IGNORECASE
        ),
    "crit_rate": re.compile(
        rf"\bCrit(?:ical)?\.?\s*(?:R(?:ate|ote)|Taxa)\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}", re.IGNORECASE
    ),
    "crit_dmg": re.compile(
        rf"\bCrit(?:ical)?\.?\s*(?:DMG|Damage|Dano)\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}", re.IGNORECASE
    ),
    "energy_regen": re.compile(
        rf"\b(?:Energy\s*Regen|Energy\s*Recharge|Recarga\s*de\s*Energia)\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}", re.IGNORECASE
    ),
    "elemental_dmg": re.compile(
        rf"\b{ELEMENT_PATTERN}\b"
        rf"\s*DMG\s*(?:Bonus)?\s*{SEP}{NUMBER}\s*{PERCENT}",
        re.IGNORECASE
    ),
    "heavy_atk_dmg": re.compile(
        rf"\bHeavy\s*Attack\s*DMG\s*(?:Bonus)?\s*\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}", re.IGNORECASE
    ),
    "liberation_dmg": re.compile(
        rf"\b(?:Resonance\s*)?Liberation\s*DMG\s*(?:Bonus)?\s*\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}", re.IGNORECASE
    ),
    "skill_dmg": re.compile(
        rf"\b(?:Resonance\s*)?Skill\s*DMG\s*(?:Bonus)?\s*\b"
        rf"{SEP}{NUMBER}\s*{PERCENT}", re.IGNORECASE
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


def clean_number(raw: str | None) -> float | None:
    """Converte o número reconhecido pelo OCR para float."""
    if raw is None:
        return None
    text = raw.strip().replace("%", "").replace(" ", "")
    if "." in text and "," in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")  # 1.234,5
        else:
            text = text.replace(",", "")  # 1,234.5
    elif "." not in text and re.fullmatch(r"\d+,\d{1,2}", text):
        text = text.replace(",", ".")  # decimal: 12,5
    else:
        text = text.replace(",", "")  # milhar: 1,234
    try:
        return float(text)
    except ValueError:
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
    return stats


def extract_stats_from_image(path: str | Path) -> dict[str, float]:
    """Imagem → PaddleOCR → texto → dicionário de stats."""
    stats, _ = extract_image_data(path)
    return stats


def extract_image_data(path: str | Path) -> tuple[dict[str, float], str | None]:
    """Imagem → texto, atributos reconhecidos e personagem identificado."""
    path = Path(path)
    engine = _require_ocr_engine()
    result = engine.predict(str(path))
    text = extract_text_from_paddle_result(result)
    stats = extract_stats_from_text(text)
    if len(stats) < 3:
        try:
            import numpy as np

            prepared = prepare_for_ocr(path, width=1920)
            enhanced_result = engine.predict(np.asarray(prepared))
            enhanced_text = extract_text_from_paddle_result(enhanced_result)
            text = "\n".join(part for part in (text, enhanced_text) if part)
        except (OSError, RuntimeError, ValueError) as exc:
            log.debug("segunda passada de OCR falhou: %s", type(exc).__name__)
    log.debug("OCR: %d linhas lidas", text.count("\n") + 1)
    return extract_stats_from_text(text), identify_character(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai stats de uma build card via OCR.")
    parser.add_argument("image", help="Caminho da imagem a processar.")
    args = parser.parse_args()

    try:
        stats, detected_character = extract_image_data(args.image)
        print(f"Personagem detectado: {detected_character}")
        print(f"Stats: {stats}")
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
