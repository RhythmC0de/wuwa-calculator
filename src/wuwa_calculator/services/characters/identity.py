"""Resolve typed search text to a catalog character ID."""

from __future__ import annotations

import re
import unicodedata

from wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS


def normalize_character_id(value: str) -> str:
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "", folded)


def resolve_character_id(value: str) -> str | None:
    target = normalize_character_id(value)
    return next(
        (
            item
            for item in KNOWN_CHARACTER_IDS
            if normalize_character_id(item) == target
        ),
        None,
    )
