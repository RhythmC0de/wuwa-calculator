"""Cálculo dos totais nos dois modos (automático e com revisão)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Mapping

from .models import HitEvent, HitPart, ReviewDecision, ReviewMode


def needs_review(event: HitEvent) -> bool:
    """Eventos que a engine não consegue fechar sozinha:
    - não confirmados (forma de números sobrepostos);
    - empilhados (valor certo, quantidade de cópias desconhecida)."""
    return (not event.confirmed) or event.stacked


def review_queue(events: Iterable[HitEvent]) -> list[HitEvent]:
    return sorted(
        (e for e in events if needs_review(e)), key=lambda e: e.timestamp
    )


def default_parts(event: HitEvent) -> tuple[HitPart, ...]:
    """O que a engine sozinha conta para o evento.

    - confirmado: 1 cópia (2 se empilhado, o mínimo possível);
    - não confirmado: não entra (nada)."""
    if event.stacked:
        return (HitPart(event.damage, 2),)
    if event.confirmed:
        return (HitPart(event.damage, 1),)
    return ()


def final_parts(
    events: Iterable[HitEvent],
    mode: ReviewMode = ReviewMode.AUTOMATIC,
    decisions: Mapping[int, ReviewDecision] | None = None,
) -> Iterator[tuple[HitEvent, tuple[HitPart, ...]]]:
    """(evento, partes que entram na conta) na ordem recebida. Descartados e
    não confirmados sem decisão aparecem com partes vazias."""
    decisions = decisions or {}
    for event in events:
        decision = decisions.get(event.index) if mode is ReviewMode.REVIEW else None
        yield event, (decision.parts if decision is not None else default_parts(event))


@dataclass(frozen=True)
class DamageTotals:
    total_damage: int
    hits: int
    peak_damage: int
    # Eventos duvidosos sem decisão do usuário. `pending_damage` é o dano que
    # ficou FORA do total por causa deles (eventos não confirmados); em
    # empilhados já entram as 2 cópias mínimas e só as extras são
    # desconhecidas, então não somam aqui.
    pending_items: int
    pending_damage: int
    reviewed_hits: int  # eventos com decisão do usuário


def compute_totals(
    events: Iterable[HitEvent],
    mode: ReviewMode = ReviewMode.AUTOMATIC,
    decisions: Mapping[int, ReviewDecision] | None = None,
) -> DamageTotals:
    """Soma o dano.

    Automático: decisões são ignoradas; só entram os eventos que a engine
    confirma. Os não confirmados ficam em `pending_*` (nunca se perdem em
    silêncio).

    Revisão: a decisão do usuário vale no lugar da engine; sem decisão, o
    evento se comporta como no automático (e segue pendente se duvidoso).
    """
    decisions = decisions or {}
    use_decisions = mode is ReviewMode.REVIEW

    total = hits = peak = pending_items = pending_damage = reviewed = 0

    for event in events:
        decision = decisions.get(event.index) if use_decisions else None

        if decision is not None:
            reviewed += 1
            parts = decision.parts
        else:
            parts = default_parts(event)
            if needs_review(event):
                pending_items += 1
                if not parts:
                    pending_damage += event.damage

        for part in parts:
            total += part.damage
            hits += part.copies
            peak = max(peak, part.value)

    return DamageTotals(total, hits, peak, pending_items, pending_damage, reviewed)
