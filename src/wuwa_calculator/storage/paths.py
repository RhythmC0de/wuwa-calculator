"""Per-user writable locations (never inside the installed package)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "Tethys"


def _base(kind: str) -> Path:
    override = os.environ.get("TETHYS_HOME")
    if override:
        return Path(override).expanduser().resolve() / kind
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        key = "XDG_DATA_HOME" if kind == "data" else "XDG_CACHE_HOME"
        fallback = Path.home() / (".local/share" if kind == "data" else ".cache")
        return Path(os.environ.get(key) or fallback) / APP_DIR_NAME.lower()
    return root / APP_DIR_NAME / kind


def user_data_dir() -> Path:
    """Teams, history and settings. Created lazily by the writers."""
    return _base("data")


def user_cache_dir() -> Path:
    """Disposable data (banner cache, downloaded images)."""
    return _base("cache")


def migrate_legacy_file(name: str, target: Path) -> None:
    """One-time copy of a file that older versions kept inside ``data/``."""
    legacy = Path(__file__).resolve().parent.parent / "data" / name
    try:
        if not target.exists() and legacy.is_file() and legacy.stat().st_size > 0:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(legacy.read_bytes())
    except OSError:
        pass
