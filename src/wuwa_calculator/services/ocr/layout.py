"""Leitura dos stats a partir de linhas de texto com posição.

Independente de Qt e do motor de OCR: recebe `TextLine` (texto, confiança e
caixa) e devolve os stats do painel de totais. A engine nativa ou o PaddleOCR
só precisam produzir essas linhas.

Ideia: achar cada rótulo ("Crit. Rate"), pegar o número na mesma linha à
direita e só aceitar um painel que tenha cara de totais do personagem. Isso
funciona em layouts diferentes (1 ou 2 colunas, total com bônus embaixo) e
rejeita cartões que só mostram Echos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Painel de totais precisa de pelo menos estes stats e deste tamanho.
MIN_PANEL_KEYS = 7
CORE_KEYS = ("hp", "atk", "def")
FLAT_MINIMUMS = {"hp": 1500.0, "atk": 200.0, "def": 100.0}
MAX_PERCENT = 400.0


@dataclass(frozen=True)
class TextLine:
    """Uma linha lida pelo OCR. x e y são o centro da caixa, em pixels."""

    text: str
    confidence: float
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        """Return the left."""
        return self.x - self.width / 2

    @property
    def right(self) -> float:
        """Return the right."""
        return self.x + self.width / 2


_ELEMENTS = r"(?:electro|spectro|havoc|fusion|glacio|aero)"
_PREFIX = r"(?:res\.?\s*|resonance\s*)?"

LABELS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (key, re.compile(pattern))
    for key, pattern in (
        ("hp", r"hp"),
        ("atk", r"atk"),
        ("def", r"def"),
        (
            "energy_regen",
            r"(?:energy\s*(?:regen|recharge)|recarga\s*de\s*energia)",
        ),
        ("crit_rate", r"crit(?:ical)?\.?\s*(?:rate|rote|taxa)"),
        ("crit_dmg", r"crit(?:ical)?\.?\s*(?:dmg|damage|dano)"),
        ("elemental_dmg", rf"{_ELEMENTS}\s*dmg(?:\s*bonus)?"),
        ("basic_atk_dmg", r"basic\s*attack\s*dmg(?:\s*bonus)?"),
        ("heavy_atk_dmg", r"heavy\s*attack\s*dmg(?:\s*bonus)?"),
        ("skill_dmg", rf"{_PREFIX}skill\s*dmg(?:\s*bonus)?"),
        ("liberation_dmg", rf"{_PREFIX}liberation\s*dmg(?:\s*bonus)?"),
        ("healing_bonus", r"healing\s*bonus"),
    )
)

_NUMBER = r"\d[\d.,]*"
_VALUE_ONLY = re.compile(rf"^{_NUMBER}\s*%?$")
_LABEL_AND_VALUE = re.compile(
    rf"^(?P<label>.+?)\s*[:=]?\s*(?P<value>{_NUMBER})\s*%?$"
)


def clean_number(raw: str | None) -> float | None:
    """Converte o número lido pelo OCR para float."""
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


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def classify_label(text: str) -> str | None:
    """Match an OCR line to a recognized character attribute label."""
    cleaned = _normalise(text).rstrip(":=")
    for key, pattern in LABELS:
        if pattern.fullmatch(cleaned):
            return key
    return None


@dataclass(frozen=True)
class _Pair:
    key: str
    value: float
    is_percent: bool
    label: TextLine
    value_line: TextLine | None


def _is_value(line: TextLine) -> bool:
    # "12450 + 5030.0" e "+70.5%" (bônus embaixo do total) não são totais.
    return bool(_VALUE_ONLY.fullmatch(line.text.strip()))


def _pairs(lines: list[TextLine]) -> list[_Pair]:
    # Keep validation intermediates explicit in this parsing pipeline.
    # pylint: disable=too-many-locals
    labels: list[tuple[str, TextLine]] = []
    values: list[TextLine] = []
    pairs: list[_Pair] = []

    for line in lines:
        key = classify_label(line.text)
        if key is not None:
            labels.append((key, line))
            continue
        if _is_value(line):
            values.append(line)
            continue
        combined = _LABEL_AND_VALUE.match(_normalise(line.text))
        if combined:
            key = classify_label(combined.group("label"))
            number = clean_number(combined.group("value"))
            if key is not None and number is not None:
                pairs.append(_Pair(key, number, "%" in line.text, line, None))

    for key, label in labels:
        band = max(label.height, 8.0) * 0.9
        candidates = []
        for value in values:
            if abs(value.y - label.y) > band:
                continue
            if value.left < label.x:
                continue
            # o número pertence ao rótulo mais próximo à esquerda dele
            blocked = any(
                other is not label
                and abs(other.y - value.y) <= band
                and label.right <= other.left < value.left
                for _, other in labels
            )
            if not blocked:
                candidates.append(value)
        if not candidates:
            continue
        tallest = max(v.height for v in candidates)
        large = [v for v in candidates if v.height >= tallest * 0.7]
        best = min(large, key=lambda v, right=label.right: v.left - right)
        number = clean_number(best.text)
        if number is not None:
            pairs.append(_Pair(key, number, "%" in best.text, label, best))
    return pairs


def _plausible(stats: dict[str, _Pair]) -> bool:
    for key in CORE_KEYS:
        pair = stats.get(key)
        if pair is None or pair.is_percent or pair.value < FLAT_MINIMUMS[key]:
            return False
    for key, pair in stats.items():
        if key not in CORE_KEYS and pair.value > MAX_PERCENT:
            return False
    return True


def _columns(pairs: list[_Pair], tolerance: float) -> list[list[_Pair]]:
    columns: list[list[_Pair]] = []
    for pair in sorted(pairs, key=lambda p: p.label.left):
        for column in columns:
            if abs(column[0].label.left - pair.label.left) <= tolerance:
                column.append(pair)
                break
        else:
            columns.append([pair])
    return columns


def _first_by_key(pairs: list[_Pair]) -> dict[str, _Pair]:
    result: dict[str, _Pair] = {}
    for pair in sorted(pairs, key=lambda p: p.label.y):
        result.setdefault(pair.key, pair)
    return result


def _y_overlap(a: list[_Pair], b: list[_Pair]) -> bool:
    a0, a1 = min(p.label.y for p in a), max(p.label.y for p in a)
    b0, b1 = min(p.label.y for p in b), max(p.label.y for p in b)
    overlap = min(a1, b1) - max(a0, b0)
    return overlap >= 0.5 * min(a1 - a0, b1 - b0)


def find_totals(lines: list[TextLine]) -> dict[str, float] | None:
    """Stats do painel de totais, ou None se o cartão não tem esse painel.

    Cartões que mostram só Echos (cada Echo com seus subatributos) também têm
    "ATK 150" e "Crit. Rate 7.5%"; eles são rejeitados porque os valores fixos
    de um Echo não passam pela checagem de plausibilidade dos totais.
    """
    pairs = _pairs(lines)
    if not pairs:
        return None
    width = max((line.right for line in lines), default=1.0)
    columns = _columns(pairs, tolerance=max(8.0, 0.012 * width))

    candidates: list[dict[str, _Pair]] = []
    for i, first in enumerate(columns):
        candidates.append(_first_by_key(first))
        for second in columns[i + 1 :]:
            if _y_overlap(first, second):
                candidates.append(_first_by_key(first + second))

    best: dict[str, _Pair] | None = None
    for stats in candidates:
        if len(stats) < MIN_PANEL_KEYS or not _plausible(stats):
            continue
        if best is None or len(stats) > len(best):
            best = stats
    if best is None:
        return None
    return {key: pair.value for key, pair in best.items()}
