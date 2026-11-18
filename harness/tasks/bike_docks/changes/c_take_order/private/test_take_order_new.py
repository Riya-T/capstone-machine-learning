"""Hidden tests for the c_take_order change (configuration). Never shown to
the writer or the editor.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_take_order/private/test_take_order_new.py
"""

import pytest
from bikes import BikeNetwork, DockError


def make(**kwargs):
    n = BikeNetwork(**kwargs)
    for name in ["north", "south", "east"]:
        n.add_station(name)
    for bike in ["b1", "b2", "b3", "b4"]:
        n.dock("north", bike)
    n.dock("south", "b5")
    return n


def state(n):
    return [(s, n.get_bikes(s), n.get_take_order(s)) for s in n.get_stations()]


# --- settings ---------------------------------------------------------------


def test_every_station_starts_with_the_network_order():
    assert [make().get_take_order(s) for s in ["north", "south", "east"]] == ["oldest"] * 3
    n = make(take_order="newest")
    assert [n.get_take_order(s) for s in ["north", "south", "east"]] == ["newest"] * 3
    n.add_station("west")
    assert n.get_take_order("west") == "newest"


def test_the_network_order_can_be_given_as_oldest():
    n = make(take_order="oldest")
    n.rebalance("north", "east", 1)
    assert n.get_bikes("east") == ["b1"]


@pytest.mark.parametrize("order", ["first", "Oldest", None, ""])
def test_an_invalid_network_order_is_rejected(order):
    with pytest.raises(ValueError):
        BikeNetwork(take_order=order)


def test_set_take_order_changes_only_that_station():
    n = make()
    n.set_take_order("north", "newest")
    assert n.get_take_order("north") == "newest"
    assert n.get_take_order("south") == "oldest"
    n.set_take_order("north", "oldest")
    assert n.get_take_order("north") == "oldest"


@pytest.mark.parametrize("order", ["last", "NEWEST", None])
def test_an_invalid_station_order_is_rejected(order):
    n = make()
    n.set_take_order("north", "newest")
    with pytest.raises(ValueError):
        n.set_take_order("north", order)
    assert n.get_take_order("north") == "newest"


def test_stations_not_in_use_raise_key_error():
    n = make()
    n.close_station("east", "south")
    for name in ["east", "west"]:
        with pytest.raises(KeyError):
            n.get_take_order(name)
        with pytest.raises(KeyError):
            n.set_take_order(name, "newest")


def test_set_take_order_changes_no_bikes():
    n = make()
    before = [(s, n.get_bikes(s)) for s in n.get_stations()]
    n.set_take_order("north", "newest")
    assert [(s, n.get_bikes(s)) for s in n.get_stations()] == before


# --- rebalance --------------------------------------------------------------


def test_newest_takes_the_last_bikes_in_their_order():
    n = make()
    n.set_take_order("north", "newest")
    n.rebalance("north", "south", 3)
    assert n.get_bikes("north") == ["b1"]
    assert n.get_bikes("south") == ["b5", "b2", "b3", "b4"]
    assert n.get_station_of("b4") == "south"
    assert n.get_station_of("b1") == "north"


def test_newest_follows_the_order_bikes_arrived():
    n = make(take_order="newest")
    n.rebalance("south", "north", 1)  # b5 is now the newest at north
    n.rebalance("north", "east", 2)
    assert n.get_bikes("east") == ["b4", "b5"]
    assert n.get_bikes("north") == ["b1", "b2", "b3"]


def test_the_order_of_the_station_the_bikes_go_to_does_not_matter():
    n = make()
    n.set_take_order("south", "newest")
    n.rebalance("north", "south", 2)
    assert n.get_bikes("south") == ["b5", "b1", "b2"]
    n.rebalance("south", "east", 2)
    assert n.get_bikes("east") == ["b1", "b2"]
    assert n.get_bikes("south") == ["b5"]


def test_a_changed_order_applies_to_later_rebalances():
    n = make()
    n.rebalance("north", "east", 1)
    n.set_take_order("north", "newest")
    n.rebalance("north", "east", 1)
    n.set_take_order("north", "oldest")
    n.rebalance("north", "east", 1)
    assert n.get_bikes("east") == ["b1", "b4", "b2"]
    assert n.get_bikes("north") == ["b3"]


def test_newest_with_too_few_bikes_still_raises():
    n = make(take_order="newest")
    before = state(n)
    with pytest.raises(DockError):
        n.rebalance("north", "south", 5)
    with pytest.raises(ValueError):
        n.rebalance("north", "south", 0)
    with pytest.raises(ValueError):
        n.rebalance("north", "north", 1)
    assert state(n) == before


def test_newest_can_take_every_bike():
    n = make(take_order="newest")
    n.rebalance("north", "east", 4)
    assert n.get_bikes("east") == ["b1", "b2", "b3", "b4"]
    assert n.get_bikes("north") == []


# --- close_station ----------------------------------------------------------


def test_close_station_ignores_the_take_order():
    n = make(take_order="newest")
    n.dock("east", "b6")
    assert n.close_station("north", "east") == 4
    assert n.get_bikes("east") == ["b6", "b1", "b2", "b3", "b4"]
    assert n.get_stations() == ["south", "east"]
