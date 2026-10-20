import pytest

from wuwa_calculator.domain.review import (
    HitEvent, ReviewMode, accept, compute_totals, correct, discard,
    needs_review, review_queue,
)


def ev(i, dmg, **kw):
    return HitEvent(index=i, timestamp=float(i), damage=dmg, **kw)


EVENTS = [
    ev(0, 1000),                                   # normal
    ev(1, 782518, confirmed=False),                # 785 + 2518 sobrepostos
    ev(2, 2071, stacked=True, confirmed=True),     # >= 2 cópias
    ev(3, 500, verified=True),
]


def test_needs_review_and_queue():
    assert [e.index for e in review_queue(EVENTS)] == [1, 2]
    assert not needs_review(EVENTS[0]) and not needs_review(EVENTS[3])


def test_automatic_ignores_unconfirmed_and_counts_min_copies():
    t = compute_totals(EVENTS, ReviewMode.AUTOMATIC)
    assert t.total_damage == 1000 + 2071 * 2 + 500
    assert t.hits == 1 + 2 + 1
    assert t.pending_items == 2 and t.pending_damage == 782518
    assert t.peak_damage == 2071


def test_automatic_ignores_decisions():
    d = {1: discard(EVENTS[1])}
    assert compute_totals(EVENTS, ReviewMode.AUTOMATIC, d) == compute_totals(EVENTS)


def test_review_applies_decisions():
    d = {
        1: correct(EVENTS[1], [(785, 1), (2518, 1)]),
        2: accept(EVENTS[2], copies=3),
    }
    t = compute_totals(EVENTS, ReviewMode.REVIEW, d)
    assert t.total_damage == 1000 + 785 + 2518 + 2071 * 3 + 500
    assert t.hits == 1 + 2 + 3 + 1
    assert t.pending_items == 0 and t.reviewed_hits == 2
    assert t.peak_damage == 2518


def test_review_discard_and_pending():
    d = {1: discard(EVENTS[1])}
    t = compute_totals(EVENTS, ReviewMode.REVIEW, d)
    assert t.total_damage == 1000 + 2071 * 2 + 500
    assert t.pending_items == 1 and t.pending_damage == 0


def test_validation():
    with pytest.raises(ValueError):
        correct(EVENTS[1], [(0, 1)])
    with pytest.raises(ValueError):
        correct(EVENTS[1], [(100, 0)])
    with pytest.raises(ValueError):
        correct(EVENTS[1], [])


def test_from_engine_old_build():
    class Old:
        timestamp = 1.0
        damage = 10
    e = HitEvent.from_engine(7, Old())
    assert e.confirmed and not e.stacked and e.index == 7


def test_final_parts_follow_mode():
    from wuwa_calculator.domain.review import final_parts

    decisions = {1: correct(EVENTS[1], [(785, 1), (2518, 1)])}
    auto = {e.index: p for e, p in final_parts(EVENTS, ReviewMode.AUTOMATIC, decisions)}
    rev = {e.index: p for e, p in final_parts(EVENTS, ReviewMode.REVIEW, decisions)}
    assert auto[1] == ()
    assert [(p.value, p.copies) for p in rev[1]] == [(785, 1), (2518, 1)]
    assert rev[0] == auto[0]
