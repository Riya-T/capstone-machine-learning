"""Hidden tests for the c_undo change (undo of stores and retrievals).
Never shown to the writer or the editor.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from lockers import LockerError, LockerRoom, NoLockerFree

LOCKERS = [("S1", "small"), ("S2", "small"), ("M1", "medium"), ("L1", "large")]
ITEMS = ["hat", "coat", "bag", "skis"]


@pytest.fixture
def room():
    r = LockerRoom()
    for locker_id, size in LOCKERS:
        r.add_locker(locker_id, size)
    return r


def state(r):
    where = {}
    for item in ITEMS:
        try:
            where[item] = r.get_locker(item)
        except KeyError:
            where[item] = None
    flags = {locker_id: r.is_out_of_order(locker_id) for locker_id, _ in LOCKERS}
    return r.get_free_lockers(), r.get_takings(), where, flags


def test_undo_walks_back_to_the_start(room):
    snapshots = [state(room)]
    room.store("hat", "small")
    snapshots.append(state(room))
    room.store("coat", "small")
    snapshots.append(state(room))
    room.retrieve("hat")
    snapshots.append(state(room))
    room.store("bag", "small")
    snapshots.append(state(room))
    for expected_item in ["bag", "hat", "coat", "hat"]:
        snapshots.pop()
        assert room.undo() == expected_item
        assert state(room) == snapshots[-1]
    with pytest.raises(LockerError):
        room.undo()
    assert state(room) == snapshots[0]


def test_undo_takes_off_exactly_the_fee_that_was_taken():
    r = LockerRoom(size_table={"s": 40, "m": 90})
    r.add_locker("S1", "s", fee=15)
    r.add_locker("M1", "m")
    r.store("hat", "s")
    r.store("coat", "s")
    assert r.get_takings() == 105
    r.undo()
    assert r.get_takings() == 15
    r.undo()
    assert r.get_takings() == 0


def test_undo_skips_calls_that_raised(room):
    room.store("hat", "large")
    for call in (
        lambda: room.store("hat", "small"),
        lambda: room.store("coat", "large"),
        lambda: room.store("", "small"),
        lambda: room.retrieve("coat"),
    ):
        with pytest.raises((ValueError, KeyError, LockerError)):
            call()
    assert room.undo() == "hat"
    with pytest.raises(LockerError):
        room.undo()


def test_undo_skips_calls_other_than_store_and_retrieve(room):
    room.store("hat", "small")
    room.add_locker("X1", "small")
    room.set_out_of_order("S2")
    room.get_free_lockers()
    assert room.undo() == "hat"
    assert room.get_free_lockers() == ["S1", "M1", "L1", "X1"]
    assert room.is_out_of_order("S2")
    with pytest.raises(LockerError):
        room.undo()


def test_undo_of_a_store_into_a_locker_now_broken_leaves_it_broken(room):
    room.store("hat", "small")
    room.set_out_of_order("S1")
    assert room.undo() == "hat"
    assert room.get_free_lockers() == ["S2", "M1", "L1"]
    assert room.is_out_of_order("S1")
    assert room.get_takings() == 0


def test_undo_of_a_retrieve_from_a_locker_now_broken_is_refused(room):
    room.store("hat", "small")
    room.store("coat", "small")
    room.retrieve("hat")
    room.set_out_of_order("S1")
    before = state(room)
    with pytest.raises(LockerError):
        room.undo()
    assert state(room) == before
    room.set_in_service("S1")
    assert room.undo() == "hat"
    assert room.get_locker("hat") == "S1"
    assert room.undo() == "coat"


def test_undo_cannot_be_redone(room):
    room.store("hat", "small")
    room.store("coat", "small")
    room.undo()
    room.store("bag", "medium")
    assert room.undo() == "bag"
    assert room.undo() == "hat"
    with pytest.raises(LockerError):
        room.undo()
    assert room.get_takings() == 0
    assert room.get_free_lockers() == ["S1", "S2", "M1", "L1"]


def test_undo_gives_the_locker_back_its_place(room):
    room.store("hat", "small")
    room.store("coat", "small")
    room.undo()
    assert room.store("bag", "small") == "S2"
    room.store("skis", "medium")
    room.store("hat2", "large")
    with pytest.raises(NoLockerFree):
        room.store("box", "small")
    room.undo()
    room.undo()
    room.undo()
    assert room.get_free_lockers() == ["S2", "M1", "L1"]
    assert room.store("bag", "small") == "S2"


def test_undo_of_a_retrieve_then_restore_of_the_same_item(room):
    room.store("hat", "medium")
    room.retrieve("hat")
    room.store("hat", "small")
    assert room.get_locker("hat") == "S1"
    assert room.undo() == "hat"
    with pytest.raises(KeyError):
        room.get_locker("hat")
    assert room.undo() == "hat"
    assert room.get_locker("hat") == "M1"
    assert room.get_takings() == 300
    assert room.get_free_lockers() == ["S1", "S2", "L1"]


def test_undo_on_a_new_room_is_refused():
    r = LockerRoom()
    with pytest.raises(LockerError):
        r.undo()
    r.add_locker("S1", "small")
    with pytest.raises(LockerError):
        r.undo()
    assert r.get_free_lockers() == ["S1"]
