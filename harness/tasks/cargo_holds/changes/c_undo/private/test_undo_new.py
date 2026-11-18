"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor. They call only the spec's methods and undo, since they run in
both sequences.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from ship import CargoError, NotEnoughCrates, Ship


@pytest.fixture
def ship():
    s = Ship()
    for name in ["fore", "mid", "aft"]:
        s.add_hold(name)
    s.load("fore", "grain", 3)
    s.load("fore", "steel", 2)
    s.load("mid", "coal", 4)
    return s


def state(s):
    return [(h, [(c, s.get_count(h, c)) for c in s.get_cargo(h)]) for h in s.get_holds()]


# --- each call can be undone ----------------------------------------------------


def test_undo_of_a_load_of_a_new_cargo_type(ship):
    before = state(ship)
    ship.load("aft", "wool", 2)
    ship.undo()
    assert state(ship) == before
    assert ship.get_cargo("aft") == []


def test_undo_of_a_load_of_more_of_a_cargo_type(ship):
    ship.load("fore", "grain", 5)
    ship.undo()
    assert ship.get_count("fore", "grain") == 3


def test_undo_of_an_unload(ship):
    before = state(ship)
    ship.unload("fore", "grain", 1)
    ship.undo()
    assert state(ship) == before


def test_undo_of_unloading_every_crate_of_a_cargo_type(ship):
    before = state(ship)
    ship.unload("fore", "steel", 2)
    ship.undo()
    assert state(ship) == before
    assert ship.get_cargo("fore") == ["grain", "steel"]


def test_one_undo_takes_back_a_whole_shift_all(ship):
    before = state(ship)
    assert ship.shift_all("fore", "mid") == 5
    ship.undo()
    assert state(ship) == before
    assert ship.get_cargo("mid") == ["coal"]


def test_undo_of_a_shift_all_into_an_empty_hold(ship):
    before = state(ship)
    ship.shift_all("mid", "aft")
    ship.undo()
    assert state(ship) == before
    assert ship.get_cargo("aft") == []


def test_undo_of_a_shift_all_onto_the_same_cargo_type(ship):
    ship.load("aft", "grain", 4)
    before = state(ship)
    ship.shift_all("fore", "aft")
    assert ship.get_count("aft", "grain") == 7
    ship.undo()
    assert state(ship) == before
    assert ship.get_count("aft", "grain") == 4


def test_undo_of_seal_hold_brings_it_back_with_its_crates(ship):
    before = state(ship)
    assert ship.seal_hold("fore", "aft") == 5
    ship.undo()
    assert state(ship) == before
    assert ship.get_holds() == ["fore", "mid", "aft"]
    assert ship.get_count("aft", "grain") == 0


def test_undo_of_seal_hold_puts_it_back_at_its_place_in_the_list(ship):
    ship.add_hold("bow")
    before = state(ship)
    ship.seal_hold("mid", "bow")
    assert ship.get_holds() == ["fore", "aft", "bow"]
    ship.undo()
    assert ship.get_holds() == ["fore", "mid", "aft", "bow"]
    assert state(ship) == before


def test_a_hold_brought_back_is_in_use_again(ship):
    ship.seal_hold("fore", "aft")
    ship.undo()
    ship.load("fore", "grain", 1)
    assert ship.get_count("fore", "grain") == 4
    with pytest.raises(CargoError):
        ship.add_hold("fore")
    assert ship.seal_hold("fore", "mid") == 6
    assert ship.get_holds() == ["mid", "aft"]


def test_undo_of_add_hold_removes_it_and_frees_the_name(ship):
    ship.add_hold("bow")
    ship.undo()
    assert ship.get_holds() == ["fore", "mid", "aft"]
    with pytest.raises(KeyError):
        ship.get_cargo("bow")
    ship.add_hold("bow")
    assert ship.get_holds() == ["fore", "mid", "aft", "bow"]
    assert ship.get_cargo("bow") == []


def test_undoing_two_seals_in_a_row_restores_the_order(ship):
    before = state(ship)
    ship.seal_hold("fore", "aft")
    ship.seal_hold("mid", "aft")
    assert ship.get_holds() == ["aft"]
    ship.undo()
    assert ship.get_holds() == ["mid", "aft"]
    assert ship.get_count("aft", "coal") == 0
    assert ship.get_count("aft", "grain") == 3
    ship.undo()
    assert state(ship) == before


# --- calls that move nothing ----------------------------------------------------


def test_a_shift_all_of_nothing_is_still_a_call(ship):
    ship.load("aft", "wool", 1)
    ship.unload("aft", "wool", 1)
    assert ship.shift_all("aft", "fore") == 0
    ship.undo()  # the shift_all, which changed nothing
    assert ship.get_cargo("aft") == []
    ship.undo()  # the unload
    assert ship.get_count("aft", "wool") == 1


