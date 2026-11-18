"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_ferry_undo_new.py
"""

import pytest
from ferry import Ferry, FerryError

ALL_DECKS = ["upper", "lower", "hold", "car_deck"]


@pytest.fixture
def ferry():
    f = Ferry()
    for name in ["upper", "lower", "hold"]:
        f.add_deck(name)
    for vehicle in ["van", "bus", "truck"]:
        f.board(vehicle, "upper")
    f.board("bike", "lower")
    return f


def state(f, decks=ALL_DECKS):
    """Every deck in use with its vehicles in order, and where each of them
    is reported to be."""
    out = []
    for deck in decks:
        try:
            vehicles = f.get_vehicles(deck)
        except KeyError:
            continue
        out.append((deck, [(v, f.get_deck_of(v)) for v in vehicles]))
    return out


# --- each call can be undone ------------------------------------------------


def test_undo_of_board_takes_the_vehicle_off_and_frees_the_name(ferry):
    before = state(ferry)
    ferry.board("car", "hold")
    ferry.undo()
    assert state(ferry) == before
    with pytest.raises(KeyError):
        ferry.get_deck_of("car")
    ferry.board("car", "lower")
    assert ferry.get_vehicles("lower") == ["bike", "car"]


@pytest.mark.parametrize("vehicle", ["van", "bus", "truck"])
def test_undo_of_leave_puts_the_vehicle_back_in_its_place(ferry, vehicle):
    before = state(ferry)
    ferry.leave(vehicle)
    ferry.undo()
    assert state(ferry) == before
    assert ferry.get_vehicles("upper") == ["van", "bus", "truck"]


def test_undo_of_move_vehicle_puts_it_back_in_its_old_place(ferry):
    before = state(ferry)
    ferry.move_vehicle("bus", "lower")
    ferry.undo()
    assert state(ferry) == before
    assert ferry.get_deck_of("bus") == "upper"
    assert ferry.get_vehicles("lower") == ["bike"]


def test_undo_of_move_deck_restores_both_decks_at_once(ferry):
    before = state(ferry)
    assert ferry.move_deck("upper", "lower") == 3
    ferry.undo()
    assert state(ferry) == before


def test_undo_of_move_deck_into_an_empty_deck(ferry):
    before = state(ferry)
    ferry.move_deck("upper", "hold")
    ferry.undo()
    assert state(ferry) == before
    assert ferry.get_vehicles("hold") == []


def test_undo_of_unload_deck_brings_every_vehicle_back(ferry):
    before = state(ferry)
    assert ferry.unload_deck("upper") == ["van", "bus", "truck"]
    ferry.undo()
    assert state(ferry) == before
    with pytest.raises(FerryError):
        ferry.board("bus", "hold")
    ferry.leave("bus")
    assert ferry.get_vehicles("upper") == ["van", "truck"]


def test_undo_of_unload_deck_after_a_name_boarded_again(ferry):
    ferry.unload_deck("upper")
    ferry.board("van", "hold")  # a new van, on another deck
    ferry.undo()  # the new van
    assert ferry.get_vehicles("hold") == []
    ferry.undo()  # the unload
    assert ferry.get_vehicles("upper") == ["van", "bus", "truck"]
    assert ferry.get_deck_of("van") == "upper"


def test_undo_of_add_deck_removes_it_and_frees_the_name(ferry):
    ferry.add_deck("car_deck")
    ferry.undo()
    with pytest.raises(KeyError):
        ferry.get_vehicles("car_deck")
    ferry.add_deck("car_deck")
    assert ferry.get_vehicles("car_deck") == []


def test_undo_of_a_vehicle_that_left_and_boarded_again(ferry):
    ferry.leave("van")
    ferry.board("van", "hold")
    ferry.undo()
    with pytest.raises(KeyError):
        ferry.get_deck_of("van")
    ferry.undo()
    assert ferry.get_vehicles("upper") == ["van", "bus", "truck"]
    assert ferry.get_vehicles("hold") == []


# --- calls that move nothing ------------------------------------------------


def test_undo_of_a_move_deck_that_moved_nothing(ferry):
    assert ferry.move_deck("hold", "upper") == 0
    ferry.undo()  # the move_deck, which changed nothing
    assert ferry.get_vehicles("lower") == ["bike"]
    ferry.undo()  # the bike
    assert ferry.get_vehicles("lower") == []
    assert ferry.get_vehicles("upper") == ["van", "bus", "truck"]


def test_undo_of_unloading_an_empty_deck(ferry):
    assert ferry.unload_deck("hold") == []
    ferry.undo()  # the unload, which changed nothing
    assert ferry.get_vehicles("lower") == ["bike"]
    ferry.undo()  # the bike
    assert ferry.get_vehicles("lower") == []


# --- what is and is not recorded --------------------------------------------


def test_undo_steps_back_one_call_at_a_time():
    f = Ferry()
    calls = [
        lambda: f.add_deck("upper"),
        lambda: f.add_deck("lower"),
        lambda: f.board("van", "upper"),
        lambda: f.board("bus", "upper"),
        lambda: f.board("bike", "lower"),
        lambda: f.add_deck("hold"),
        lambda: f.board("truck", "upper"),
        lambda: f.move_vehicle("bus", "lower"),
        lambda: f.leave("van"),
        lambda: f.move_deck("lower", "upper"),
        lambda: f.board("van", "lower"),
        lambda: f.unload_deck("upper"),
        lambda: f.board("bus", "hold"),
        lambda: f.move_deck("hold", "lower"),
        lambda: f.move_vehicle("van", "hold"),
    ]
    states = [state(f)]
    for call in calls:
        call()
        states.append(state(f))
    assert states[-1] == [
        ("upper", []),
        ("lower", [("bus", "lower")]),
        ("hold", [("van", "hold")]),
    ]
    for expected in reversed(states[:-1]):
        f.undo()
        assert state(f) == expected
    with pytest.raises(FerryError):
        f.undo()
    assert state(f) == []


def test_undo_skips_calls_that_raised(ferry):
    ferry.board("car", "hold")
    for call in (
        lambda: ferry.add_deck("upper"),
        lambda: ferry.board("van", "lower"),
        lambda: ferry.board("camper", "attic"),
        lambda: ferry.leave("camper"),
        lambda: ferry.move_vehicle("van", "upper"),
        lambda: ferry.move_vehicle("van", "attic"),
        lambda: ferry.move_deck("upper", "upper"),
        lambda: ferry.move_deck("upper", "attic"),
        lambda: ferry.unload_deck("attic"),
    ):
        with pytest.raises((ValueError, KeyError, FerryError)):
            call()
    ferry.undo()  # the car
    assert ferry.get_vehicles("hold") == []
    assert ferry.get_vehicles("upper") == ["van", "bus", "truck"]


def test_undo_ignores_get_calls(ferry):
    ferry.board("car", "hold")
    ferry.get_vehicles("hold")
    ferry.get_deck_of("car")
    ferry.undo()
    assert ferry.get_vehicles("hold") == []
    assert ferry.get_vehicles("lower") == ["bike"]


def test_undo_has_no_redo():
    f = Ferry()
    f.add_deck("upper")
    f.board("van", "upper")
    f.undo()
    f.undo()
    assert state(f) == []
    with pytest.raises(FerryError):
        f.undo()


def test_undo_after_new_calls_takes_back_the_new_calls_first(ferry):
    ferry.board("car", "hold")
    ferry.undo()
    ferry.board("camper", "hold")
    ferry.undo()
    assert ferry.get_vehicles("hold") == []
    ferry.undo()  # the bike boarded by the fixture
    assert ferry.get_vehicles("lower") == []
    assert ferry.get_vehicles("upper") == ["van", "bus", "truck"]


def test_undo_with_nothing_left_raises_and_changes_nothing():
    f = Ferry()
    with pytest.raises(FerryError):
        f.undo()
    f.add_deck("upper")
    f.undo()
    with pytest.raises(FerryError):
        f.undo()
    assert state(f) == []
    f.add_deck("upper")
    f.board("van", "upper")
    assert f.get_vehicles("upper") == ["van"]


def test_undo_of_the_whole_fixture(ferry):
    for _ in range(7):
        ferry.undo()
    assert state(ferry) == []
    with pytest.raises(FerryError):
        ferry.undo()


def test_undo_restores_vehicles_that_later_calls_use(ferry):
    ferry.move_deck("upper", "hold")
    ferry.undo()
    ferry.move_vehicle("truck", "lower")
    assert ferry.get_vehicles("lower") == ["bike", "truck"]
    assert ferry.unload_deck("upper") == ["van", "bus"]
    assert ferry.get_vehicles("hold") == []
