"""Hidden tests for the c_rebalance_many change (atomic operation). Never
shown to the writer or the editor.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_rebalance_many/private/test_rebalance_many_new.py
"""

import pytest
from bikes import BikeNetwork, DockError


@pytest.fixture
def net():
    n = BikeNetwork()
    for name in ["north", "south", "east", "west"]:
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


# --- moves that succeed -----------------------------------------------------


def test_a_single_move_is_like_rebalance(net):
    assert net.rebalance_many([("north", "south", 2)]) == 2
    assert net.get_bikes("north") == ["b3", "b4"]
    assert net.get_bikes("south") == ["b5", "b6", "b1", "b2"]
    assert net.get_station_of("b1") == "south"


def test_moves_from_several_stations(net):
    assert net.rebalance_many([("north", "east", 1), ("south", "east", 2), ("north", "west", 3)]) == 6
    assert state(net) == [
        ("north", []),
        ("south", []),
        ("east", ["b1", "b5", "b6"]),
        ("west", ["b2", "b3", "b4"]),
    ]
    assert where(net)["b6"] == "east"
    assert where(net)["b4"] == "west"


def test_a_later_move_sees_the_bikes_an_earlier_one_moved(net):
    # The two bikes moved to east are then moved on from east to west.
    assert net.rebalance_many([("north", "east", 2), ("east", "west", 2)]) == 4
    assert net.get_bikes("east") == []
    assert net.get_bikes("west") == ["b1", "b2"]
    assert net.get_station_of("b2") == "west"


def test_a_later_move_takes_the_new_first_bikes(net):
    assert net.rebalance_many([("south", "north", 1), ("north", "east", 4), ("north", "west", 1)]) == 6
    assert net.get_bikes("east") == ["b1", "b2", "b3", "b4"]
    assert net.get_bikes("west") == ["b5"]
    assert net.get_bikes("north") == []


def test_bikes_can_go_back_and_forth(net):
    assert net.rebalance_many([("north", "south", 1), ("south", "north", 3)]) == 4
    assert net.get_bikes("north") == ["b2", "b3", "b4", "b5", "b6", "b1"]
    assert net.get_bikes("south") == []


def test_the_moves_count_every_time_a_bike_moves(net):
    moves = [("north", "east", 1), ("east", "west", 1), ("west", "east", 1)]
    assert net.rebalance_many(moves) == 3
    assert net.get_bikes("east") == ["b1"]


# --- moves that fail --------------------------------------------------------


def test_too_few_bikes_in_the_last_move_changes_nothing(net):
    before, before_where = state(net), where(net)
    with pytest.raises(DockError):
        net.rebalance_many([("north", "east", 2), ("south", "west", 1), ("north", "west", 3)])
    assert state(net) == before
    assert where(net) == before_where


def test_too_few_bikes_counts_the_earlier_moves(net):
    # south only has 2 bikes, but the first move brings it a third.
    assert net.rebalance_many([("north", "south", 1), ("south", "east", 3)]) == 4
    before = state(net)
    # east has 3 bikes, and the first move takes 2 of them away.
    with pytest.raises(DockError):
        net.rebalance_many([("east", "west", 2), ("east", "north", 2)])
    assert state(net) == before


def test_a_station_not_in_use_changes_nothing(net):
    before = state(net)
    with pytest.raises(KeyError):
        net.rebalance_many([("north", "east", 1), ("east", "nowhere", 1)])
    with pytest.raises(KeyError):
        net.rebalance_many([("north", "east", 1), ("nowhere", "east", 1)])
    assert state(net) == before


def test_a_bad_count_changes_nothing(net):
    before = state(net)
    with pytest.raises(ValueError):
        net.rebalance_many([("north", "east", 1), ("north", "west", 0)])
    with pytest.raises(ValueError):
        net.rebalance_many([("south", "east", 1), ("north", "west", -1)])
    assert state(net) == before


def test_the_same_station_on_both_sides_changes_nothing(net):
    before = state(net)
    with pytest.raises(ValueError):
        net.rebalance_many([("north", "east", 1), ("south", "south", 1)])
    assert state(net) == before


def test_the_network_works_normally_after_a_failed_job(net):
    with pytest.raises(DockError):
        net.rebalance_many([("north", "east", 4), ("north", "west", 1)])
    net.rebalance("north", "west", 1)
    net.dock("east", "b7")
    assert net.get_bikes("west") == ["b1"]
    assert net.get_bikes("east") == ["b7"]
    assert net.get_bikes("north") == ["b2", "b3", "b4"]
    with pytest.raises(DockError):
        net.dock("west", "b4")
