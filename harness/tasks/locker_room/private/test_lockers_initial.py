"""Hidden tests for the initial locker_room spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest private/test_lockers_initial.py
"""

import pytest
from lockers import LockerError, LockerRoom, NoLockerFree

BAD_SIZES = ["huge", "Small", "", None, 1]
ITEMS = ["hat", "coat", "bag", "skis", "box"]


@pytest.fixture
def room():
    """Two small, one medium and one large locker, all free."""
    r = LockerRoom()
    for locker_id, size in [("S1", "small"), ("S2", "small"), ("M1", "medium"), ("L1", "large")]:
        r.add_locker(locker_id, size)
    return r


def state(r, items=ITEMS):
    """Free lockers, takings and where each item is, to check that a failed
    call changed nothing."""
    where = {}
    for item in items:
        try:
            where[item] = r.get_locker(item)
        except KeyError:
            where[item] = None
    return r.get_free_lockers(), r.get_takings(), where


# --- lockers ------------------------------------------------------------------


def test_a_new_room_is_empty():
    r = LockerRoom()
    assert r.get_free_lockers() == []
    assert r.get_takings() == 0
    with pytest.raises(NoLockerFree):
        r.store("hat", "small")


def test_lockers_are_listed_in_the_order_added():
    r = LockerRoom()
    for locker_id, size in [("Z9", "large"), ("A1", "small"), ("K5", "medium")]:
        r.add_locker(locker_id, size)
    assert r.get_free_lockers() == ["Z9", "A1", "K5"]


@pytest.mark.parametrize("size", BAD_SIZES)
def test_lockers_need_a_known_size(size):
    r = LockerRoom()
    with pytest.raises(ValueError):
        r.add_locker("A1", size)
    assert r.get_free_lockers() == []


def test_lockers_need_an_id():
    r = LockerRoom()
    with pytest.raises(ValueError):
        r.add_locker("", "small")
    assert r.get_free_lockers() == []


def test_adding_a_locker_twice_is_rejected(room):
    room.store("hat", "small")
    before = state(room)
    with pytest.raises(LockerError):
        room.add_locker("S1", "large")
    with pytest.raises(ValueError):
        # The bad size is reported before the id that was already added.
        room.add_locker("S1", "huge")
    assert state(room) == before


# --- storing ------------------------------------------------------------------


def test_lockers_of_one_size_are_used_in_the_order_added(room):
    assert room.store("hat", "small") == "S1"
    assert room.store("gloves", "small") == "S2"
    assert room.store("scarf", "small") == "M1"
    assert room.store("cap", "small") == "L1"
    with pytest.raises(NoLockerFree):
        room.store("sock", "small")


def test_a_freed_locker_is_used_again_before_a_larger_one(room):
    room.store("hat", "small")
    room.store("gloves", "small")
    room.retrieve("hat")
    assert room.store("scarf", "small") == "S1"
    assert room.get_free_lockers() == ["M1", "L1"]


def test_a_freed_locker_comes_back_in_its_place(room):
    room.store("hat", "small")
    room.store("gloves", "small")
    room.retrieve("hat")
    assert room.get_free_lockers() == ["S1", "M1", "L1"]


def test_an_item_never_goes_into_a_smaller_locker(room):
    room.store("bag", "large")
    before = state(room)
    with pytest.raises(NoLockerFree):
        room.store("skis", "large")
    with pytest.raises(NoLockerFree):
        room.store("box", "large")
    assert state(room) == before
    assert room.store("coat", "medium") == "M1"


def test_the_fee_depends_on_the_locker_not_the_item(room):
    room.store("hat", "small")  # S1: 200
    room.store("gloves", "small")  # S2: 200
    room.store("scarf", "small")  # M1: 300
    room.store("cap", "small")  # L1: 500
    assert room.get_takings() == 1200


def test_takings_add_up_over_stores_and_are_never_refunded(room):
    room.store("bag", "large")
    room.retrieve("bag")
    room.store("bag", "medium")
    room.retrieve("bag")
    assert room.get_takings() == 500 + 300


def test_storing_an_item_that_is_already_stored_is_rejected(room):
    room.store("hat", "small")
    before = state(room)
    with pytest.raises(LockerError):
        room.store("hat", "small")
    with pytest.raises(LockerError):
        room.store("hat", "large")
    assert state(room) == before


def test_an_item_can_be_stored_again_after_retrieving(room):
    room.store("hat", "medium")
    room.retrieve("hat")
    assert room.store("hat", "small") == "S1"
    assert room.get_locker("hat") == "S1"


@pytest.mark.parametrize("size", BAD_SIZES)
def test_storing_needs_a_known_size(room, size):
    before = state(room)
    with pytest.raises(ValueError):
        room.store("hat", size)
    assert state(room) == before


def test_storing_needs_an_item_id(room):
    before = state(room)
    with pytest.raises(ValueError):
        room.store("", "small")
    assert state(room) == before


def test_store_errors_come_in_order():
    r = LockerRoom()
    r.add_locker("S1", "small")
    r.store("hat", "small")
    # No locker is free, so each call also has a NoLockerFree problem.
    with pytest.raises(ValueError):
        r.store("hat", "huge")
    with pytest.raises(ValueError):
        r.store("", "small")
    with pytest.raises(LockerError) as caught:
        r.store("hat", "small")
    assert not isinstance(caught.value, NoLockerFree)
    assert r.get_takings() == 200


# --- retrieving -----------------------------------------------------------------


def test_retrieve_returns_the_locker_and_forgets_the_item(room):
    room.store("hat", "small")
    room.store("coat", "medium")
    assert room.retrieve("coat") == "M1"
    with pytest.raises(KeyError):
        room.get_locker("coat")
    assert room.get_locker("hat") == "S1"


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.retrieve("skis"),
        lambda r: r.get_locker("skis"),
        lambda r: r.retrieve("S1"),
        lambda r: r.retrieve(None),
        lambda r: r.get_locker(1),
    ],
)
def test_items_that_are_not_stored_raise_key_error(room, call):
    room.store("hat", "small")
    before = state(room)
    with pytest.raises(KeyError):
        call(room)
    assert state(room) == before


def test_retrieving_twice_is_rejected(room):
    room.store("hat", "small")
    room.retrieve("hat")
    before = state(room)
    with pytest.raises(KeyError):
        room.retrieve("hat")
    assert state(room) == before


def test_no_locker_free_is_a_locker_error():
    assert issubclass(NoLockerFree, LockerError)


def test_rooms_do_not_share_lockers():
    first, second = LockerRoom(), LockerRoom()
    first.add_locker("S1", "small")
    first.store("hat", "small")
    assert second.get_free_lockers() == []
    assert second.get_takings() == 0
    second.add_locker("S1", "small")
    assert second.store("hat", "small") == "S1"
