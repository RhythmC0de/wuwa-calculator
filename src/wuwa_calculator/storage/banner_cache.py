"""Small local cache for displaying the last banner before network refresh."""

from __future__ import annotations

import base64
import binascii
import time
from pathlib import Path
from typing import Any

from wuwa_calculator.storage.atomic import read_json, write_json
from wuwa_calculator.storage.paths import user_cache_dir

CACHE_FILE = user_cache_dir() / "current_banner.json"
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60
MAX_IMAGE_BYTES = 6 * 1024 * 1024


def load_cached_banner(path: Path = CACHE_FILE) -> dict[str, Any] | None:
    try:
        if time.time() - path.stat().st_mtime > CACHE_MAX_AGE_SECONDS:
            path.unlink(missing_ok=True)
            return None
    except OSError:
        return None
    payload = read_json(path, None, max_bytes=MAX_IMAGE_BYTES * 2)
    if not isinstance(payload, dict):
        return None
    encoded = payload.get("image_bytes", "")
    if not isinstance(encoded, str) or not encoded:
        return None
    try:
        payload["image_bytes"] = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None
    return payload


def save_cached_banner(banner: dict[str, Any], path: Path = CACHE_FILE) -> None:
    image_bytes = banner.get("image_bytes")
    if not isinstance(image_bytes, bytes) or not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        return
    payload = {
        key: value
        for key, value in banner.items()
        if key != "image_bytes" and isinstance(value, (str, int, float, bool, type(None)))
    }
    payload["image_bytes"] = base64.b64encode(image_bytes).decode("ascii")
    try:
        write_json(path, payload, indent=None)
    except OSError:
        pass
