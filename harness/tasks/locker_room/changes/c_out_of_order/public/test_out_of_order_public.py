"""Public checks for the c_out_of_order change (lockers out of service).
Shown to the editor, never to the writer.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_out_of_order/public/test_out_of_order_public.py
"""

import pytest
from lockers import LockerRoom, NoLockerFree


@pytest.fixture
def room():
    r = LockerRoom()
    r.add_locker("S1", "small")
    r.add_locker("S2", "small")
    return r


def test_broken_locker_is_skipped(room):
    room.set_out_of_order("S1")
    assert room.is_out_of_order("S1")
    assert room.get_free_lockers() == ["S2"]
    assert room.store("hat", "small") == "S2"
    with pytest.raises(NoLockerFree):
        room.store("cap", "small")


def test_broken_locker_still_hands_back_its_item(room):
    room.store("hat", "small")
    room.set_out_of_order("S1")
    assert room.retrieve("hat") == "S1"
    assert room.get_free_lockers() == ["S2"]
    room.set_in_service("S1")
    assert room.get_free_lockers() == ["S1", "S2"]
