"""Core calculation processing for Wuwa Damage Lab.

This module intentionally contains only calculation processing code.
It is reloaded by the desktop application when the processing logic changes.
"""

# ! Keep this module independent from Qt, network requests and UI widgets.
# * EDITAVEL: altere formulas aqui e valide os resultados antes de ligar a interface.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DamageResult:
    base_per_hit: float
    non_critical_per_hit: float
    average_per_hit: float
    critical_per_hit: float
    total_cast: float
    rotation_damage: float
    dps: float
    crit_chance: float
    crit_damage: float
    total_bonus: float
    defense_multiplier: float
    resistance_multiplier: float


@dataclass
class ManualDamageResult:
    damage_per_hit: float
    total_damage: float
    dps: float


def parse_number(value: str, default: float = 0.0) -> float:
    try:
        return float(value.replace(",", ".").strip())
    except (AttributeError, ValueError):
        return default


def calculate_damage(
    attack: float,
    scaling: float,
    flat_bonus: float,
    crit_rate: float,
    crit_damage: float,
    hits: int,
    enemy_defense: float,
    resistance_reduction: float,
    rotation_casts: int,
    rotation_seconds: float,
) -> DamageResult:
    """Calculate damage for one ability and its rotation contribution."""
    attack_total = max(0.0, attack)
    skill_modifier = max(0.0, scaling) / 100.0
    damage_bonus = max(0.0, flat_bonus) / 100.0
    bonus_multiplier = 1.0 + damage_bonus
    defense_factor = max(0.0, 1.0 - max(0.0, enemy_defense) / 100.0)
    resistance_factor = max(0.0, 1.0 - max(0.0, resistance_reduction) / 100.0)

    non_critical_per_hit = (
        attack_total
        * skill_modifier
        * bonus_multiplier
        * defense_factor
        * resistance_factor
    )
    crit_rate_fraction = max(0.0, min(1.0, crit_rate / 100.0))
    crit_multiplier = max(1.0, 1.0 + max(0.0, crit_damage) / 100.0)
    critical_per_hit = non_critical_per_hit * crit_multiplier
    average_per_hit = non_critical_per_hit * (
        (1.0 - crit_rate_fraction) + crit_rate_fraction * crit_multiplier
    )

    effective_hits = max(1, int(hits))
    effective_casts = max(1, int(rotation_casts))
    total_cast = average_per_hit * effective_hits
    rotation_damage = total_cast * effective_casts
    dps = rotation_damage / max(0.1, rotation_seconds)

    return DamageResult(
        base_per_hit=non_critical_per_hit,
        non_critical_per_hit=non_critical_per_hit,
        average_per_hit=average_per_hit,
        critical_per_hit=critical_per_hit,
        total_cast=total_cast,
        rotation_damage=rotation_damage,
        dps=dps,
        crit_chance=crit_rate,
        crit_damage=crit_damage,
        total_bonus=flat_bonus,
        defense_multiplier=defense_factor,
        resistance_multiplier=resistance_factor,
    )


def calculate_manual_damage(
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
    """Apply the character-tab formula using manually entered build values."""
    damage_per_hit = (
        max(0.0, attack_total)
        * max(0.0, skill_modifier) / 100.0
        * (1.0 + max(0.0, damage_bonus) / 100.0)
        * max(0.0, crit_multiplier)
        * max(0.0, defense_factor)
        * max(0.0, resistance_factor)
    )
    total_damage = damage_per_hit * max(1, int(hits)) * max(1, int(casts))
    return ManualDamageResult(
        damage_per_hit=damage_per_hit,
        total_damage=total_damage,
        dps=total_damage / max(0.1, duration),
    )
