"""A lost append race must be deferred, not failed (issue #5393).

An append reads the stored document, adds its turn and writes it back on condition the document
has not moved. Losing that race writes nothing — the precondition rejects the write whole — so
redoing it on a fresh read is always safe. The worker used to treat it like any other exception
and mark the operation terminally `failed`, which dropped the turn it carried.

What the worker then does with that classification — defer, no retry spent, with a rising count —
is covered end to end against a real database by
``test_worker.py::test_a_lost_append_race_defers_and_counts_up``.
"""

from hindsight_api.engine.memories.base import StoreWriteConflict
from hindsight_api.engine.retain.types import ConcurrentAppendConflict
from hindsight_api.worker.backpressure import is_append_conflict
from hindsight_api.worker.poller import _append_conflict_defer_seconds


def test_both_stores_lost_races_are_recognised():
    assert is_append_conflict(ConcurrentAppendConflict("document moved"))
    assert is_append_conflict(StoreWriteConflict("watermark mismatch"))


def test_it_is_found_through_wrapping():
    """The worker sees the conflict wrapped by whatever re-raised it."""
    try:
        try:
            raise ConcurrentAppendConflict("document moved")
        except Exception as inner:
            raise RuntimeError("retain failed for document chat-1") from inner
    except Exception as outer:
        assert is_append_conflict(outer)


def test_ordinary_failures_are_untouched():
    assert not is_append_conflict(ValueError("document_id must not be empty"))


def test_a_cycle_in_the_chain_terminates():
    a, b = Exception("a"), Exception("b")
    a.__cause__, b.__cause__ = b, a
    assert is_append_conflict(a) is False


def test_backoff_grows_and_is_capped():
    """Seconds at first — the winner is usually done by then — minutes at worst."""
    assert 1.0 <= _append_conflict_defer_seconds(1) <= 3.0
    assert _append_conflict_defer_seconds(1) < _append_conflict_defer_seconds(10)
    assert _append_conflict_defer_seconds(50) <= 450.0
