"""Regras puras (sem Qt, sem I/O) da revisão dos hits detectados."""

from .models import (
    DecisionKind,
    HitEvent,
    HitPart,
    ReviewDecision,
    ReviewMode,
    accept,
    correct,
    discard,
)
from .parsing import ParseError, format_parts, parse_parts
from .totals import (
    DamageTotals,
    compute_totals,
    default_parts,
    final_parts,
    needs_review,
    review_queue,
)

__all__ = [
    "ParseError",
    "DamageTotals",
    "DecisionKind",
    "HitEvent",
    "HitPart",
    "ReviewDecision",
    "ReviewMode",
    "accept",
    "compute_totals",
    "correct",
    "default_parts",
    "discard",
    "final_parts",
    "format_parts",
    "needs_review",
    "parse_parts",
    "review_queue",
]
