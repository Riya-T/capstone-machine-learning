"""Hidden tests for the c_lock change (locked freezers), which comes after
c_capacity. Never shown to the writer or the editor.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/private/test_lock_new.py
"""

import pytest
from freezers import FreezerError, Freezers, Full, Locked


@pytest.fixture
def lab():
    """Freezers A, B and C: A holds a1, a2; B holds b1; C is empty."""
    lab = Freezers()
    for freezer_id in ["A", "B", "C"]:
        lab.add_freezer(freezer_id)
    lab.store("A", "a1")
    lab.store("A", "a2")
    lab.store("B", "b1")
    return lab


def state(lab):
    """The freezer list, every freezer's samples and capacity, and where each
    sample is found, to check that a failed call changed nothing."""
    freezers = lab.get_freezers()
    samples = {f: lab.get_samples(f) for f in freezers}
    capacities = {f: lab.get_capacity(f) for f in freezers}
    found = {s: lab.find(s) for listed in samples.values() for s in listed}
    return freezers, samples, capacities, found


# --- lock and unlock ----------------------------------------------------------


@pytest.mark.parametrize("method", ["lock", "unlock"])
@pytest.mark.parametrize("freezer_id", ["X", "C"])
def test_locking_a_freezer_not_in_use_raises_key_error(lab, method, freezer_id):
    lab.remove_freezer("C", "A")
    before = state(lab)
    with pytest.raises(KeyError):
        getattr(lab, method)(freezer_id)
    assert state(lab) == before


def test_locking_twice_or_unlocking_an_unlocked_freezer_does_nothing(lab):
    lab.lock("A")
    lab.lock("A")
    with pytest.raises(Locked):
        lab.store("A", "new")
    lab.unlock("A")
    lab.store("A", "new")
    lab.unlock("A")
    lab.unlock("B")
    lab.store("B", "new2")
    assert lab.get_samples("A") == ["a1", "a2", "new"]
    assert lab.get_samples("B") == ["b1", "new2"]


def test_locking_and_unlocking_move_no_samples(lab):
    before = state(lab)
    lab.lock("A")
    assert state(lab) == before
    lab.unlock("A")
    assert state(lab) == before


def test_locked_is_a_freezer_error_but_not_full():
    assert issubclass(Locked, FreezerError)
    assert not issubclass(Locked, Full)
    assert not issubclass(Full, Locked)


# --- calls refused while a freezer is locked ----------------------------------


@pytest.mark.parametrize(
    "locked, call",
    [
        ("C", lambda lab: lab.store("C", "new")),
        ("A", lambda lab: lab.discard("a1")),
        ("A", lambda lab: lab.move("a1", "C")),
        ("C", lambda lab: lab.move("a1", "C")),
        ("A", lambda lab: lab.move_all("A", "B")),
        ("B", lambda lab: lab.move_all("A", "B")),
        ("A", lambda lab: lab.remove_freezer("A", "B")),
        ("B", lambda lab: lab.remove_freezer("A", "B")),
    ],
    ids=[
        "store_into",
        "discard_from",
        "move_from",
        "move_into",
        "move_all_from",
        "move_all_into",
        "remove_freezer_from",
        "remove_freezer_into",
    ],
)
def test_a_locked_freezer_refuses_every_movement(lab, locked, call):
    lab.lock(locked)
    before = state(lab)
    with pytest.raises(Locked):
        call(lab)
    assert state(lab) == before


@pytest.mark.parametrize(
    "locked, call",
    [
        ("A", lambda lab: lab.move_all("C", "A")),
        ("C", lambda lab: lab.move_all("C", "A")),
        ("C", lambda lab: lab.remove_freezer("C", "A")),
        ("A", lambda lab: lab.remove_freezer("C", "A")),
    ],
    ids=["move_all_into", "move_all_from", "remove_freezer_from", "remove_freezer_into"],
)
def test_a_locked_freezer_is_refused_even_with_nothing_to_move(lab, locked, call):
    lab.lock(locked)
    before = state(lab)
    with pytest.raises(Locked):
        call(lab)
    assert state(lab) == before
    assert lab.get_freezers() == ["A", "B", "C"]


def test_unlocking_lets_samples_move_again(lab):
    lab.lock("A")
    lab.lock("B")
    lab.unlock("A")
    lab.unlock("B")
    lab.move("b1", "A")
    assert lab.move_all("A", "C") == 3
    lab.discard("a1")
    assert lab.remove_freezer("C", "B") == 2
    assert lab.get_samples("B") == ["a2", "b1"]


