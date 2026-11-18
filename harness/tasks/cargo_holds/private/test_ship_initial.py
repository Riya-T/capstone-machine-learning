"""Hidden tests for the initial cargo_holds spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest private/test_ship_initial.py
"""

import pytest
from ship import CargoError, NotEnoughCrates, Ship


@pytest.fixture
def ship():
    s = Ship()
    for name in ["fore", "mid", "aft"]:
        s.add_hold(name)
    s.load("fore", "grain", 5)
    s.load("fore", "steel", 2)
    return s


def state(s):
    """Every hold in order with its cargo and counts, to check that a failed
    call changed nothing."""
    return [(h, [(c, s.get_count(h, c)) for c in s.get_cargo(h)]) for h in s.get_holds()]


# --- holds --------------------------------------------------------------------


def test_a_new_hold_is_empty():
    s = Ship()
    s.add_hold("fore")
    assert s.get_cargo("fore") == []
    assert s.get_count("fore", "grain") == 0


def test_holds_are_listed_in_the_order_added():
    s = Ship()
    for name in ["mid", "fore", "aft"]:
        s.add_hold(name)
    assert s.get_holds() == ["mid", "fore", "aft"]


def test_a_new_ship_has_no_holds():
    assert Ship().get_holds() == []


def test_adding_a_name_in_use_is_rejected(ship):
    before = state(ship)
    with pytest.raises(CargoError):
        ship.add_hold("fore")
    assert state(ship) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.load("bow", "grain", 1),
        lambda s: s.unload("bow", "grain", 1),
        lambda s: s.shift_all("bow", "mid"),
        lambda s: s.shift_all("fore", "bow"),
        lambda s: s.seal_hold("bow", "mid"),
        lambda s: s.seal_hold("fore", "bow"),
        lambda s: s.get_count("bow", "grain"),
        lambda s: s.get_cargo("bow"),
    ],
)
def test_holds_that_were_never_added_raise_key_error(ship, call):
    before = state(ship)
    with pytest.raises(KeyError):
        call(ship)
    assert state(ship) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.load("aft", "grain", 1),
        lambda s: s.unload("aft", "grain", 1),
        lambda s: s.shift_all("aft", "fore"),
        lambda s: s.shift_all("fore", "aft"),
        lambda s: s.seal_hold("aft", "fore"),
        lambda s: s.seal_hold("fore", "aft"),
        lambda s: s.get_count("aft", "grain"),
        lambda s: s.get_cargo("aft"),
    ],
)
def test_a_sealed_hold_is_not_in_use(ship, call):
    ship.load("aft", "wool", 1)
    ship.seal_hold("aft", "mid")
    before = state(ship)
    with pytest.raises(KeyError):
        call(ship)
    assert state(ship) == before


# --- loading and unloading ----------------------------------------------------


def test_loading_and_unloading_change_the_count(ship):
    ship.load("fore", "grain", 3)
    ship.unload("fore", "grain", 6)
    ship.load("mid", "grain", 1)
    assert ship.get_count("fore", "grain") == 2
    assert ship.get_count("mid", "grain") == 1
    assert ship.get_count("fore", "steel") == 2


def test_every_crate_of_a_cargo_type_can_be_unloaded(ship):
    ship.unload("fore", "steel", 2)
    assert ship.get_count("fore", "steel") == 0
    assert ship.get_cargo("fore") == ["grain"]


def test_cargo_is_listed_in_alphabetical_order(ship):
    ship.load("mid", "wool", 1)
    ship.load("mid", "coal", 2)
    ship.load("mid", "iron", 3)
    assert ship.get_cargo("mid") == ["coal", "iron", "wool"]


def test_unloading_more_than_there_are_raises_and_changes_nothing(ship):
    before = state(ship)
    with pytest.raises(NotEnoughCrates):
        ship.unload("fore", "steel", 3)
    with pytest.raises(NotEnoughCrates):
        ship.unload("fore", "coal", 1)
    with pytest.raises(NotEnoughCrates):
        ship.unload("mid", "grain", 1)
    assert state(ship) == before


@pytest.mark.parametrize("count", [0, -3])
def test_loading_a_count_of_0_or_less_is_rejected(ship, count):
    before = state(ship)
    with pytest.raises(ValueError):
        ship.load("fore", "grain", count)
    assert state(ship) == before


# --- shifting and sealing -----------------------------------------------------


def test_shift_all_moves_every_cargo_type(ship):
    ship.load("mid", "grain", 1)
    ship.load("mid", "coal", 4)
    assert ship.shift_all("fore", "mid") == 7
    assert ship.get_cargo("fore") == []
    assert ship.get_cargo("mid") == ["coal", "grain", "steel"]
    assert ship.get_count("mid", "grain") == 6
    assert ship.get_count("mid", "steel") == 2
    assert ship.get_holds() == ["fore", "mid", "aft"]


def test_a_hold_emptied_by_shift_all_can_be_loaded_again(ship):
    ship.shift_all("fore", "aft")
    ship.load("fore", "coal", 3)
    assert ship.get_cargo("fore") == ["coal"]
    assert ship.get_count("aft", "grain") == 5


def test_shift_all_from_an_empty_hold_moves_nothing(ship):
    before = state(ship)
    assert ship.shift_all("aft", "fore") == 0
    assert state(ship) == before


def test_seal_hold_moves_every_crate_and_removes_the_hold(ship):
    ship.load("aft", "grain", 2)
    assert ship.seal_hold("fore", "aft") == 7
    assert ship.get_holds() == ["mid", "aft"]
    assert ship.get_count("aft", "grain") == 7
    assert ship.get_count("aft", "steel") == 2


def test_sealing_into_an_empty_hold(ship):
    assert ship.seal_hold("fore", "mid") == 7
    assert ship.get_holds() == ["mid", "aft"]
    assert ship.get_cargo("mid") == ["grain", "steel"]


def test_the_other_holds_keep_their_order_after_a_seal(ship):
    ship.add_hold("bow")
    ship.load("mid", "coal", 1)
    ship.seal_hold("mid", "bow")
    assert ship.get_holds() == ["fore", "aft", "bow"]
    assert ship.get_count("bow", "coal") == 1


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.shift_all("fore", "fore"),
        lambda s: s.seal_hold("fore", "fore"),
        lambda s: s.shift_all("aft", "aft"),
    ],
    ids=["shift_all", "seal_hold", "shift_all_empty"],
)
def test_the_same_hold_on_both_sides_is_rejected(ship, call):
    before = state(ship)
    with pytest.raises(ValueError):
        call(ship)
    assert state(ship) == before


# --- general ------------------------------------------------------------------


def test_not_enough_crates_is_a_cargo_error():
    assert issubclass(NotEnoughCrates, CargoError)


def test_ships_do_not_share_holds():
    first, second = Ship(), Ship()
    first.add_hold("fore")
    first.load("fore", "grain", 3)
    assert second.get_holds() == []
    second.add_hold("fore")
    assert second.get_count("fore", "grain") == 0
