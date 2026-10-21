"""Public checks for lockers.py.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest public/test_lockers_public.py
"""

import pytest
from lockers import LockerRoom, NoLockerFree


@pytest.fixture
def room():
    r = LockerRoom()
    r.add_locker("S1", "small")
    r.add_locker("M1", "medium")
    r.add_locker("L1", "large")
    return r


def test_an_item_goes_into_a_locker_of_its_size(room):
    assert room.store("scarf", "small") == "S1"
    assert room.get_locker("scarf") == "S1"
    assert room.get_free_lockers() == ["M1", "L1"]
    assert room.get_takings() == 200


def test_the_smallest_locker_that_fits_is_used(room):
    assert room.store("coat", "medium") == "M1"
    assert room.store("boots", "medium") == "L1"
    assert room.get_free_lockers() == ["S1"]


def test_retrieving_frees_the_locker(room):
    room.store("bag", "large")
    assert room.retrieve("bag") == "L1"
    assert room.get_free_lockers() == ["S1", "M1", "L1"]
    assert room.get_takings() == 500


def test_an_item_that_fits_nowhere_raises(room):
    room.store("coat", "large")
    with pytest.raises(NoLockerFree):
        room.store("suitcase", "large")
    assert room.get_free_lockers() == ["S1", "M1"]


def test_an_unknown_size_is_rejected(room):
    with pytest.raises(ValueError):
        room.store("scarf", "tiny")


def test_retrieving_an_item_that_is_not_stored_raises(room):
    with pytest.raises(KeyError):
        room.retrieve("scarf")