def test_other_freezers_still_work_while_one_is_locked(lab):
    lab.lock("A")
    lab.store("B", "b2")
    lab.move("b1", "C")
    assert lab.move_all("B", "C") == 1
    lab.discard("b1")
    assert lab.remove_freezer("B", "C") == 0
    assert lab.get_samples("C") == ["b2"]
    assert lab.get_samples("A") == ["a1", "a2"]


def test_reading_and_capacities_work_on_a_locked_freezer(lab):
    lab.lock("A")
    assert lab.find("a1") == "A"
    assert lab.get_samples("A") == ["a1", "a2"]
    assert lab.get_freezers() == ["A", "B", "C"]
    lab.set_capacity("A", 1)
    assert lab.get_capacity("A") == 1
    assert lab.get_samples("A") == ["a1", "a2"]


def test_a_new_freezer_can_be_added_and_locked(lab):
    lab.lock("A")
    lab.add_freezer("D")
    lab.store("D", "d1")
    lab.lock("D")
    with pytest.raises(Locked):
        lab.move("d1", "B")
    assert lab.get_freezers() == ["A", "B", "C", "D"]


# --- order of errors ----------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.move("a1", "X"),
        lambda lab: lab.move("zz", "A"),
        lambda lab: lab.discard("zz"),
        lambda lab: lab.move_all("A", "X"),
        lambda lab: lab.move_all("X", "A"),
        lambda lab: lab.remove_freezer("A", "X"),
        lambda lab: lab.remove_freezer("X", "A"),
    ],
)
def test_key_errors_come_before_locked(lab, call):
    lab.lock("A")
    before = state(lab)
    with pytest.raises(KeyError):
        call(lab)
    assert state(lab) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.move("a1", "A"),
        lambda lab: lab.move_all("A", "A"),
        lambda lab: lab.remove_freezer("A", "A"),
    ],
    ids=["move", "move_all", "remove_freezer"],
)
def test_value_errors_come_before_locked(lab, call):
    lab.lock("A")
    before = state(lab)
    with pytest.raises(ValueError):
        call(lab)
    assert state(lab) == before


@pytest.mark.parametrize("freezer_id", ["A", "C"])
def test_locked_comes_before_a_duplicate_sample_id(lab, freezer_id):
    lab.lock(freezer_id)
    before = state(lab)
    with pytest.raises(Locked):
        lab.store(freezer_id, "b1")
    assert state(lab) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.store("C", "new"),
        lambda lab: lab.move("b1", "C"),
        lambda lab: lab.move_all("B", "C"),
        lambda lab: lab.remove_freezer("B", "C"),
    ],
    ids=["store", "move", "move_all", "remove_freezer"],
)
def test_locked_comes_before_full_in_the_receiving_freezer(lab, call):
    lab.set_capacity("C", 0)
    lab.lock("C")
    before = state(lab)
    with pytest.raises(Locked):
        call(lab)
    assert state(lab) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.move("b1", "C"),
        lambda lab: lab.move_all("B", "C"),
        lambda lab: lab.remove_freezer("B", "C"),
    ],
    ids=["move", "move_all", "remove_freezer"],
)
def test_locked_comes_before_full_when_the_sending_freezer_is_locked(lab, call):
    lab.set_capacity("C", 0)
    lab.lock("B")
    before = state(lab)
    with pytest.raises(Locked):
        call(lab)
    assert state(lab) == before


# --- capacities still apply ---------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.store("C", "new"),
        lambda lab: lab.move("a1", "C"),
        lambda lab: lab.move_all("A", "C"),
        lambda lab: lab.remove_freezer("A", "C"),
    ],
    ids=["store", "move", "move_all", "remove_freezer"],
)
def test_capacities_still_raise_full_with_locks_in_use(lab, call):
    lab.lock("A")
    lab.unlock("A")
    lab.lock("C")
    lab.unlock("C")
    lab.lock("B")  # a locked freezer the call does not involve
    lab.set_capacity("C", 0)
    before = state(lab)
    with pytest.raises(Full):
        call(lab)
    assert state(lab) == before


def test_moving_nothing_into_a_full_unlocked_freezer_still_works(lab):
    lab.lock("B")
    lab.set_capacity("A", 0)
    assert lab.move_all("C", "A") == 0
    assert lab.remove_freezer("C", "A") == 0
    assert lab.get_freezers() == ["A", "B"]
