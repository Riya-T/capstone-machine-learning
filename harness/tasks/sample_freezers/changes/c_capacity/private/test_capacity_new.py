"""Hidden tests for the c_capacity change (freezer capacities). Never shown to
the writer or the editor.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from freezers import FreezerError, Freezers, Full

BAD_CAPACITIES = [-1, 1.5, "3", [2]]


@pytest.fixture
def lab():
    """Freezers A, B and C: A holds a1, a2; B holds b1, b2, b3; C is empty."""
    lab = Freezers()
    for freezer_id in ["A", "B", "C"]:
        lab.add_freezer(freezer_id)
    for sample_id in ["a1", "a2"]:
        lab.store("A", sample_id)
    for sample_id in ["b1", "b2", "b3"]:
        lab.store("B", sample_id)
    return lab


def state(lab):
    """The freezer list, every freezer's samples and capacity, and where each
    sample is found, to check that a failed call changed nothing."""
    freezers = lab.get_freezers()
    samples = {f: lab.get_samples(f) for f in freezers}
    capacities = {f: lab.get_capacity(f) for f in freezers}
    found = {s: lab.find(s) for listed in samples.values() for s in listed}
    return freezers, samples, capacities, found


# --- setting capacities -------------------------------------------------------


def test_every_freezer_starts_without_a_capacity(lab):
    assert [lab.get_capacity(f) for f in ["A", "B", "C"]] == [None, None, None]
    lab.add_freezer("D")
    assert lab.get_capacity("D") is None


def test_without_a_capacity_any_number_of_samples_fit(lab):
    for i in range(40):
        lab.store("C", f"c{i}")
    assert len(lab.get_samples("C")) == 40
    assert lab.move_all("C", "A") == 40


def test_set_capacity_replaces_the_capacity(lab):
    lab.set_capacity("C", 5)
    assert lab.get_capacity("C") == 5
    lab.set_capacity("C", 0)
    assert lab.get_capacity("C") == 0
    lab.set_capacity("C", None)
    assert lab.get_capacity("C") is None


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_invalid_capacities_are_rejected(lab, capacity):
    lab.set_capacity("A", 4)
    before = state(lab)
    with pytest.raises(ValueError):
        lab.set_capacity("A", capacity)
    assert state(lab) == before
    assert lab.get_capacity("A") == 4


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.get_capacity("X"),
        lambda lab: lab.set_capacity("X", 3),
        lambda lab: lab.set_capacity("X", -1),
        lambda lab: lab.get_capacity("C"),
        lambda lab: lab.set_capacity("C", 3),
    ],
)
def test_capacity_of_a_freezer_not_in_use_raises_key_error(lab, call):
    lab.remove_freezer("C", "A")
    before = state(lab)
    with pytest.raises(KeyError):
        call(lab)
    assert state(lab) == before


def test_setting_a_capacity_moves_no_samples(lab):
    before = state(lab)
    lab.set_capacity("B", 1)
    lab.set_capacity("B", None)
    assert state(lab) == before


def test_capacities_belong_to_one_freezer(lab):
    lab.set_capacity("C", 1)
    lab.store("A", "a3")
    lab.move("b1", "A")
    assert lab.get_capacity("A") is None
    assert lab.get_capacity("B") is None
    assert lab.get_samples("A") == ["a1", "a2", "a3", "b1"]


def test_full_is_a_freezer_error():
    assert issubclass(Full, FreezerError)


# --- store and move -----------------------------------------------------------


def test_store_fills_up_to_the_capacity_and_no_further(lab):
    lab.set_capacity("C", 2)
    lab.store("C", "c1")
    lab.store("C", "c2")
    before = state(lab)
    with pytest.raises(Full):
        lab.store("C", "c3")
    assert state(lab) == before
    with pytest.raises(KeyError):
        lab.find("c3")


def test_a_discarded_sample_makes_room(lab):
    lab.set_capacity("C", 1)
    lab.store("C", "c1")
    lab.discard("c1")
    lab.store("C", "c2")
    assert lab.get_samples("C") == ["c2"]


def test_moving_into_a_full_freezer_raises_full_and_changes_nothing(lab):
    lab.set_capacity("C", 1)
    lab.store("C", "c1")
    before = state(lab)
    with pytest.raises(Full):
        lab.move("a1", "C")
    assert state(lab) == before


def test_moving_up_to_the_capacity_works(lab):
    lab.set_capacity("C", 2)
    lab.move("a1", "C")
    lab.move("b2", "C")
    assert lab.get_samples("C") == ["a1", "b2"]
    with pytest.raises(Full):
        lab.move("a2", "C")


def test_samples_can_always_leave_a_full_freezer(lab):
    lab.set_capacity("B", 3)
    lab.move("b1", "A")
    assert lab.get_samples("B") == ["b2", "b3"]
    lab.move("a1", "B")
    assert lab.get_samples("B") == ["b2", "b3", "a1"]


def test_removing_the_limit_lets_samples_in_again(lab):
    lab.set_capacity("C", 0)
    with pytest.raises(Full):
        lab.store("C", "c1")
    lab.set_capacity("C", None)
    lab.store("C", "c1")
    assert lab.get_samples("C") == ["c1"]


# --- a capacity below the current count ---------------------------------------


def test_a_capacity_below_the_count_keeps_the_samples(lab):
    lab.set_capacity("B", 1)
    assert lab.get_samples("B") == ["b1", "b2", "b3"]
    assert lab.get_capacity("B") == 1


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.store("B", "new"),
        lambda lab: lab.move("a1", "B"),
        lambda lab: lab.move_all("A", "B"),
        lambda lab: lab.remove_freezer("A", "B"),
    ],
    ids=["store", "move", "move_all", "remove_freezer"],
)
def test_nothing_goes_into_a_freezer_over_its_capacity(lab, call):
    lab.set_capacity("B", 1)
    before = state(lab)
    with pytest.raises(Full):
        call(lab)
    assert state(lab) == before


def test_an_over_full_freezer_accepts_samples_once_enough_have_left(lab):
    lab.set_capacity("B", 2)
    lab.discard("b1")
    with pytest.raises(Full):
        lab.store("B", "new")
    lab.move("b2", "C")
    lab.store("B", "new")
    assert lab.get_samples("B") == ["b3", "new"]


def test_only_the_receiving_freezer_capacity_counts(lab):
    lab.set_capacity("A", 0)  # A holds 2, more than its capacity
    lab.move("a1", "C")
    assert lab.move_all("A", "C") == 1
    assert lab.get_samples("C") == ["a1", "a2"]


# --- move_all and remove_freezer ----------------------------------------------


def test_move_all_that_fits_exactly(lab):
    lab.set_capacity("C", 3)
    assert lab.move_all("B", "C") == 3
    assert lab.get_samples("C") == ["b1", "b2", "b3"]


def test_move_all_that_does_not_fit_moves_nothing(lab):
    lab.set_capacity("C", 3)
    lab.store("C", "c1")  # room for 2 more, but B holds 3
    before = state(lab)
    with pytest.raises(Full):
        lab.move_all("B", "C")
    assert state(lab) == before
    assert lab.get_samples("B") == ["b1", "b2", "b3"]


def test_move_all_after_existing_samples_up_to_the_capacity(lab):
    lab.set_capacity("A", 5)
    assert lab.move_all("B", "A") == 3
    assert lab.get_samples("A") == ["a1", "a2", "b1", "b2", "b3"]


def test_remove_freezer_that_fits_exactly(lab):
    lab.set_capacity("A", 5)
    assert lab.remove_freezer("B", "A") == 3
    assert lab.get_samples("A") == ["a1", "a2", "b1", "b2", "b3"]
    assert lab.get_freezers() == ["A", "C"]


def test_remove_freezer_that_does_not_fit_moves_nothing_and_keeps_the_freezer(lab):
    lab.set_capacity("A", 4)  # room for 2 more, but B holds 3
    before = state(lab)
    with pytest.raises(Full):
        lab.remove_freezer("B", "A")
    assert state(lab) == before
    assert lab.get_freezers() == ["A", "B", "C"]
    lab.store("B", "b4")  # B is still in use
    lab.set_capacity("A", 6)
    assert lab.remove_freezer("B", "A") == 4


def test_remove_freezer_into_an_empty_freezer_with_too_little_room(lab):
    lab.set_capacity("C", 2)
    before = state(lab)
    with pytest.raises(Full):
        lab.remove_freezer("B", "C")
    assert state(lab) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.move_all("C", "A"),
        lambda lab: lab.remove_freezer("C", "A"),
    ],
    ids=["move_all", "remove_freezer"],
)
def test_moving_zero_samples_never_raises_full(lab, call):
    lab.set_capacity("A", 0)  # A holds 2, more than its capacity
    assert call(lab) == 0
    assert lab.get_samples("A") == ["a1", "a2"]


def test_removing_an_empty_freezer_into_a_full_one_removes_it(lab):
    lab.set_capacity("B", 3)
    assert lab.remove_freezer("C", "B") == 0
    assert lab.get_freezers() == ["A", "B"]


# --- order of errors ----------------------------------------------------------


@pytest.mark.parametrize(
    "call, error",
    [
        (lambda lab: lab.store("X", "new"), KeyError),
        (lambda lab: lab.move("a1", "A"), ValueError),
        (lambda lab: lab.move("zz", "A"), KeyError),
        (lambda lab: lab.move_all("A", "A"), ValueError),
        (lambda lab: lab.move_all("B", "X"), KeyError),
        (lambda lab: lab.remove_freezer("A", "A"), ValueError),
        (lambda lab: lab.remove_freezer("X", "A"), KeyError),
    ],
)
def test_earlier_errors_are_raised_instead_of_full(lab, call, error):
    lab.set_capacity("A", 0)  # A holds 2, more than its capacity
    before = state(lab)
    with pytest.raises(error):
        call(lab)
    assert state(lab) == before


@pytest.mark.parametrize("freezer_id", ["A", "C"])
def test_a_duplicate_sample_id_is_reported_instead_of_full(lab, freezer_id):
    lab.set_capacity(freezer_id, 0)
    before = state(lab)
    with pytest.raises(FreezerError) as caught:
        lab.store(freezer_id, "b1")
    assert not isinstance(caught.value, Full)
    assert state(lab) == before


# --- with undo (s2 only) ------------------------------------------------------
# In s2 this change comes after c_undo. These checks return at once when the
# program has no undo (s1), and never depend on whether set_capacity itself
# can be undone: every capacity is set before the calls that undo reverses.


def undo_lab():
    """A holds a1, a2 with capacity 1 (over it); B holds b1, b2, b3 with no
    capacity; C holds c1 with capacity 1 (full). The last call undo can
    reverse is store("C", "c1"). None if the program has no undo."""
    lab = Freezers()
    if not hasattr(lab, "undo"):
        return None
    for freezer_id in ["A", "B", "C"]:
        lab.add_freezer(freezer_id)
    for sample_id in ["a1", "a2"]:
        lab.store("A", sample_id)
    for sample_id in ["b1", "b2", "b3"]:
        lab.store("B", sample_id)
    lab.set_capacity("A", 1)
    lab.set_capacity("C", 1)
    lab.store("C", "c1")
    return lab


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.store("C", "c2"),
        lambda lab: lab.move("a1", "C"),
        lambda lab: lab.move_all("A", "C"),
        lambda lab: lab.remove_freezer("B", "C"),
    ],
    ids=["store", "move", "move_all", "remove_freezer"],
)
def test_a_call_that_raises_full_is_not_recorded_for_undo(call):
    lab = undo_lab()
    if lab is None:
        return
    with pytest.raises(Full):
        call(lab)
    lab.undo()  # reverses store("C", "c1"), the last call that succeeded
    assert lab.get_freezers() == ["A", "B", "C"]
    assert lab.get_samples("C") == []
    assert lab.get_samples("A") == ["a1", "a2"]
    assert lab.get_samples("B") == ["b1", "b2", "b3"]


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.discard("a1"),
        lambda lab: lab.move("a1", "B"),
        lambda lab: lab.move_all("A", "B"),
    ],
    ids=["discard", "move", "move_all"],
)
def test_undo_puts_samples_back_into_a_freezer_over_its_capacity(call):
    lab = undo_lab()
    if lab is None:
        return
    call(lab)
    lab.undo()  # A goes back over its capacity of 1: undo checks no capacity
    assert lab.get_samples("A") == ["a1", "a2"]
    assert lab.get_samples("B") == ["b1", "b2", "b3"]
    assert lab.find("a1") == "A"
