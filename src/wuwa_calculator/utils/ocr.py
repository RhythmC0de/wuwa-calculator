# captura os stats de uma imagem usando OCR + regex
# para capturar os stats, a imagem precisa estar
# em escala de cinza e com contraste/nitidez aumentados
from __future__ import annotations

import os
import re
import sys
import json
import unicodedata

from pathlib import Path

# Desativa o MKL-DNN por compatibilidade entre builds do PaddlePaddle.
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
# PaddleOCR ainda inclui protos antigos incompatíveis com protobuf 4+.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from paddleocr import PaddleOCR
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.wuwa_calculator.utils.image_processing import prepare_for_ocr  # pylint: disable=wrong-import-position
from src.wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS

SEP = r"\s*[:=]?\s*"
NUMBER = r"([\d.,]+)"
PERCENT = r"\s*%?"

ELEMENTS = (
    "Electro", "Spectro",
    "Havoc", "Fusion",
    "Glacio", "Aero",)

ELEMENT_PATTERN = "|".join(ELEMENTS)

ocr = PaddleOCR(lang="en")

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


def _normalise_character(value: str) -> str:
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "", folded)


def identify_character(text: str) -> str | None:
    """Identifica o personagem pelo nome lido no topo da build card."""
    candidates = text.splitlines()[:8]
    normalised_ids = {
        _normalise_character(character_id): character_id
        for character_id in KNOWN_CHARACTER_IDS
    }
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
    if text.count(",") == 1 and "." not in text:
        text = text.replace(",", ".")
    else:
        text = text.replace(",", "")
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
    print("[Importação] Extraindo informações da imagem...")
    result = ocr.predict(str(path))
    text = extract_text_from_paddle_result(result)
    stats = extract_stats_from_text(text)
    if len(stats) < 3:
        try:
            import numpy as np

            prepared = prepare_for_ocr(path, width=1920)
            enhanced_result = ocr.predict(np.asarray(prepared))
            enhanced_text = extract_text_from_paddle_result(enhanced_result)
            text = "\n".join(part for part in (text, enhanced_text) if part)
        except (OSError, RuntimeError, ValueError):
            pass
    print(f"[Importação] Texto encontrado: {text}")
    return extract_stats_from_text(text), identify_character(text)


if __name__ == "__main__":
    from src.wuwa_calculator.app.main import select_image  # pylint: disable=import-outside-toplevel,no-name-in-module
    img_prepared = prepare_for_ocr(select_image())
    img_prepared.save("utils/ocr_output.png")
    img_prepared.show()
