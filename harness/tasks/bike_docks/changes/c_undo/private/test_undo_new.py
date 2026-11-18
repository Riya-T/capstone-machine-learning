"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from bikes import BikeNetwork, DockError


@pytest.fixture
def net():
    n = BikeNetwork()
    for name in ["north", "south", "east"]:
        n.add_station(name)
    for bike in ["b1", "b2", "b3", "b4"]:
        n.dock("north", bike)
    n.dock("south", "b5")
    n.dock("south", "b6")
    return n


def state(n):
    return [(s, n.get_bikes(s)) for s in n.get_stations()]


def where(n):
    return {b: n.get_station_of(b) for s in n.get_stations() for b in n.get_bikes(s)}


# --- each call can be undone ------------------------------------------------


def test_undo_of_a_dock_frees_the_bike(net):
    before = state(net)
    net.dock("east", "b7")
    net.undo()
    assert state(net) == before
    with pytest.raises(KeyError):
        net.get_station_of("b7")
    net.dock("south", "b7")
    assert net.get_bikes("south") == ["b5", "b6", "b7"]


def test_undo_of_an_undock_puts_the_bike_back_in_its_place(net):
    before = state(net)
    net.undock("b2")
    net.undo()
    assert state(net) == before
    assert net.get_bikes("north") == ["b1", "b2", "b3", "b4"]
    assert net.get_station_of("b2") == "north"


def test_undo_of_undocking_the_first_bike(net):
    net.undock("b5")
    net.undo()
    assert net.get_bikes("south") == ["b5", "b6"]
    with pytest.raises(DockError):
        net.dock("east", "b5")


def test_undo_of_a_rebalance_puts_the_bikes_back_at_the_front(net):
    before = state(net)
    net.rebalance("north", "south", 3)
    assert net.get_bikes("south") == ["b5", "b6", "b1", "b2", "b3"]
    net.undo()
    assert state(net) == before
    assert where(net)["b1"] == "north"
    assert where(net)["b6"] == "south"


def test_undo_of_a_rebalance_of_every_bike(net):
    before = state(net)
    net.rebalance("south", "east", 2)
    net.undo()
    assert state(net) == before
    assert net.get_bikes("east") == []


def test_undo_of_a_rebalance_after_the_station_got_more_bikes(net):
    net.rebalance("north", "east", 2)
    net.dock("north", "b7")
    net.undo()  # the dock
    net.undo()  # the rebalance
    assert net.get_bikes("north") == ["b1", "b2", "b3", "b4"]
    assert net.get_bikes("east") == []


def test_undo_of_close_station_brings_it_back_with_its_bikes(net):
    before, before_where = state(net), where(net)
    assert net.close_station("north", "east") == 4
    net.undo()
    assert state(net) == before
    assert where(net) == before_where
    assert net.get_stations() == ["north", "south", "east"]
    assert net.get_bikes("east") == []


def test_undo_of_close_station_keeps_its_place_in_the_list(net):
    net.add_station("west")
    net.dock("west", "b7")
    before = state(net)
    net.close_station("south", "west")
    assert net.get_stations() == ["north", "east", "west"]
    net.undo()
    assert net.get_stations() == ["north", "south", "east", "west"]
    assert net.get_bikes("west") == ["b7"]
    assert state(net) == before


def test_a_station_brought_back_is_in_use_again(net):
    net.close_station("south", "north")
    net.undo()
    net.dock("south", "b7")
    assert net.get_bikes("south") == ["b5", "b6", "b7"]
    with pytest.raises(DockError):
        net.add_station("south")
    assert net.close_station("south", "east") == 3
    assert net.get_stations() == ["north", "east"]


def test_closing_an_empty_station_can_be_undone(net):
    assert net.close_station("east", "south") == 0
    net.undo()
    assert net.get_stations() == ["north", "south", "east"]
    assert net.get_bikes("east") == []
    net.undo()  # the dock of b6
    assert net.get_bikes("south") == ["b5"]


