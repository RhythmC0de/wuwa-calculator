"""Pure URL allowlist policy (no Qt, no network, no filesystem writes)."""

from __future__ import annotations

import ipaddress
from pathlib import Path
from urllib.parse import urlsplit

# Reviewed image/data hosts. Exact match or a subdomain of the entry.
ALLOWED_REMOTE_HOSTS: frozenset[str] = frozenset({
    "rackoon.com.br",
    "wuwalab.com",
    "i.imgur.com",
    "wuwatracker.com",                    # banner catalog + icons
    "gist.githubusercontent.com",         # banner JSON
})

# Hosts that receive the player's gacha-record parameters (POST). Kept apart on
# purpose: image hosts must never receive those credentials.
GACHA_API_HOST_SUFFIXES: tuple[str, ...] = ("aki-game2.com", "aki-game2.net", "kurogames.com")

_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp"})


def _host_matches(host: str, allowed: tuple[str, ...] | frozenset[str]) -> bool:
    host = host.casefold().rstrip(".")
    return any(host == entry or host.endswith("." + entry) for entry in allowed)


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def _https_ok(url: object) -> tuple[bool, str]:
    if not isinstance(url, str) or not url or len(url) > 2048 or any(c in url for c in "\r\n\t "):
        return False, ""
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError:
        return False, ""
    if parts.scheme != "https" or not host or parts.username or parts.password:
        return False, ""
    if port not in (None, 443) or _is_ip_literal(host):
        return False, ""
    return True, host


def allows_remote_content(url: object) -> bool:
    ok, host = _https_ok(url)
    return ok and _host_matches(host, ALLOWED_REMOTE_HOSTS)


def allows_gacha_api(url: object) -> bool:
    ok, host = _https_ok(url)
    return ok and _host_matches(host, GACHA_API_HOST_SUFFIXES)


def allows_local_image(path: str, *, roots: tuple[Path, ...] | None = None) -> bool:
    """Bundled (``:/``) or image files that resolve inside an approved root."""
    if path.startswith(":/"):
        return True
    package_root = Path(__file__).resolve().parent.parent
    approved = roots if roots is not None else (package_root, package_root.parent.parent / "Assets")
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = package_root / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    if resolved.suffix.casefold() not in _IMAGE_SUFFIXES:
        return False
    for root in approved:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False
