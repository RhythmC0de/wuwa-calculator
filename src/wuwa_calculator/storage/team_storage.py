"""Local team storage for the Tethys PySide6 application."""

# * EDITAVEL: altere o formato dos registros junto com ui/tabs/teams_tab.py.
# ! Preserve compatibilidade ao mudar as chaves dos JSON salvos pelo usuario.

from __future__ import annotations

from pathlib import Path
from typing import Any

from wuwa_calculator.storage.atomic import read_json, write_json
from wuwa_calculator.storage.paths import migrate_legacy_file, user_data_dir

TEAMS_FILE = user_data_dir() / "teams.json"
DEFAULT_TEAMS: list[dict[str, Any]] = [
    {"name": "Fusion quickswap", "status": "Not started", "characters": ["Augusta", "Brant", "Shorekeeper"]},
    {"name": "Glacio control", "status": "Not started", "characters": []},
    {"name": "Aero burst", "status": "Not started", "characters": []},
]


def _defaults() -> list[dict[str, Any]]:
    return [{**team, "characters": list(team["characters"])} for team in DEFAULT_TEAMS]


def load_teams(path: Path = TEAMS_FILE) -> list[dict[str, Any]]:
    if path == TEAMS_FILE:
        migrate_legacy_file("teams.json", path)
    value = read_json(path, None)
    if not isinstance(value, list):
        return _defaults()
    return [team for team in value if isinstance(team, dict) and str(team.get("name", "")).strip()]


def save_teams(teams: list[dict[str, Any]], path: Path = TEAMS_FILE) -> None:
    write_json(path, teams)
