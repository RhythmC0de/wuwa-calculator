"""WuwaTracker banner catalog (public banner-history page) with safe HTTP."""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urljoin

from wuwa_calculator.infrastructure.safe_http import fetch_image_bytes, fetch_text
from wuwa_calculator.infrastructure.url_policy import allows_remote_content

log = logging.getLogger(__name__)

PAGE_URL = "https://wuwatracker.com/pt/banner-history"
FALLBACK_IMAGE_URL = "https://i.imgur.com/JrRW9Bt.jpeg"
QINGXIAO_IMAGE_URL = "https://i.imgur.com/lq6O5Vo.jpeg"  # page icon is missing; pinned override
MAX_CATALOG_ITEMS = 200

# Bounded character classes (no nested ".*?" spanning the whole page) to avoid
# pathological backtracking on a hostile or malformed response.
_PATTERN = re.compile(
    r'"character":\{"name":"(?P<name>[^"]{1,80})",'
    r'"iconSrc":"(?P<icon>[^"]{1,300})".{0,2000}?'
    r'"firstStartDate":"(?P<start>[^"]{1,40})"'
)


def parse_catalog(html: str, page_url: str = PAGE_URL) -> list[dict[str, Any]]:
    """Pure parser: returns catalog entries sorted by start, without images."""
    normalized = html.replace('\\"', '"')
    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in _PATTERN.finditer(normalized):
        name, start, icon = match.group("name"), match.group("start"), match.group("icon")
        if name == "next-size-adjust" or "/api/character-icons/" not in icon or name in seen:
            continue
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        image_url = QINGXIAO_IMAGE_URL if name.casefold() == "qingxiao" else urljoin(page_url, icon)
        if not allows_remote_content(image_url):
            continue
        seen.add(name)
        catalog.append({
            "name": name,
            "image_url": image_url,
            "image_bytes": b"",
            "starts_at": start_date.isoformat(),
            "ends_at": (start_date + timedelta(days=14)).isoformat(),
            "rarity": 5,
            "speculated": False,
            "source": "wuwatracker-page",
        })
        if len(catalog) >= MAX_CATALOG_ITEMS:
            break
    catalog.sort(key=lambda item: item["starts_at"])
    for index in range(len(catalog) - 1):
        catalog[index]["ends_at"] = catalog[index + 1]["starts_at"]
    return catalog


def select_window(catalog: list[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
    """Previous phase, current phase and the next two announced ones."""
    if not catalog:
        return []
    moment = (now or datetime.now(timezone.utc)).isoformat()
    current = next(
        (i for i, item in enumerate(catalog) if item["starts_at"] <= moment <= item["ends_at"]),
        len(catalog) - 1,
    )
    return catalog[max(0, current - 1): min(len(catalog), current + 3)]


def fetch_banner_catalog() -> list[dict[str, Any]]:
    try:
        html = fetch_text(PAGE_URL)
    except Exception as exc:  # network/policy errors must never crash the UI thread
        log.warning("banner catalog unavailable: %s", type(exc).__name__)
        return []
    selected = select_window(parse_catalog(html))

    def load(item: dict[str, Any]) -> None:
        try:
            item["image_bytes"] = fetch_image_bytes(str(item["image_url"]))
        except Exception as exc:
            log.info("banner image for %s unavailable: %s", item["name"], type(exc).__name__)

    if selected:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(load, selected))
    return selected


def fetch_fallback_banner() -> dict[str, Any] | None:
    """Last-resort banner (static image)."""
    try:
        return {
            "name": "Jingyuan",
            "image_bytes": fetch_image_bytes(FALLBACK_IMAGE_URL),
            "ends_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "source": "fallback",
        }
    except Exception as exc:
        log.info("fallback banner unavailable: %s", type(exc).__name__)
        return None
