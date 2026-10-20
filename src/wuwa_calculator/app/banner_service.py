"""Fetch the current Wuthering Waves banner into memory."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from wuwa_calculator.infrastructure.safe_http import MAX_IMAGE_BYTES, MAX_JSON_BYTES, fetch_bytes
from wuwa_calculator.infrastructure.url_policy import allows_remote_content

log = logging.getLogger(__name__)

DEFAULT_API_URL = (
    "https://gist.githubusercontent.com/yloove7/"
    "b1440f18d4c1152f9f3914fbdb2b7b14/raw/gistfile1.txt"
)
API_URL = DEFAULT_API_URL  # fixed: an env override would bypass the URL allowlist


def _request_bytes(url: str, cache_bust: bool = False, timeout: int = 8) -> bytes:
    if cache_bust:
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query))
        query["tethys_ts"] = str(int(time.time()))
        url = urlunsplit(parts._replace(query=urlencode(query)))
    is_image = url != API_URL
    return fetch_bytes(
        url,
        max_bytes=MAX_IMAGE_BYTES if is_image else MAX_JSON_BYTES,
        timeout=timeout,
        accept="image/*" if is_image else "application/json",
    )


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    
    for key in ("banners", "featured", "events", "data", "results"):
        nested = payload.get(key)
        if isinstance(nested, list):
            result = [item for item in nested if isinstance(item, dict)]
            return result
    return [payload]


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _parse_timestamp(value: Any) -> str | None:
    
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    
    if not isinstance(value, str) or not value.strip():
        return None
    
    text = value.strip().replace("Z", "+00:00")
    
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    
    result = parsed.astimezone(timezone.utc).isoformat()
    return result


def _normalise_banner(item: dict[str, Any]) -> dict[str, Any] | None:
    
    character = item.get("character")
    
    if isinstance(character, dict):
        name = _first(character, "name", "title", "id")
        image_url = _first(character, "image", "imageUrl", "image_url", "icon")
    else:
        name = character or _first(item, "name", "title", "characterName")
        image_url = None

    image_url = image_url or _first(
        item, "image", "imageUrl", "image_url", "bannerImage", "art"
    )
    
    end_value = _first(
        item, "endTime", "end_time", "endDate", "end_date", "endsAt", "end"
    )
    
    ends_at = _parse_timestamp(end_value)
    
    if image_url and not allows_remote_content(str(image_url)):
        log.warning("imagem do banner bloqueada (host fora da lista): %s", urlsplit(str(image_url)).hostname)
        return None
    if not name or not image_url or not ends_at:
        return None
    
    result = {
        "name": str(name),
        "image_url": str(image_url),
        "ends_at": ends_at,
    }
    return result


def _select_active(payload: Any) -> dict[str, Any] | None:
    candidates = _as_list(payload)
    
    now = datetime.now(timezone.utc)
    
    normalised: list[dict[str, Any]] = []
    for item in candidates:
        banner = _normalise_banner(item)
        if banner is None:
            continue
        try:
            end = datetime.fromisoformat(banner["ends_at"])
        except ValueError:
            continue
        if end > now:
            normalised.append(banner)

    if not normalised:
        return None
    
    result = min(normalised, key=lambda item: item["ends_at"])
    return result


def fetch_current_banner() -> dict[str, Any] | None:
    """Fetch the active banner and keep its image bytes in memory only."""
    try:
        payload = json.loads(
            _request_bytes(API_URL, timeout=6).decode("utf-8")
        )
        
        banner = _select_active(payload)
        
        if banner is None:
            raise ValueError("nenhum banner ativo com imagem em host permitido na resposta da API")
        
        image_bytes = _request_bytes(banner["image_url"], timeout=8)
        
        banner["image_bytes"] = image_bytes
        return banner
    except (OSError, URLError, ValueError, json.JSONDecodeError) as e:
        log.warning("banner fetch failed: %s: %s", type(e).__name__, e)
        return None
