"""Hidden tests for the initial sample_freezers spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest private/test_freezers_initial.py
"""

import pytest
from freezers import FreezerError, Freezers


@pytest.fixture
def lab():
    """Freezers A, B and C: A holds a1, a2, a3; B holds b1; C is empty."""
    lab = Freezers()
    for freezer_id in ["A", "B", "C"]:
        lab.add_freezer(freezer_id)
    for sample_id in ["a1", "a2", "a3"]:
        lab.store("A", sample_id)
    lab.store("B", "b1")
    return lab


def state(lab):
    """The freezer list, every freezer's samples and where each sample is
    found, to check that a failed call changed nothing."""
    samples = {f: lab.get_samples(f) for f in lab.get_freezers()}
    found = {s: lab.find(s) for listed in samples.values() for s in listed}
    return lab.get_freezers(), samples, found


# --- freezers ---------------------------------------------------------------


def test_a_new_lab_has_no_freezers():
    assert Freezers().get_freezers() == []


def test_freezers_are_listed_in_the_order_added():
    lab = Freezers()
    for freezer_id in ["Z", "M", "A"]:
        lab.add_freezer(freezer_id)
    assert lab.get_freezers() == ["Z", "M", "A"]


def test_a_new_freezer_is_empty(lab):
    assert lab.get_samples("C") == []


def test_adding_a_freezer_id_in_use_is_rejected(lab):
    before = state(lab)
    with pytest.raises(FreezerError):
        lab.add_freezer("A")
    assert state(lab) == before


def test_a_removed_freezer_id_can_be_added_again_as_a_new_empty_freezer(lab):
    lab.remove_freezer("A", "C")
    lab.add_freezer("A")
    assert lab.get_freezers() == ["B", "C", "A"]
    assert lab.get_samples("A") == []
    assert lab.find("a1") == "C"
    lab.store("A", "new")
    lab.move("a2", "A")
    assert lab.get_samples("A") == ["new", "a2"]


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.store("X", "new"),
        lambda lab: lab.move("a1", "X"),
        lambda lab: lab.move_all("X", "B"),
        lambda lab: lab.move_all("A", "X"),
        lambda lab: lab.remove_freezer("X", "B"),
        lambda lab: lab.remove_freezer("A", "X"),
        lambda lab: lab.get_samples("X"),
    ],
)
def test_freezers_not_in_use_raise_key_error(lab, call):
    before = state(lab)
    with pytest.raises(KeyError):
        call(lab)
    assert state(lab) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.store("C", "new"),
        lambda lab: lab.move("a1", "C"),
        lambda lab: lab.move_all("C", "A"),
        lambda lab: lab.move_all("A", "C"),
        lambda lab: lab.remove_freezer("C", "A"),
        lambda lab: lab.remove_freezer("A", "C"),
        lambda lab: lab.get_samples("C"),
    ],
)
def test_a_removed_freezer_raises_key_error(lab, call):
    lab.remove_freezer("C", "B")
    before = state(lab)
    with pytest.raises(KeyError):
        call(lab)
    assert state(lab) == before


# --- samples ----------------------------------------------------------------


def test_stored_samples_are_listed_in_order_and_found(lab):
    assert lab.get_samples("A") == ["a1", "a2", "a3"]
    assert lab.get_samples("B") == ["b1"]
    assert lab.find("a2") == "A"
    assert lab.find("b1") == "B"


@pytest.mark.parametrize("freezer_id", ["A", "C"])
def test_a_stored_sample_id_cannot_be_stored_again(lab, freezer_id):
    before = state(lab)
    with pytest.raises(FreezerError):
        lab.store(freezer_id, "a2")
    assert state(lab) == before


def test_discard_removes_only_that_sample(lab):
    lab.discard("a2")
    assert lab.get_samples("A") == ["a1", "a3"]
    assert lab.get_samples("B") == ["b1"]
    with pytest.raises(KeyError):
        lab.find("a2")


def test_a_discarded_sample_id_can_be_stored_again(lab):
    lab.discard("a2")
    lab.store("A", "a2")
    assert lab.get_samples("A") == ["a1", "a3", "a2"]
    lab.discard("b1")
    lab.store("C", "b1")
    assert lab.find("b1") == "C"
    assert lab.get_samples("B") == []


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.discard("zz"),
        lambda lab: lab.move("zz", "B"),
        lambda lab: lab.find("zz"),
    ],
)
def test_samples_that_are_not_stored_raise_key_error(lab, call):
    before = state(lab)
    with pytest.raises(KeyError):
        call(lab)
    assert state(lab) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lab: lab.discard("a1"),
        lambda lab: lab.move("a1", "B"),
        lambda lab: lab.find("a1"),
    ],
)
def test_a_discarded_sample_raises_key_error(lab, call):
    lab.discard("a1")
    before = state(lab)
    with pytest.raises(KeyError):
        call(lab)
    assert state(lab) == before


def test_move_puts_the_sample_last_in_its_new_freezer(lab):
    lab.move("a2", "B")
    assert lab.get_samples("A") == ["a1", "a3"]
    assert lab.get_samples("B") == ["b1", "a2"]
    assert lab.find("a2") == "B"


