"""Hidden tests for the c_out_of_order change (lockers out of service).
Never shown to the writer or the editor.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_out_of_order/private/test_out_of_order_new.py
"""

import pytest
from lockers import LockerRoom, NoLockerFree

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


def test_broken_flag_is_off_for_new_lockers(room):
    assert [room.is_out_of_order(x) for x, _ in LOCKERS] == [False] * 4


def test_broken_flag_can_be_set_and_cleared_repeatedly(room):
    room.set_out_of_order("M1")
    room.set_out_of_order("M1")
    assert room.is_out_of_order("M1")
    room.set_in_service("M1")
    assert not room.is_out_of_order("M1")
    room.set_in_service("M1")
    assert not room.is_out_of_order("M1")
    assert room.get_free_lockers() == ["S1", "S2", "M1", "L1"]


def test_broken_lockers_push_items_to_the_next_size(room):
    room.set_out_of_order("S1")
    room.set_out_of_order("S2")
    assert room.store("hat", "small") == "M1"
    room.set_out_of_order("L1")
    before = state(room)
    with pytest.raises(NoLockerFree):
        room.store("coat", "small")
    with pytest.raises(NoLockerFree):
        room.store("skis", "large")
    assert state(room) == before
    assert room.get_takings() == 300


def test_broken_lockers_are_never_free(room):
    room.set_out_of_order("S2")
    room.set_out_of_order("L1")
    assert room.get_free_lockers() == ["S1", "M1"]
    room.store("hat", "small")
    room.store("coat", "small")
    assert room.get_free_lockers() == []


def test_broken_locker_keeps_its_item_until_retrieved(room):
    room.store("hat", "small")
    room.store("coat", "medium")
    room.set_out_of_order("M1")
    assert room.get_locker("coat") == "M1"
    assert room.is_out_of_order("M1")
    assert room.retrieve("coat") == "M1"
    assert room.get_free_lockers() == ["S2", "L1"]
    assert room.store("bag", "medium") == "L1"


def test_broken_locker_back_in_service_takes_its_place_again(room):
    room.set_out_of_order("S1")
    assert room.store("hat", "small") == "S2"
    room.set_in_service("S1")
    assert room.get_free_lockers() == ["S1", "M1", "L1"]
    assert room.store("coat", "small") == "S1"


def test_broken_locker_in_use_put_back_in_service_stays_in_use(room):
    room.store("hat", "small")
    room.set_out_of_order("S1")
    room.set_in_service("S1")
    assert room.get_free_lockers() == ["S2", "M1", "L1"]
    assert room.get_locker("hat") == "S1"


def test_broken_flag_changes_no_money():
    r = LockerRoom()
    r.add_locker("S1", "small", fee=70)
    r.store("hat", "small")
    r.set_out_of_order("S1")
    r.retrieve("hat")
    r.set_in_service("S1")
    assert r.get_takings() == 70
    assert r.get_fee("S1") == 70


@pytest.mark.parametrize("locker_id", ["Q9", None, 1, "hat"])
@pytest.mark.parametrize(
    "method", ["set_out_of_order", "set_in_service", "is_out_of_order"]
)
def test_broken_flag_needs_a_known_locker(room, method, locker_id):
    room.store("hat", "small")
    before = state(room)
    with pytest.raises(KeyError):
        getattr(room, method)(locker_id)
    assert state(room) == before
