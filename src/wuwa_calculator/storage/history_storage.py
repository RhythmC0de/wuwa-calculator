"""Local rotation-history storage without UI or network dependencies."""

# * EDITAVEL: altere o formato do historico junto com app/history_tab.py.
# ! Valide JSON importado antes de usa-lo na interface.

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ROTATION_HISTORY_FILE = DATA_DIR / "rotation_history.json"


def read_json_file(path: Path, default: object) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def write_json_file(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def empty_rotation_document() -> dict[str, object]:
    return {"schema_version": 2, "updated_at": "", "teams": [], "rotations": [], "comparisons": []}


def load_rotation_document(path: Path = ROTATION_HISTORY_FILE) -> dict[str, object]:
    stored = read_json_file(path, None)
    document = empty_rotation_document()
    if isinstance(stored, list):
        document["rotations"] = [record for record in stored if isinstance(record, dict)]
    elif isinstance(stored, dict):
        document.update({key: value for key, value in stored.items() if key in document})
        for key in ("teams", "rotations", "comparisons"):
            if not isinstance(document.get(key), list):
                document[key] = []
    return document


def save_rotation_document(document: dict[str, object], path: Path = ROTATION_HISTORY_FILE) -> None:
    normalized = {**empty_rotation_document(), **document}
    normalized["schema_version"] = 2
    normalized["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    write_json_file(path, normalized)


def load_rotation_history(path: Path = ROTATION_HISTORY_FILE) -> list[dict[str, object]]:
    rotations = load_rotation_document(path).get("rotations", [])
    return [record for record in rotations if isinstance(record, dict)]


def load_rotation_teams(path: Path = ROTATION_HISTORY_FILE) -> list[dict[str, object]]:
    teams = load_rotation_document(path).get("teams", [])
    return [team for team in teams if isinstance(team, dict)]


def save_rotation_test(
    team: str,
    rotation: str,
    damage: float,
    video: str = "",
    path: Path = ROTATION_HISTORY_FILE,
    skills: list[dict[str, object]] | None = None,
    practical_damage: float | None = None,
) -> dict[str, object]:
    document = load_rotation_document(path)
    history = [record for record in document["rotations"] if isinstance(record, dict)]
    valid_ids = []
    for record in history:
        try:
            valid_ids.append(int(record.get("id", 0)))
        except (TypeError, ValueError):
            continue
    next_id = max(valid_ids, default=0) + 1
    record: dict[str, object] = {
        "id": next_id,
        "team": team.strip() or "Time sem nome",
        "rotation": rotation.strip() or "Rotação sem nome",
        "damage": float(damage),
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "video": video.strip(),
        "skills": skills or [],
    }
    if practical_damage is not None:
        record["practical_damage"] = float(practical_damage)
    history.append(record)
    document["rotations"] = history
    comparisons = document.get("comparisons", [])
    if not isinstance(comparisons, list):
        comparisons = []
    comparisons.append({
        "rotation_id": next_id,
        "theoretical": float(damage),
        "practical": practical_damage,
        "skills": skills or [],
    })
    document["comparisons"] = comparisons
    save_rotation_document(document, path)
    return record


def import_rotation_history(
    source_path: Path,
    destination_path: Path = ROTATION_HISTORY_FILE,
) -> list[dict[str, object]]:
    imported_data = read_json_file(source_path, None)
    if imported_data is None:
        raise ValueError("O arquivo JSON não pôde ser lido ou está inválido.")
    imported_document = imported_data if isinstance(imported_data, dict) else {}
    if isinstance(imported_data, list):
        candidates = imported_data
    elif isinstance(imported_data, dict):
        candidates = next(
            (value for key, value in imported_data.items() if key.casefold() in {"history", "rotations", "tests", "records"} and isinstance(value, list)),
            None,
        )
        if candidates is None:
            candidates = [imported_data] if any(key in imported_data for key in ("team", "rotation", "damage", "total_damage")) else []
    else:
        candidates = []
    if not candidates or not all(isinstance(item, dict) for item in candidates):
        raise ValueError("O JSON não contém testes de rotação reconhecíveis.")

    destination_document = load_rotation_document(destination_path)
    history = [record for record in destination_document["rotations"] if isinstance(record, dict)]
    imported_teams = imported_document.get("teams", [])
    if isinstance(imported_teams, list):
        existing_teams = [team for team in destination_document["teams"] if isinstance(team, dict)]
        existing_names = {str(team.get("name", "")).casefold() for team in existing_teams}
        for team in imported_teams:
            if isinstance(team, dict) and str(team.get("name", "")).casefold() not in existing_names:
                existing_teams.append(team)
                existing_names.add(str(team.get("name", "")).casefold())
        destination_document["teams"] = existing_teams
    used_ids: list[int] = []
    for record in history:
        try:
            used_ids.append(int(record.get("id", 0)))
        except (TypeError, ValueError):
            continue
    next_id = max(used_ids, default=0) + 1
    imported_records: list[dict[str, object]] = []
    for item in candidates:
        source = item
        raw_damage = source.get("damage", source.get("total_damage", source.get("totalDamage", 0)))
        try:
            damage = float(raw_damage)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Dano inválido no registro importado: {raw_damage!r}.") from error
        record: dict[str, object] = {
            "id": next_id,
            "team": str(source.get("team", source.get("team_name", source.get("name", "Time sem nome")))).strip() or "Time sem nome",
            "rotation": str(source.get("rotation", source.get("rotation_name", source.get("title", "Rotação sem nome")))).strip() or "Rotação sem nome",
            "damage": damage,
            "date": str(source.get("date", source.get("timestamp", datetime.now().astimezone().isoformat(timespec="seconds")))),
            "video": str(source.get("video", source.get("video_path", ""))).strip(),
            "skills": source.get("skills", source.get("skill_details", [])) if isinstance(source.get("skills", source.get("skill_details", [])), list) else [],
        }
        practical_value = source.get("practical_damage", source.get("practicalDamage"))
        if practical_value not in (None, ""):
            try:
                record["practical_damage"] = float(practical_value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Dano prático inválido no registro importado: {practical_value!r}.") from error
        imported_records.append(record)
        history.append(record)
        next_id += 1
    destination_document["rotations"] = history
    destination_comparisons = destination_document.get("comparisons", [])
    if not isinstance(destination_comparisons, list):
        destination_comparisons = []
    imported_comparisons = imported_document.get("comparisons")
    if isinstance(imported_comparisons, list):
        destination_comparisons.extend(item for item in imported_comparisons if isinstance(item, dict))
    else:
        destination_comparisons.extend(
            {
                "rotation_id": int(record["id"]),
                "theoretical": float(record["damage"]),
                "practical": record.get("practical_damage"),
                "skills": record.get("skills", []),
            }
            for record in imported_records
        )
    destination_document["comparisons"] = destination_comparisons
    save_rotation_document(destination_document, destination_path)
    return imported_records


def export_rotation_history(source: Path = ROTATION_HISTORY_FILE, destination: Path | None = None) -> None:
    target = destination or source
    save_rotation_document(load_rotation_document(source), target)
