"""Atomic JSON persistence with corrupt-file quarantine."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

MAX_JSON_BYTES = 32 * 1024 * 1024


def read_json(path: Path, default: object, *, max_bytes: int = MAX_JSON_BYTES) -> object:
    """Return parsed JSON or ``default``. Corrupt files are renamed, not lost."""
    try:
        if not path.is_file():
            return default
        if path.stat().st_size > max_bytes:
            raise ValueError("json too large")
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return default
        return json.loads(text)
    except (ValueError, UnicodeDecodeError):
        _quarantine(path)
        return default
    except OSError:
        return default


def _quarantine(path: Path) -> None:
    try:
        path.replace(path.with_name(f"{path.name}.corrupt-{int(time.time())}"))
    except OSError:
        pass


def write_json(path: Path, value: object, *, indent: int | None = 2) -> None:
    """Write via temp file + fsync + os.replace so a crash never truncates data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=indent)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
