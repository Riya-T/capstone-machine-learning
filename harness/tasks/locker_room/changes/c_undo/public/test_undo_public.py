"""Public checks for the c_undo change (undo of stores and retrievals).
Shown to the editor, never to the writer.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from lockers import LockerError, LockerRoom


@pytest.fixture
def room():
    r = LockerRoom()
    r.add_locker("S1", "small")
    r.add_locker("M1", "medium")
    return r


def test_undoing_a_store_refunds_the_fee(room):
    room.store("hat", "medium")
    assert room.undo() == "hat"
    assert room.get_free_lockers() == ["S1", "M1"]
    assert room.get_takings() == 0
    with pytest.raises(KeyError):
        room.get_locker("hat")


def test_undoing_a_retrieve_puts_the_item_back(room):
    room.store("hat", "small")
    room.retrieve("hat")
    assert room.undo() == "hat"
    assert room.get_locker("hat") == "S1"
    assert room.get_takings() == 200


def test_undoing_with_nothing_to_undo_raises(room):
    with pytest.raises(LockerError):
        room.undo()
