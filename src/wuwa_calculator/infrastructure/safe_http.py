"""Minimal HTTPS client: allowlisted hosts, revalidated redirects, size caps."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from wuwa_calculator.infrastructure.url_policy import allows_remote_content

USER_AGENT = "Tethys/1.4 (+desktop)"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_HTML_BYTES = 8 * 1024 * 1024
MAX_REDIRECTS = 3


class BlockedURL(ValueError):
    """Raised when a URL is outside the allowlist."""


class _Redirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, check: Callable[[str], bool]) -> None:
        self._check = check
        self.max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        if not self._check(newurl):
            raise BlockedURL(f"redirect blocked: {newurl[:80]}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bytes(
    url: str,
    *,
    max_bytes: int,
    timeout: float = 8,
    accept: str = "*/*",
    check: Callable[[str], bool] = allows_remote_content,
) -> bytes:
    if not check(url):
        raise BlockedURL(f"url not allowed: {url[:80]}")
    opener = urllib.request.build_opener(_Redirect(check))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with opener.open(request, timeout=timeout) as response:  # nosec B310 - validated above
        declared = response.headers.get("Content-Length")
        if declared and declared.isdigit() and int(declared) > max_bytes:
            raise ValueError("response too large")
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("response too large")
    return data


def fetch_json(url: str, *, timeout: float = 8) -> Any:
    return json.loads(fetch_bytes(url, max_bytes=MAX_JSON_BYTES, timeout=timeout, accept="application/json").decode("utf-8"))


def fetch_image_bytes(url: str, *, timeout: float = 10) -> bytes:
    return fetch_bytes(url, max_bytes=MAX_IMAGE_BYTES, timeout=timeout, accept="image/*")


def fetch_text(url: str, *, timeout: float = 12) -> str:
    return fetch_bytes(url, max_bytes=MAX_HTML_BYTES, timeout=timeout, accept="text/html").decode("utf-8", errors="replace")


def post_json(url: str, body: dict[str, Any], *, timeout: float = 10, check: Callable[[str], bool], max_bytes: int = MAX_JSON_BYTES) -> Any:
    if not check(url):
        raise BlockedURL(f"url not allowed: {url[:80]}")
    opener = urllib.request.build_opener(_Redirect(check))
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    with opener.open(request, timeout=timeout) as response:  # nosec B310
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("response too large")
    return json.loads(data.decode("utf-8"))
