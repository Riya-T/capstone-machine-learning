"""Public checks for the c_take_kit change (atomic operation). Shown to the
editor, never to the writer.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_take_kit/public/test_take_kit_public.py
"""

import pytest
from parts import NotEnoughParts, PartsStore


@pytest.fixture
def store():
    s = PartsStore()
    s.add_bin("A1")
    s.stock("A1", "bolt", 10)
    s.stock("A1", "nut", 6)
    return s


def test_a_kit_takes_every_part_number_in_it(store):
    assert store.take_kit("A1", {"bolt": 4, "nut": 4}) == 8
    assert store.get_count("A1", "bolt") == 6
    assert store.get_count("A1", "nut") == 2


def test_a_kit_that_cannot_be_completed_takes_nothing(store):
    with pytest.raises(NotEnoughParts):
        store.take_kit("A1", {"bolt": 4, "nut": 7})
    assert store.get_count("A1", "bolt") == 10
    assert store.get_count("A1", "nut") == 6
