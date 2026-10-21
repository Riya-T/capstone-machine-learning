"""Public checks for the c_versions change (locker versions and moves).
Shown to the editor, never to the writer.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from lockers import LockerRoom, VersionConflict


@pytest.fixture
def room():
    r = LockerRoom()
    r.add_locker("S1", "small")
    r.add_locker("L1", "large")
    return r


def test_version_goes_up_when_a_locker_changes(room):
    assert room.get_version("S1") == 1
    room.store("hat", "small")
    room.retrieve("hat", expected_version=2)
    assert room.get_version("S1") == 3
    assert room.get_version("L1") == 1


def test_move_puts_the_item_into_another_locker(room):
    room.store("hat", "small")
    room.move("hat", "L1", expected_version=1)
    assert room.get_locker("hat") == "L1"
    assert room.get_free_lockers() == ["S1"]
    assert (room.get_version("S1"), room.get_version("L1")) == (3, 2)
    assert room.get_takings() == 200


def test_version_that_is_out_of_date_is_refused(room):
    room.store("hat", "small")
    with pytest.raises(VersionConflict):
        room.retrieve("hat", expected_version=1)
    assert room.get_locker("hat") == "S1"
