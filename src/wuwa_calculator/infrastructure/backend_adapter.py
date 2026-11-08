"""UI-safe boundary around the existing damage-processing backend."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wuwa_calculator.domain.calculations.damage import (
    DamageResult,
    ManualDamageResult,
    calculate_damage,
    calculate_manual_damage,
)
from wuwa_calculator.storage.history_storage import (
    ROTATION_HISTORY_FILE,
    export_rotation_history,
    import_rotation_history,
    load_rotation_history,
    load_rotation_teams,
    save_rotation_test,
)


@dataclass(frozen=True)
class DamageInput:
    """Inputs accepted by the calculation boundary used by the UI."""

    # Fields mirror the persisted or externally consumed data schema.
    # pylint: disable=too-many-instance-attributes
    attack: float = 1500.0
    scaling: float = 120.0
    flat_bonus: float = 20.0
    crit_rate: float = 50.0
    crit_damage: float = 150.0
    hits: int = 1
    enemy_defense: float = 20.0
    resistance_reduction: float = 0.0
    rotation_casts: int = 1
    rotation_seconds: float = 10.0


def calculate(values: DamageInput) -> DamageResult:
    """Calculate damage from the inputs supplied by the interface."""
    return calculate_damage(
        values.attack,
        values.scaling,
        values.flat_bonus,
        values.crit_rate,
        values.crit_damage,
        values.hits,
        values.enemy_defense,
        values.resistance_reduction,
        values.rotation_casts,
        values.rotation_seconds,
    )


def calculate_character_damage(
    attack_total: float,
    skill_modifier: float,
    damage_bonus: float,
    crit_multiplier: float,
    defense_factor: float,
    resistance_factor: float,
    hits: int,
    casts: int,
    duration: float,
) -> ManualDamageResult:
    """Calculate per-hit damage and DPS for the selected character."""
    # Keep the established call signature used by existing callers.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    return calculate_manual_damage(
        attack_total,
        skill_modifier,
        damage_bonus,
        crit_multiplier,
        defense_factor,
        resistance_factor,
        hits,
        casts,
        duration,
    )


def history_records(
    path: Path = ROTATION_HISTORY_FILE,
) -> list[dict[str, Any]]:
    """Load the saved rotation records exposed to the interface."""
    return load_rotation_history(path)


def history_teams(path: Path = ROTATION_HISTORY_FILE) -> list[dict[str, Any]]:
    """Load the teams referenced by saved rotation records."""
    return load_rotation_teams(path)


def save_history_record(
    team: str,
    rotation: str,
    damage: float = 0.0,
    path: Path = ROTATION_HISTORY_FILE,
    skills: list[dict[str, object]] | None = None,
    practical_damage: float | None = None,
) -> dict[str, Any]:
    """Save history record."""
    # Keep the established call signature used by existing callers.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    return save_rotation_test(
        team=team,
        rotation=rotation,
        damage=damage,
        path=path,
        skills=skills,
        practical_damage=practical_damage,
    )


def import_history_file(
    source: Path, destination: Path = ROTATION_HISTORY_FILE
) -> list[dict[str, Any]]:
    """Import history file."""
    return import_rotation_history(source, destination)


def export_history_file(
    source: Path = ROTATION_HISTORY_FILE, destination: Path | None = None
) -> None:
    """Export history file."""
    export_rotation_history(source, destination)