def test_undo_of_add_station_removes_it_and_frees_the_name(net):
    net.add_station("west")
    net.undo()
    assert net.get_stations() == ["north", "south", "east"]
    with pytest.raises(KeyError):
        net.get_bikes("west")
    net.add_station("west")
    assert net.get_stations() == ["north", "south", "east", "west"]
    assert net.get_bikes("west") == []


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    n = BikeNetwork()
    calls = [
        lambda: n.add_station("north"),
        lambda: n.add_station("south"),
        lambda: n.dock("north", "b1"),
        lambda: n.dock("north", "b2"),
        lambda: n.dock("south", "b3"),
        lambda: n.add_station("east"),
        lambda: n.dock("north", "b4"),
        lambda: n.undock("b2"),
        lambda: n.rebalance("north", "south", 2),
        lambda: n.dock("east", "b2"),
        lambda: n.rebalance("south", "east", 1),
        lambda: n.close_station("south", "north"),
        lambda: n.add_station("west"),
        lambda: n.close_station("east", "west"),
        lambda: n.undock("b4"),
    ]
    states = [(state(n), where(n))]
    for call in calls:
        call()
        states.append((state(n), where(n)))
    assert n.get_stations() == ["north", "west"]
    assert n.get_bikes("north") == ["b1"]
    assert n.get_bikes("west") == ["b2", "b3"]
    for expected in reversed(states[:-1]):
        n.undo()
        assert (state(n), where(n)) == expected
    with pytest.raises(DockError):
        n.undo()
    assert n.get_stations() == []


def test_failed_calls_are_not_recorded(net):
    net.dock("east", "b7")
    for call in (
        lambda: net.add_station("north"),
        lambda: net.dock("west", "b8"),
        lambda: net.dock("north", "b5"),
        lambda: net.undock("b9"),
        lambda: net.rebalance("north", "south", 9),
        lambda: net.rebalance("north", "south", 0),
        lambda: net.rebalance("north", "north", 1),
        lambda: net.close_station("north", "north"),
        lambda: net.close_station("west", "north"),
    ):
        with pytest.raises((ValueError, KeyError, DockError)):
            call()
    net.undo()  # the dock of b7
    assert net.get_bikes("east") == []
    assert net.get_bikes("south") == ["b5", "b6"]


def test_get_calls_are_not_recorded(net):
    net.dock("east", "b7")
    net.get_bikes("east")
    net.get_station_of("b7")
    net.get_stations()
    net.undo()
    assert net.get_bikes("east") == []
    assert net.get_bikes("south") == ["b5", "b6"]


def test_there_is_no_redo():
    n = BikeNetwork()
    n.add_station("north")
    n.dock("north", "b1")
    n.undo()
    n.undo()
    assert n.get_stations() == []
    with pytest.raises(DockError):
        n.undo()


def test_new_calls_after_an_undo_are_undone_first(net):
    net.undock("b1")
    net.undo()
    net.rebalance("north", "east", 1)
    net.undo()
    assert net.get_bikes("north") == ["b1", "b2", "b3", "b4"]
    assert net.get_bikes("east") == []
    net.undo()  # the dock of b6 in the fixture
    assert net.get_bikes("south") == ["b5"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    n = BikeNetwork()
    with pytest.raises(DockError):
        n.undo()
    n.add_station("north")
    n.undo()
    with pytest.raises(DockError):
        n.undo()
    assert n.get_stations() == []
    n.add_station("north")
    n.dock("north", "b1")
    assert n.get_bikes("north") == ["b1"]


def test_the_whole_fixture_can_be_undone(net):
    for _ in range(9):
        net.undo()
    assert net.get_stations() == []
    with pytest.raises(DockError):
        net.undo()


def test_undo_restores_bikes_that_a_later_call_checks(net):
    net.rebalance("north", "south", 4)
    net.undo()
    net.rebalance("north", "east", 4)
    assert net.get_bikes("east") == ["b1", "b2", "b3", "b4"]
    with pytest.raises(DockError):
        net.rebalance("north", "south", 1)
    net.undock("b6")
    net.undo()
    with pytest.raises(DockError):
        net.dock("east", "b6")
