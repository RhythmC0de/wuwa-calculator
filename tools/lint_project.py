"""Run Pylint on project scripts, excluding caches and generated files."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

IGNORED_DIRECTORIES = frozenset(
    {
        ".cache",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)


def discover_scripts(project_root: Path) -> list[Path]:
    """Find maintained Python scripts without entering cache directories."""
    scripts = set(project_root.glob("*.py"))
    for directory in ("src", "test", "tools", "DEMO"):
        for current, directories, filenames in os.walk(
            project_root / directory
        ):
            directories[:] = [
                name
                for name in directories
                if name not in IGNORED_DIRECTORIES
                and not name.startswith(".venv-")
            ]
            scripts.update(
                Path(current) / name
                for name in filenames
                if name.endswith(".py")
            )
    return sorted(scripts)


def main() -> int:
    """Analyze maintained Python files and return Pylint's exit status."""
    root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "-m",
        "pylint",
        "--rcfile",
        str(root / "pyproject.toml"),
        *(str(path.relative_to(root)) for path in discover_scripts(root)),
    ]
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
