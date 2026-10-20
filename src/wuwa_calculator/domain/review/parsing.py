"""Leitura do texto digitado pelo usuário na correção de um hit.

Exemplos aceitos:
    785 + 2518         dois números diferentes sobrepostos
    2071 x3            o mesmo número três vezes
    17.040 ; 1.151     separador de milhar "." "," ou "'" é ignorado
    430 + 1574 x2      misto
"""

from __future__ import annotations

import re

from .models import MAX_COPIES, MAX_HIT_VALUE, HitPart

_TOKEN = re.compile(r"(\d[\d.,']*)\s*(?:[x×*]\s*(\d{1,3}))?", re.IGNORECASE)
_SEPARATORS = re.compile(r"[\s+;/|]*")


class ParseError(ValueError):
    """Mensagem já pronta para mostrar ao usuário."""


def parse_parts(text: str) -> tuple[HitPart, ...]:
    text = (text or "").strip()
    if not text:
        raise ParseError("Digite pelo menos um valor.")

    parts: list[HitPart] = []
    position = 0
    while position < len(text):
        gap = _SEPARATORS.match(text, position)
        position = gap.end() if gap else position
        if position >= len(text):
            break

        token = _TOKEN.match(text, position)
        if token is None:
            raise ParseError(
                f"Não entendi '{text[position:position + 8]}'. "
                "Use, por exemplo: 785 + 2518   ou   2071 x3"
            )

        digits = re.sub(r"[.,']", "", token.group(1))
        value = int(digits)
        copies = int(token.group(2)) if token.group(2) else 1

        if not 0 < value <= MAX_HIT_VALUE:
            raise ParseError(f"Valor fora do intervalo permitido: {digits}")
        if not 0 < copies <= MAX_COPIES:
            raise ParseError(f"Quantidade de cópias deve ficar entre 1 e {MAX_COPIES}.")

        parts.append(HitPart(value, copies))
        position = token.end()

    if not parts:
        raise ParseError("Digite pelo menos um valor.")
    return tuple(parts)


def format_parts(parts: tuple[HitPart, ...]) -> str:
    """Inverso de parse_parts, para preencher o campo de texto."""
    return " + ".join(
        f"{p.value}" + (f" x{p.copies}" if p.copies > 1 else "") for p in parts
    )
