"""Resolve typed search text to a catalog character ID."""

from __future__ import annotations

import functools
import re
import unicodedata

from wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS


def normalize_character_id(value: str) -> str:
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "", folded)


@functools.lru_cache(maxsize=1)
def normalized_id_map() -> dict[str, str]:
    """normalized -> canonical id (built once; the catalog is static)."""
    return {normalize_character_id(item): item for item in sorted(KNOWN_CHARACTER_IDS)}


def resolve_character_id(value: str) -> str | None:
    return normalized_id_map().get(normalize_character_id(value))