def test_undo_of_a_seal_after_a_shift_all_of_nothing(ship):
    ship.load("mid", "coal", 1)
    assert ship.shift_all("aft", "mid") == 0
    assert ship.seal_hold("mid", "fore") == 5
    ship.undo()
    assert ship.get_holds() == ["fore", "mid", "aft"]
    assert ship.get_count("mid", "coal") == 5
    assert ship.get_count("fore", "coal") == 0
    ship.undo()  # the shift_all of nothing
    assert ship.get_count("mid", "coal") == 5
    ship.undo()
    assert ship.get_count("mid", "coal") == 4


# --- what is and is not recorded --------------------------------------------------


def test_each_undo_goes_one_call_further_back():
    s = Ship()
    calls = [
        lambda: s.add_hold("fore"),
        lambda: s.add_hold("mid"),
        lambda: s.load("fore", "grain", 5),
        lambda: s.load("fore", "steel", 2),
        lambda: s.add_hold("aft"),
        lambda: s.load("mid", "coal", 4),
        lambda: s.unload("fore", "grain", 1),
        lambda: s.shift_all("mid", "aft"),
        lambda: s.seal_hold("fore", "aft"),
        lambda: s.add_hold("bow"),
        lambda: s.load("bow", "wool", 1),
        lambda: s.shift_all("mid", "bow"),
        lambda: s.seal_hold("bow", "mid"),
    ]
    states = [state(s)]
    for call in calls:
        call()
        states.append(state(s))
    assert s.get_holds() == ["mid", "aft"]
    assert s.get_count("aft", "grain") == 4
    assert s.get_count("mid", "wool") == 1
    for expected in reversed(states[:-1]):
        s.undo()
        assert state(s) == expected
    with pytest.raises(CargoError):
        s.undo()
    assert s.get_holds() == []


def test_failed_calls_are_not_recorded(ship):
    ship.load("aft", "wool", 2)
    for call in (
        lambda: ship.unload("fore", "grain", 99),
        lambda: ship.unload("aft", "coal", 1),
        lambda: ship.shift_all("fore", "fore"),
        lambda: ship.shift_all("fore", "bow"),
        lambda: ship.seal_hold("mid", "mid"),
        lambda: ship.seal_hold("bow", "mid"),
        lambda: ship.add_hold("fore"),
        lambda: ship.load("bow", "grain", 1),
        lambda: ship.load("fore", "grain", 0),
    ):
        with pytest.raises((ValueError, KeyError, CargoError)):
            call()
    ship.undo()  # the load of the wool
    assert ship.get_cargo("aft") == []
    assert ship.get_count("fore", "grain") == 3


def test_get_calls_are_not_recorded(ship):
    ship.load("aft", "wool", 2)
    ship.get_count("aft", "wool")
    ship.get_cargo("aft")
    ship.get_holds()
    ship.undo()
    assert ship.get_cargo("aft") == []
    assert ship.get_count("mid", "coal") == 4


def test_there_is_no_redo():
    s = Ship()
    s.add_hold("fore")
    s.load("fore", "grain", 3)
    s.undo()
    s.undo()
    assert s.get_holds() == []
    with pytest.raises(CargoError):
        s.undo()


def test_new_calls_after_an_undo_are_undone_first(ship):
    ship.load("aft", "wool", 2)
    ship.undo()
    ship.load("aft", "iron", 1)
    ship.undo()
    assert ship.get_cargo("aft") == []
    ship.undo()  # the load of the coal in the fixture
    assert ship.get_cargo("mid") == []
    assert ship.get_cargo("fore") == ["grain", "steel"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    s = Ship()
    with pytest.raises(CargoError):
        s.undo()
    s.add_hold("fore")
    s.undo()
    with pytest.raises(CargoError):
        s.undo()
    assert s.get_holds() == []
    s.add_hold("fore")
    s.load("fore", "grain", 1)
    assert s.get_count("fore", "grain") == 1


def test_the_whole_fixture_can_be_undone(ship):
    for _ in range(6):
        ship.undo()
    assert ship.get_holds() == []
    with pytest.raises(CargoError):
        ship.undo()


def test_undo_restores_counts_that_a_later_call_checks(ship):
    ship.unload("fore", "grain", 3)
    ship.undo()
    assert ship.shift_all("fore", "aft") == 5
    with pytest.raises(NotEnoughCrates):
        ship.unload("fore", "grain", 1)
    assert ship.get_count("aft", "grain") == 3
