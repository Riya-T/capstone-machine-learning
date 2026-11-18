"""Public checks for the c_take_order change (configuration). Shown to the
editor, never to the writer.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_take_order/public/test_take_order_public.py
"""

from bikes import BikeNetwork


def make(**kwargs):
    n = BikeNetwork(**kwargs)
    n.add_station("north")
    n.add_station("south")
    for bike in ["b1", "b2", "b3"]:
        n.dock("north", bike)
    return n


def test_stations_take_the_oldest_bikes_by_default():
    n = make()
    assert n.get_take_order("north") == "oldest"
    n.rebalance("north", "south", 2)
    assert n.get_bikes("south") == ["b1", "b2"]


def test_a_station_set_to_newest_gives_its_last_bikes():
    n = make()
    n.set_take_order("north", "newest")
    n.rebalance("north", "south", 2)
    assert n.get_bikes("north") == ["b1"]
    assert n.get_bikes("south") == ["b2", "b3"]


def test_the_network_sets_the_order_of_new_stations():
    n = make(take_order="newest")
    assert n.get_take_order("south") == "newest"
