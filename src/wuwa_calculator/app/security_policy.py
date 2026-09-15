"""Runtime security policy for the Tethys PySide6 application."""

from pathlib import Path
from urllib.parse import urlparse

# ! Only reviewed image hosts used by the local character/weapon catalog are allowed.
# Responses are still accepted as pixels only; they are never executed as code.
ALLOWED_REMOTE_HOSTS: frozenset[str] = frozenset({
    "rackoon.com.br",
    "wuwalab.com",
    "i.imgur.com",
})


def allows_remote_content(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and parsed.hostname.casefold() in ALLOWED_REMOTE_HOSTS
    )


def allows_local_image(path: str) -> bool:
    """Allow only bundled/local image references, never executable content."""
    if path.startswith(":/"):
        return True
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(__file__).resolve().parent / candidate
    project_root = Path(__file__).resolve().parent.parent
    try:
        candidate.resolve().relative_to(project_root)
    except ValueError:
        return False
    return candidate.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
