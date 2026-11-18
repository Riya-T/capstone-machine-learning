"""Hidden tests for the initial ferry_decks spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest private/test_ferry_initial.py
"""

import pytest
from ferry import Ferry, FerryError

DECKS = ["upper", "lower", "hold"]


@pytest.fixture
def ferry():
    f = Ferry()
    for name in DECKS:
        f.add_deck(name)
    for vehicle in ["van", "bus", "truck"]:
        f.board(vehicle, "upper")
    f.board("bike", "lower")
    return f


def state(f, decks=DECKS):
    """Every deck with its vehicles in order, to check that a failed call
    changed nothing."""
    return [(d, f.get_vehicles(d)) for d in decks]


# --- decks ----------------------------------------------------------------------


def test_a_new_deck_is_empty():
    f = Ferry()
    f.add_deck("upper")
    assert f.get_vehicles("upper") == []


def test_adding_a_deck_name_in_use_is_rejected(ferry):
    before = state(ferry)
    with pytest.raises(FerryError):
        ferry.add_deck("upper")
    assert state(ferry) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.board("car", "attic"),
        lambda f: f.move_vehicle("van", "attic"),
        lambda f: f.move_deck("attic", "upper"),
        lambda f: f.move_deck("upper", "attic"),
        lambda f: f.unload_deck("attic"),
        lambda f: f.get_vehicles("attic"),
    ],
)
def test_decks_that_were_never_added_raise_key_error(ferry, call):
    before = state(ferry)
    with pytest.raises(KeyError):
        call(ferry)
    assert state(ferry) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda f, v: f.leave(v),
        lambda f, v: f.move_vehicle(v, "hold"),
        lambda f, v: f.get_deck_of(v),
    ],
    ids=["leave", "move_vehicle", "get_deck_of"],
)
@pytest.mark.parametrize("vehicle", ["car", "bus", "bike"])
def test_vehicles_not_aboard_raise_key_error(ferry, call, vehicle):
    ferry.leave("bus")
    ferry.unload_deck("lower")  # the bike
    before = state(ferry)
    with pytest.raises(KeyError):
        call(ferry, vehicle)
    assert state(ferry) == before


# --- boarding and leaving -------------------------------------------------------


def test_board_puts_vehicles_after_those_already_there(ferry):
    ferry.board("camper", "upper")
    ferry.board("car", "hold")
    assert state(ferry) == [
        ("upper", ["van", "bus", "truck", "camper"]),
        ("lower", ["bike"]),
        ("hold", ["car"]),
    ]
    assert ferry.get_deck_of("camper") == "upper"
    assert ferry.get_deck_of("bike") == "lower"


@pytest.mark.parametrize("deck", ["upper", "hold"])
def test_boarding_a_vehicle_already_aboard_is_rejected(ferry, deck):
    before = state(ferry)
    with pytest.raises(FerryError):
        ferry.board("bus", deck)
    assert state(ferry) == before
    assert ferry.get_deck_of("bus") == "upper"


def test_leave_keeps_the_order_of_the_others(ferry):
    ferry.leave("van")
    ferry.leave("bike")
    assert state(ferry) == [("upper", ["bus", "truck"]), ("lower", []), ("hold", [])]


def test_a_vehicle_that_left_may_board_again_at_the_end(ferry):
    ferry.leave("van")
    ferry.board("van", "upper")
    assert ferry.get_vehicles("upper") == ["bus", "truck", "van"]
    ferry.leave("bike")
    ferry.board("bike", "hold")
    assert ferry.get_deck_of("bike") == "hold"


# --- moving one vehicle ---------------------------------------------------------


def test_move_vehicle_goes_to_the_end_of_the_deck(ferry):
    ferry.move_vehicle("bus", "lower")
    assert state(ferry) == [("upper", ["van", "truck"]), ("lower", ["bike", "bus"]), ("hold", [])]
    assert ferry.get_deck_of("bus") == "lower"


def test_a_moved_vehicle_can_move_back(ferry):
    ferry.move_vehicle("van", "hold")
    ferry.move_vehicle("van", "upper")
    assert ferry.get_vehicles("upper") == ["bus", "truck", "van"]
    assert ferry.get_vehicles("hold") == []


def test_moving_a_vehicle_to_its_own_deck_is_rejected(ferry):
    before = state(ferry)
    with pytest.raises(ValueError):
        ferry.move_vehicle("bus", "upper")
    assert state(ferry) == before


# --- moving a whole deck --------------------------------------------------------


def test_move_deck_puts_the_vehicles_after_those_already_there(ferry):
    assert ferry.move_deck("upper", "lower") == 3
    assert state(ferry) == [("upper", []), ("lower", ["bike", "van", "bus", "truck"]), ("hold", [])]


def test_move_deck_updates_where_each_vehicle_is(ferry):
    ferry.move_deck("upper", "hold")
    assert [ferry.get_deck_of(v) for v in ["van", "bus", "truck"]] == ["hold"] * 3
    ferry.move_vehicle("bus", "upper")
    assert ferry.get_vehicles("hold") == ["van", "truck"]
    ferry.leave("truck")
    assert ferry.get_vehicles("hold") == ["van"]


def test_a_deck_emptied_by_move_deck_is_still_in_use(ferry):
    ferry.move_deck("lower", "upper")
    ferry.board("car", "lower")
    assert ferry.get_vehicles("lower") == ["car"]
    assert ferry.get_vehicles("upper") == ["van", "bus", "truck", "bike"]


def test_move_deck_from_an_empty_deck_moves_nothing(ferry):
    before = state(ferry)
    assert ferry.move_deck("hold", "upper") == 0
    assert state(ferry) == before


@pytest.mark.parametrize("deck", ["upper", "hold"])
def test_move_deck_onto_the_same_deck_is_rejected(ferry, deck):
    before = state(ferry)
    with pytest.raises(ValueError):
        ferry.move_deck(deck, deck)
    assert state(ferry) == before


# --- unloading a deck -----------------------------------------------------------


def test_unload_deck_takes_its_vehicles_off_the_ferry(ferry):
    assert ferry.unload_deck("upper") == ["van", "bus", "truck"]
    assert state(ferry) == [("upper", []), ("lower", ["bike"]), ("hold", [])]
    for vehicle in ["van", "bus", "truck"]:
        with pytest.raises(KeyError):
            ferry.get_deck_of(vehicle)
    assert ferry.get_deck_of("bike") == "lower"


def test_unloading_an_empty_deck_returns_an_empty_list(ferry):
    before = state(ferry)
    assert ferry.unload_deck("hold") == []
    assert state(ferry) == before


def test_unloaded_vehicles_may_board_again(ferry):
    ferry.move_vehicle("van", "hold")
    ferry.unload_deck("upper")
    ferry.board("truck", "lower")
    ferry.board("bus", "upper")
    assert state(ferry) == [("upper", ["bus"]), ("lower", ["bike", "truck"]), ("hold", ["van"])]


# --- general --------------------------------------------------------------------


def test_ferries_do_not_share_decks():
    first, second = Ferry(), Ferry()
    first.add_deck("upper")
    first.board("van", "upper")
    second.add_deck("upper")
    assert second.get_vehicles("upper") == []
    second.board("van", "upper")
    assert first.get_vehicles("upper") == ["van"]
