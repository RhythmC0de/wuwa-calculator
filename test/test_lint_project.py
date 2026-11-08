"""Check lint discovery and precise inference of compiled Qt signals."""

import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_script_discovery_excludes_caches_and_builds(tmp_path):
    """Exclude caches, virtual environments, and native builds from lint."""
    names = (
        "tethys.py",
        "src/app.py",
        "test/test_app.py",
        "tools/check.py",
        "src/.cache/cached.py",
        "src/__pycache__/cached.py",
        "tools/.ruff_cache/cached.py",
        "test/.pytest_cache/cached.py",
        "src/native/build/generated.py",
        "src/.venv-backup/library.py",
        ".cache/cached.py",
        ".venv/library.py",
    )
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    discover = runpy.run_path(str(ROOT / "tools/lint_project.py"))[
        "discover_scripts"
    ]
    actual = {
        path.relative_to(tmp_path).as_posix() for path in discover(tmp_path)
    }
    assert actual == {
        "tethys.py",
        "src/app.py",
        "test/test_app.py",
        "tools/check.py",
    }


def test_qt_signal_inference_keeps_real_member_errors(tmp_path):
    """Recognize signals while checking dictionaries and invalid methods."""
    sample = tmp_path / "signal_sample.py"
    sample.write_text(
        "from PySide6.QtCore import QTimer\n"
        "timer = QTimer()\n"
        "timer.timeout.connect(lambda: None)\n"
        "timer.timeout.missing_operation()\n"
        "values = {'key': 1}\n"
        "values['key'] = 2\n"
        "values.missing_operation()\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pylint",
            "--rcfile",
            str(ROOT / "pyproject.toml"),
            "--disable=all",
            "--enable=no-member,unsupported-assignment-operation",
            "--output-format=json",
            "--reports=n",
            "--score=n",
            str(sample),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    diagnostics = json.loads(result.stdout)
    assert result.returncode == 2, result.stderr
    assert [(item["symbol"], item["line"]) for item in diagnostics] == [
        ("no-member", 4),
        ("no-member", 7),
    ]
