"""Modelos da revisão. Dataclasses imutáveis, sem dependência de UI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Teto de sanidade para um único valor digitado/lido (evita erro de digitação
# estourar o total). O maior hit real observado está na casa dos milhões.
MAX_HIT_VALUE = 99_999_999
MAX_COPIES = 50


class ReviewMode(str, Enum):
    AUTOMATIC = "automatic"  # só a engine decide o que entra no total
    REVIEW = "review"        # o usuário confere o que a engine duvidou


class DecisionKind(str, Enum):
    ACCEPTED = "accepted"    # "a leitura da engine está certa"
    CORRECTED = "corrected"  # valor(es)/cópias diferentes dos da engine
    DISCARDED = "discarded"  # não é dano (HUD, quest, lixo)


@dataclass(frozen=True)
class HitPart:
    """`copies` ocorrências do número `value` dentro de um mesmo evento."""

    value: int
    copies: int = 1

    def __post_init__(self) -> None:
        if not 0 < self.value <= MAX_HIT_VALUE:
            raise ValueError(f"valor fora do intervalo: {self.value}")
        if not 0 < self.copies <= MAX_COPIES:
            raise ValueError(f"cópias fora do intervalo: {self.copies}")

    @property
    def damage(self) -> int:
        return self.value * self.copies


@dataclass(frozen=True)
class HitEvent:
    """Evento da engine, já desligado do objeto pybind11."""

    index: int
    timestamp: float
    damage: int
    confirmed: bool = True
    stacked: bool = False
    verified: bool = False
    repeats: int = 0
    observations: int = 0
    digit_pitch: float = 0.0
    center_x: int = 0
    center_y: int = 0
    width: int = 0
    height: int = 0

    @classmethod
    def from_engine(cls, index: int, event: object) -> "HitEvent":
        """Copia os campos de um DamageEvent nativo (builds antigas sem
        `confirmed`/`stacked` contam como confirmadas)."""

        def read(name: str, default):
            return getattr(event, name, default)

        return cls(
            index=index,
            timestamp=float(read("timestamp", 0.0)),
            damage=int(read("damage", 0)),
            confirmed=bool(read("confirmed", True)),
            stacked=bool(read("stacked", False)),
            verified=bool(read("verified", False)),
            repeats=int(read("repeats", 0)),
            observations=int(read("observations", 0)),
            digit_pitch=float(read("digit_pitch", 0.0)),
            center_x=int(read("center_x", 0)),
            center_y=int(read("center_y", 0)),
            width=int(read("width", 0)),
            height=int(read("height", 0)),
        )


@dataclass(frozen=True)
class ReviewDecision:
    event_index: int
    kind: DecisionKind
    parts: tuple[HitPart, ...] = ()

    def __post_init__(self) -> None:
        if self.kind is DecisionKind.DISCARDED and self.parts:
            raise ValueError("descarte não tem valores")
        if self.kind is not DecisionKind.DISCARDED and not self.parts:
            raise ValueError("decisão sem valores")

    @property
    def damage(self) -> int:
        return sum(part.damage for part in self.parts)

    @property
    def hits(self) -> int:
        return sum(part.copies for part in self.parts)


def accept(event: HitEvent, copies: int | None = None) -> ReviewDecision:
    """Aceita a leitura da engine. Em eventos empilhados são, no mínimo,
    duas cópias (a engine não sabe quantas); `copies` sobrescreve."""
    count = copies if copies is not None else (2 if event.stacked else 1)
    return ReviewDecision(
        event.index, DecisionKind.ACCEPTED, (HitPart(event.damage, count),)
    )


def correct(event: HitEvent, parts: list[tuple[int, int]]) -> ReviewDecision:
    """Valores/cópias informados pelo usuário. Ex.: [(785, 1), (2518, 1)]."""
    return ReviewDecision(
        event.index,
        DecisionKind.CORRECTED,
        tuple(HitPart(value, copies) for value, copies in parts),
    )


def discard(event: HitEvent) -> ReviewDecision:
    return ReviewDecision(event.index, DecisionKind.DISCARDED)