def test_moving_a_sample_to_its_own_freezer_is_rejected(lab):
    before = state(lab)
    with pytest.raises(ValueError):
        lab.move("a2", "A")
    assert state(lab) == before


def test_a_sample_moved_away_and_back_arrives_last(lab):
    lab.move("a1", "B")
    lab.move("a1", "A")
    assert lab.get_samples("A") == ["a2", "a3", "a1"]
    assert lab.get_samples("B") == ["b1"]


# --- moving every sample ----------------------------------------------------


def test_move_all_keeps_the_order_after_the_samples_already_there(lab):
    assert lab.move_all("A", "B") == 3
    assert lab.get_samples("B") == ["b1", "a1", "a2", "a3"]
    assert lab.get_samples("A") == []
    assert [lab.find(s) for s in ["a1", "a2", "a3"]] == ["B", "B", "B"]
    assert lab.get_freezers() == ["A", "B", "C"]


def test_move_all_into_an_empty_freezer(lab):
    assert lab.move_all("A", "C") == 3
    assert lab.get_samples("C") == ["a1", "a2", "a3"]


def test_move_all_from_an_empty_freezer_moves_nothing(lab):
    before = state(lab)
    assert lab.move_all("C", "A") == 0
    assert state(lab) == before


@pytest.mark.parametrize("freezer_id", ["A", "C"])
def test_move_all_to_the_same_freezer_is_rejected(lab, freezer_id):
    before = state(lab)
    with pytest.raises(ValueError):
        lab.move_all(freezer_id, freezer_id)
    assert state(lab) == before


def test_an_emptied_freezer_can_be_filled_again(lab):
    lab.move_all("A", "B")
    lab.store("A", "new")
    lab.move("b1", "A")
    assert lab.get_samples("A") == ["new", "b1"]
    assert sorted(lab.get_samples("B")) == ["a1", "a2", "a3"]


def test_remove_freezer_moves_the_samples_then_removes_it(lab):
    assert lab.remove_freezer("A", "B") == 3
    assert lab.get_freezers() == ["B", "C"]
    assert lab.get_samples("B") == ["b1", "a1", "a2", "a3"]
    assert [lab.find(s) for s in ["a1", "a2", "a3"]] == ["B", "B", "B"]


def test_removing_a_freezer_keeps_the_order_of_the_others(lab):
    lab.add_freezer("D")
    assert lab.remove_freezer("B", "D") == 1
    assert lab.get_freezers() == ["A", "C", "D"]
    assert lab.get_samples("D") == ["b1"]


def test_removing_an_empty_freezer_moves_nothing(lab):
    assert lab.remove_freezer("C", "A") == 0
    assert lab.get_freezers() == ["A", "B"]
    assert lab.get_samples("A") == ["a1", "a2", "a3"]


@pytest.mark.parametrize("freezer_id", ["A", "C"])
def test_removing_a_freezer_into_itself_is_rejected(lab, freezer_id):
    before = state(lab)
    with pytest.raises(ValueError):
        lab.remove_freezer(freezer_id, freezer_id)
    assert state(lab) == before


def test_moved_samples_can_be_moved_and_discarded_later(lab):
    lab.remove_freezer("A", "B")
    lab.move("a2", "C")
    lab.discard("a1")
    assert lab.get_samples("B") == ["b1", "a3"]
    assert lab.get_samples("C") == ["a2"]


def test_samples_are_listed_in_order_of_arrival_by_every_route(lab):
    lab.store("C", "c1")
    lab.move("b1", "C")
    lab.move_all("A", "C")
    lab.add_freezer("D")
    lab.store("D", "d1")
    lab.store("D", "d2")
    lab.remove_freezer("D", "C")
    lab.store("C", "c2")
    assert lab.get_samples("C") == ["c1", "b1", "a1", "a2", "a3", "d1", "d2", "c2"]
    assert lab.get_freezers() == ["A", "B", "C"]


# --- order of errors ----------------------------------------------------------


def test_move_reports_key_errors_before_anything_else(lab):
    before = state(lab)
    with pytest.raises(KeyError):
        lab.move("zz", "X")
    with pytest.raises(KeyError):
        lab.move("zz", "A")
    assert state(lab) == before


def test_failed_calls_change_nothing(lab):
    before = state(lab)
    for call in (
        lambda: lab.store("A", "b1"),
        lambda: lab.move("a1", "A"),
        lambda: lab.move_all("B", "B"),
        lambda: lab.remove_freezer("A", "A"),
        lambda: lab.remove_freezer("A", "X"),
        lambda: lab.discard("zz"),
        lambda: lab.add_freezer("B"),
    ):
        with pytest.raises((KeyError, ValueError, FreezerError)):
            call()
    assert state(lab) == before


def test_freezer_error_is_an_exception():
    assert issubclass(FreezerError, Exception)


def test_labs_do_not_share_freezers_or_samples():
    first, second = Freezers(), Freezers()
    first.add_freezer("A")
    first.store("A", "s1")
    assert second.get_freezers() == []
    second.add_freezer("A")
    second.store("A", "s1")
    assert second.get_samples("A") == ["s1"]
    assert first.get_samples("A") == ["s1"]
