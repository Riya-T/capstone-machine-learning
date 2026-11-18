"""Hidden tests for the c_dangerous change (dangerous goods on open-air
decks only). Never shown to the writer or the editor.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_dangerous/private/test_ferry_dangerous_new.py
"""

import pytest
from ferry import Ferry, FerryError, NotAllowed

DECKS = ["upper", "lower", "hold"]


@pytest.fixture
def ferry():
    # upper and hold are open-air; the tanker in the middle of upper is dangerous.
    f = Ferry()
    f.add_deck("upper", open_air=True)
    f.add_deck("lower")
    f.add_deck("hold", open_air=True)
    f.board("van", "upper")
    f.board("tanker", "upper", dangerous=True)
    f.board("bus", "upper")
    f.board("bike", "lower")
    return f


def state(f, decks=DECKS):
    return [(d, f.get_vehicles(d)) for d in decks]


# --- the settings -----------------------------------------------------------------


def test_dangerous_vehicles_are_listed_in_deck_order(ferry):
    ferry.board("gas", "upper", dangerous=True)
    ferry.board("car", "upper")
    assert ferry.get_dangerous("upper") == ["tanker", "gas"]
    assert ferry.get_dangerous("lower") == []
    assert ferry.get_dangerous("hold") == []


def test_dangerous_list_of_a_deck_never_added_raises_key_error(ferry):
    with pytest.raises(KeyError):
        ferry.get_dangerous("attic")


def test_dangerous_defaults_to_false_and_closed_decks_take_other_vehicles(ferry):
    ferry.board("car", "lower")
    ferry.board("lorry", "hold")
    assert ferry.get_vehicles("lower") == ["bike", "car"]
    assert ferry.get_dangerous("hold") == []


def test_dangerous_error_is_a_ferry_error():
    assert issubclass(NotAllowed, FerryError)


# --- board ------------------------------------------------------------------------


def test_dangerous_vehicle_refused_by_a_closed_deck_changes_nothing(ferry):
    before = state(ferry)
    with pytest.raises(NotAllowed):
        ferry.board("gas", "lower", dangerous=True)
    assert state(ferry) == before
    ferry.board("gas", "hold", dangerous=True)
    assert ferry.get_dangerous("hold") == ["gas"]


def test_dangerous_flag_comes_from_the_latest_boarding(ferry):
    ferry.leave("tanker")
    ferry.board("tanker", "lower")
    assert ferry.get_dangerous("lower") == []
    ferry.leave("bike")
    ferry.board("bike", "upper", dangerous=True)
    assert ferry.get_dangerous("upper") == ["bike"]


def test_dangerous_flag_ends_when_a_deck_is_unloaded(ferry):
    ferry.unload_deck("upper")
    ferry.board("tanker", "lower")
    assert ferry.get_vehicles("lower") == ["bike", "tanker"]
    assert ferry.get_dangerous("lower") == []


# --- move_vehicle -----------------------------------------------------------------


def test_dangerous_vehicle_moves_to_another_open_air_deck(ferry):
    ferry.move_vehicle("tanker", "hold")
    assert ferry.get_dangerous("hold") == ["tanker"]
    assert ferry.get_dangerous("upper") == []
    assert ferry.get_vehicles("upper") == ["van", "bus"]


def test_dangerous_vehicle_may_not_move_to_a_closed_deck(ferry):
    before = state(ferry)
    with pytest.raises(NotAllowed):
        ferry.move_vehicle("tanker", "lower")
    assert state(ferry) == before
    assert ferry.get_deck_of("tanker") == "upper"


def test_dangerous_rule_lets_other_vehicles_move_anywhere(ferry):
    ferry.move_vehicle("van", "lower")
    ferry.move_vehicle("bike", "hold")
    assert state(ferry) == [("upper", ["tanker", "bus"]), ("lower", ["van"]), ("hold", ["bike"])]


# --- move_deck --------------------------------------------------------------------


def test_dangerous_vehicles_move_with_their_deck_to_an_open_air_deck(ferry):
    ferry.board("lorry", "hold")
    assert ferry.move_deck("upper", "hold") == 3
    assert ferry.get_vehicles("hold") == ["lorry", "van", "tanker", "bus"]
    assert ferry.get_dangerous("hold") == ["tanker"]


def test_dangerous_vehicle_stops_a_whole_move_deck_to_a_closed_deck(ferry):
    before = state(ferry)
    with pytest.raises(NotAllowed):
        ferry.move_deck("upper", "lower")
    assert state(ferry) == before
    assert ferry.get_deck_of("van") == "upper"
    assert ferry.get_vehicles("lower") == ["bike"]


def test_dangerous_rule_allows_move_deck_without_dangerous_vehicles(ferry):
    ferry.move_vehicle("tanker", "hold")
    assert ferry.move_deck("upper", "lower") == 2
    assert ferry.get_vehicles("lower") == ["bike", "van", "bus"]


def test_dangerous_refused_move_deck_works_once_the_vehicle_is_gone(ferry):
    with pytest.raises(NotAllowed):
        ferry.move_deck("upper", "lower")
    ferry.leave("tanker")
    assert ferry.move_deck("upper", "lower") == 2


def test_dangerous_rule_lets_an_empty_deck_move_anywhere(ferry):
    ferry.move_vehicle("bike", "upper")
    assert ferry.move_deck("lower", "hold") == 0


# --- leaving ----------------------------------------------------------------------


def test_dangerous_vehicles_can_always_leave(ferry):
    ferry.leave("tanker")
    assert ferry.get_dangerous("upper") == []
    ferry.board("gas", "hold", dangerous=True)
    assert ferry.unload_deck("hold") == ["gas"]
    assert ferry.get_dangerous("hold") == []
