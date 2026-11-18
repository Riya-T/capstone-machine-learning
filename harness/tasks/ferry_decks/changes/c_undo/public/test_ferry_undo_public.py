"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_ferry_undo_public.py
"""

import pytest
from ferry import Ferry, FerryError


@pytest.fixture
def ferry():
    f = Ferry()
    f.add_deck("upper")
    f.add_deck("lower")
    return f


def test_undo_takes_back_the_last_boarding(ferry):
    ferry.board("van", "upper")
    ferry.board("bus", "upper")
    ferry.undo()
    assert ferry.get_vehicles("upper") == ["van"]
    ferry.undo()
    assert ferry.get_vehicles("upper") == []


def test_undo_takes_back_a_move_vehicle(ferry):
    ferry.board("van", "upper")
    ferry.move_vehicle("van", "lower")
    ferry.undo()
    assert ferry.get_vehicles("upper") == ["van"]
    assert ferry.get_vehicles("lower") == []
    assert ferry.get_deck_of("van") == "upper"


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(FerryError):
        Ferry().undo()
