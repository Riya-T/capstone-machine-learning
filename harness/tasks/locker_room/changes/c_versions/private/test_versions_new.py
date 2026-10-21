"""Hidden tests for the c_versions change (locker versions and moves).
Never shown to the writer or the editor.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from lockers import LockerError, LockerRoom, NoLockerFree, VersionConflict

LOCKERS = [("S1", "small"), ("S2", "small"), ("M1", "medium"), ("L1", "large")]
ITEMS = ["hat", "coat", "bag"]


@pytest.fixture
def room():
    """hat is in S1 (version 2) and coat in M1 (version 2); S2 and L1 are
    free at version 1."""
    r = LockerRoom()
    for locker_id, size in LOCKERS:
        r.add_locker(locker_id, size)
    r.store("hat", "small")
    r.store("coat", "medium")
    return r


def state(r):
    where = {}
    for item in ITEMS:
        try:
            where[item] = r.get_locker(item)
        except KeyError:
            where[item] = None
    versions = {locker_id: r.get_version(locker_id) for locker_id, _ in LOCKERS}
    return r.get_free_lockers(), r.get_takings(), where, versions


def test_version_counts_every_item_in_and_out(room):
    assert [room.get_version(x) for x, _ in LOCKERS] == [2, 1, 2, 1]
    room.retrieve("hat")
    room.store("bag", "small")
    room.retrieve("bag")
    assert room.get_version("S1") == 5
    assert [room.get_version(x) for x in ["S2", "M1", "L1"]] == [1, 2, 1]


def test_version_does_not_change_on_reads_or_failed_calls(room):
    before = state(room)
    room.get_free_lockers()
    room.get_locker("hat")
    room.get_takings()
    for call in (
        lambda: room.store("hat", "small"),
        lambda: room.store("bag", "huge"),
        lambda: room.retrieve("bag"),
        lambda: room.add_locker("S1", "small"),
        lambda: room.move("hat", "M1"),
        lambda: room.retrieve("hat", expected_version=1),
    ):
        with pytest.raises((ValueError, KeyError, LockerError)):
            call()
    assert state(room) == before


def test_version_of_a_failed_store_stays(room):
    room.store("bag", "large")
    before = state(room)
    with pytest.raises(NoLockerFree):
        room.store("box", "large")
    assert state(room) == before


@pytest.mark.parametrize("stale", [1, 3, "2", 2.5])
def test_version_mismatch_on_retrieve_changes_nothing(room, stale):
    before = state(room)
    with pytest.raises(VersionConflict):
        room.retrieve("hat", expected_version=stale)
    assert state(room) == before
    assert room.retrieve("hat", expected_version=2) == "S1"


def test_version_conflict_is_a_locker_error():
    assert issubclass(VersionConflict, LockerError)


def test_version_needs_a_known_locker(room):
    for locker_id in ["Q9", None, 1, "hat"]:
        with pytest.raises(KeyError):
            room.get_version(locker_id)


def test_version_check_comes_after_the_missing_item(room):
    with pytest.raises(KeyError):
        room.retrieve("bag", expected_version=99)
    with pytest.raises(KeyError):
        room.move("bag", "L1", expected_version=99)


def test_move_frees_the_old_locker_and_charges_nothing(room):
    room.move("hat", "S2")
    assert room.get_locker("hat") == "S2"
    assert room.get_free_lockers() == ["S1", "L1"]
    assert room.get_takings() == 500
    assert [room.get_version(x) for x, _ in LOCKERS] == [3, 2, 2, 1]
    assert room.store("bag", "small") == "S1"
    assert room.retrieve("hat") == "S2"


def test_move_to_a_larger_locker_and_back(room):
    room.move("hat", "L1", expected_version=1)
    room.move("hat", "S1", expected_version=3)
    assert room.get_locker("hat") == "S1"
    assert room.get_version("S1") == 4
    assert room.get_version("L1") == 3


def test_move_keeps_the_size_the_item_was_stored_with(room):
    room.store("bag", "small")  # goes into S2
    room.move("bag", "L1")
    room.retrieve("hat")
    room.move("bag", "S1")
    assert room.get_locker("bag") == "S1"
    with pytest.raises(LockerError):
        # coat was stored as medium; S2 is empty but small.
        room.move("coat", "S2")


def test_move_errors_come_in_order(room):
    room.store("bag", "large")  # L1, version 2
    before = state(room)
    for call, error in (
        (lambda: room.move("box", "Q9", expected_version=7), KeyError),
        (lambda: room.move("hat", "Q9", expected_version=7), KeyError),
        (lambda: room.move("hat", None), KeyError),
        (lambda: room.move("coat", "L1", expected_version=1), VersionConflict),
        (lambda: room.move("coat", "S2", expected_version=2), VersionConflict),
        (lambda: room.move("coat", "L1", expected_version=2), LockerError),
        (lambda: room.move("coat", "M1"), LockerError),
        (lambda: room.move("coat", "S2", expected_version=1), LockerError),
    ):
        with pytest.raises(error) as caught:
            call()
        if error is LockerError:
            assert not isinstance(caught.value, VersionConflict)
    assert state(room) == before


def test_move_is_refused_into_a_locker_in_use(room):
    before = state(room)
    with pytest.raises(LockerError):
        room.move("hat", "M1")
    with pytest.raises(LockerError):
        room.move("hat", "S1")
    assert state(room) == before
