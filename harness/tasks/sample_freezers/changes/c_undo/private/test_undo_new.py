"""Hidden tests for the c_undo change (undo). Never shown to the writer or the
editor.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from freezers import FreezerError, Freezers


@pytest.fixture
def lab():
    """Freezers A, B and C: A holds a1, a2, a3; B holds b1; C is empty.
    Building it takes 7 recorded calls."""
    lab = Freezers()
    for freezer_id in ["A", "B", "C"]:
        lab.add_freezer(freezer_id)
    for sample_id in ["a1", "a2", "a3"]:
        lab.store("A", sample_id)
    lab.store("B", "b1")
    return lab


def state(lab):
    """The freezer list, every freezer's samples and where each sample is
    found."""
    samples = {f: lab.get_samples(f) for f in lab.get_freezers()}
    found = {s: lab.find(s) for listed in samples.values() for s in listed}
    return lab.get_freezers(), samples, found


# --- undoing each kind of call --------------------------------------------------


def test_undo_on_a_new_lab_raises_freezer_error():
    lab = Freezers()
    with pytest.raises(FreezerError):
        lab.undo()
    assert lab.get_freezers() == []


def test_undoing_add_freezer_removes_it_and_frees_the_id(lab):
    before = state(lab)
    lab.add_freezer("D")
    lab.undo()
    assert state(lab) == before
    with pytest.raises(KeyError):
        lab.get_samples("D")
    lab.add_freezer("D")
    assert lab.get_freezers() == ["A", "B", "C", "D"]


def test_undoing_store_removes_the_sample_and_frees_the_id(lab):
    before = state(lab)
    lab.store("C", "c1")
    lab.undo()
    assert state(lab) == before
    with pytest.raises(KeyError):
        lab.find("c1")
    lab.store("A", "c1")
    assert lab.get_samples("A") == ["a1", "a2", "a3", "c1"]


@pytest.mark.parametrize("sample_id", ["a1", "a2", "a3"])
def test_undoing_discard_puts_the_sample_back_in_its_place(lab, sample_id):
    before = state(lab)
    lab.discard(sample_id)
    lab.undo()
    assert state(lab) == before


@pytest.mark.parametrize("sample_id", ["a1", "a2", "a3"])
def test_undoing_move_puts_the_sample_back_in_its_place(lab, sample_id):
    before = state(lab)
    lab.move(sample_id, "B")
    lab.undo()
    assert state(lab) == before
    assert lab.get_samples("B") == ["b1"]


@pytest.mark.parametrize("to_freezer", ["B", "C"])
def test_undoing_move_all_restores_both_freezers(lab, to_freezer):
    before = state(lab)
    assert lab.move_all("A", to_freezer) == 3
    lab.undo()
    assert state(lab) == before


@pytest.mark.parametrize("freezer_id, to_freezer", [("A", "B"), ("B", "C"), ("A", "C")])
def test_undoing_remove_freezer_brings_it_back_in_its_place(lab, freezer_id, to_freezer):
    before = state(lab)
    lab.remove_freezer(freezer_id, to_freezer)
    lab.undo()
    assert state(lab) == before
    assert lab.get_freezers() == ["A", "B", "C"]


def test_a_freezer_brought_back_is_in_use_again(lab):
    lab.remove_freezer("A", "B")
    lab.undo()
    with pytest.raises(FreezerError):
        lab.add_freezer("A")
    lab.store("A", "a4")
    assert lab.get_samples("A") == ["a1", "a2", "a3", "a4"]
    assert lab.remove_freezer("A", "C") == 4
    assert lab.get_samples("C") == ["a1", "a2", "a3", "a4"]


def test_a_move_all_of_nothing_still_counts(lab):
    lab.store("B", "b2")
    assert lab.move_all("C", "A") == 0
    lab.undo()  # takes back the move_all
    assert lab.get_samples("B") == ["b1", "b2"]
    lab.undo()  # takes back the store
    assert lab.get_samples("B") == ["b1"]


def test_removing_an_empty_freezer_can_be_undone(lab):
    before = state(lab)
    lab.store("B", "b2")
    after_store = state(lab)
    assert lab.remove_freezer("C", "A") == 0
    lab.undo()
    assert state(lab) == after_store
    assert lab.get_samples("C") == []
    lab.undo()
    assert state(lab) == before


# --- the order of undos -------------------------------------------------------


def test_each_undo_goes_one_call_further_back(lab):
    states = [state(lab)]
    for call in (
        lambda: lab.move("a1", "C"),
        lambda: lab.store("C", "c1"),
        lambda: lab.move_all("C", "B"),
        lambda: lab.discard("a2"),
        lambda: lab.add_freezer("D"),
        lambda: lab.remove_freezer("B", "D"),
        lambda: lab.move("b1", "A"),
        lambda: lab.store("A", "a2"),
    ):
        call()
        states.append(state(lab))
    assert lab.get_samples("A") == ["a3", "b1", "a2"]
    for expected in reversed(states[:-1]):
        lab.undo()
        assert state(lab) == expected


def test_undo_goes_back_through_every_call_to_the_start(lab):
    for _ in range(7):
        lab.undo()
    assert lab.get_freezers() == []
    with pytest.raises(FreezerError):
        lab.undo()
    lab.add_freezer("A")
    lab.store("A", "a1")
    assert lab.get_samples("A") == ["a1"]


def test_a_sample_moved_twice_comes_back_one_step_at_a_time(lab):
    lab.move("a1", "B")
    lab.move("a1", "A")
    assert lab.get_samples("A") == ["a2", "a3", "a1"]
    lab.undo()
    assert lab.get_samples("A") == ["a2", "a3"]
    assert lab.get_samples("B") == ["b1", "a1"]
    lab.undo()
    assert lab.get_samples("A") == ["a1", "a2", "a3"]
    assert lab.get_samples("B") == ["b1"]


def test_failed_calls_are_not_recorded(lab):
    before = state(lab)
    lab.store("C", "c1")
    for call in (
        lambda: lab.store("C", "a1"),
        lambda: lab.store("X", "c2"),
        lambda: lab.add_freezer("A"),
        lambda: lab.discard("zz"),
        lambda: lab.move("a1", "A"),
        lambda: lab.move_all("X", "A"),
        lambda: lab.move_all("B", "B"),
        lambda: lab.remove_freezer("A", "A"),
        lambda: lab.remove_freezer("A", "X"),
    ):
        with pytest.raises((KeyError, ValueError, FreezerError)):
            call()
    lab.undo()  # takes back the store, the last call that succeeded
    assert state(lab) == before


def test_reading_is_not_recorded(lab):
    before = state(lab)
    lab.store("C", "c1")
    lab.find("c1")
    lab.get_samples("C")
    lab.get_freezers()
    lab.undo()
    assert state(lab) == before


def test_undo_is_not_recorded_so_there_is_no_redo(lab):
    before = state(lab)
    lab.store("C", "c1")
    lab.store("C", "c2")
    lab.undo()
    lab.undo()
    assert state(lab) == before


def test_calls_after_an_undo_are_recorded_as_usual(lab):
    before = state(lab)
    lab.store("C", "c1")
    lab.undo()
    lab.store("C", "c2")
    lab.move("c2", "A")
    lab.undo()
    assert lab.get_samples("C") == ["c2"]
    assert lab.get_samples("A") == ["a1", "a2", "a3"]
    lab.undo()
    assert state(lab) == before
    lab.undo()  # the last call that built the fixture: store("B", "b1")
    assert lab.get_samples("B") == []


def test_nothing_left_to_undo_changes_nothing():
    lab = Freezers()
    lab.add_freezer("A")
    lab.undo()
    with pytest.raises(FreezerError):
        lab.undo()
    assert lab.get_freezers() == []
    lab.add_freezer("A")
    assert lab.get_freezers() == ["A"]
