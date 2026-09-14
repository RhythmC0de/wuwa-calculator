"""Small local cache for displaying the last banner before network refresh."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any

CACHE_FILE = Path(__file__).resolve().parent / "current_banner.json"
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60


def load_cached_banner() -> dict[str, Any] | None:
    try:
        if time.time() - CACHE_FILE.stat().st_mtime > CACHE_MAX_AGE_SECONDS:
            CACHE_FILE.unlink(missing_ok=True)
            return None
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        encoded = payload.get("image_bytes", "")
        if not isinstance(payload, dict) or not isinstance(encoded, str) or not encoded:
            return None
        payload["image_bytes"] = base64.b64decode(encoded)
        return payload
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        try:
            CACHE_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def save_cached_banner(banner: dict[str, Any]) -> None:
    image_bytes = banner.get("image_bytes")
    if not isinstance(image_bytes, bytes) or not image_bytes:
        return
    payload = {
        key: value
        for key, value in banner.items()
        if key != "image_bytes" and isinstance(value, (str, int, float, bool, type(None)))
    }
    payload["image_bytes"] = base64.b64encode(image_bytes).decode("ascii")
    try:
        CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
