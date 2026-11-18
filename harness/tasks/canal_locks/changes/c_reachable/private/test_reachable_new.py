"""Hidden tests for the c_reachable change (reachable locks). Never shown to
the writer or the editor.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reachable/private/test_reachable_new.py
"""

import pytest
from canals import CanalNetwork


@pytest.fixture
def network():
    n = CanalNetwork()
    for name in ["upper", "middle", "lower", "basin"]:
        n.add_lock(name)
    n.connect("upper", "middle")
    n.connect("middle", "lower")
    n.connect("basin", "middle")
    n.connect("lower", "upper")
    return n


def state(n):
    return [(lock, n.get_channels(lock)) for lock in n.get_locks()]


def test_direct_channels_come_first_in_their_order(network):
    assert network.get_reachable("middle") == ["upper", "lower", "basin"]


def test_locks_further_out_come_after(network):
    assert network.get_reachable("basin") == ["middle", "upper", "lower"]
    assert network.get_reachable("upper") == ["middle", "lower", "basin"]
    assert network.get_reachable("lower") == ["middle", "upper", "basin"]


def test_each_lock_is_listed_once_and_the_start_is_not_listed(network):
    reachable = network.get_reachable("upper")
    assert "upper" not in reachable
    assert len(reachable) == len(set(reachable)) == 3


def test_a_chain_is_followed_to_the_end():
    n = CanalNetwork()
    for name in ["a", "b", "c", "d", "e"]:
        n.add_lock(name)
    n.connect("d", "e")
    n.connect("c", "d")
    n.connect("b", "c")
    n.connect("a", "b")
    assert n.get_reachable("a") == ["b", "c", "d", "e"]
    assert n.get_reachable("e") == ["d", "c", "b", "a"]
    assert n.get_reachable("c") == ["d", "b", "e", "a"]


def test_each_level_follows_the_order_of_the_level_before():
    n = CanalNetwork()
    for name in ["hub", "x", "y", "x1", "x2", "y1"]:
        n.add_lock(name)
    n.connect("hub", "y")
    n.connect("hub", "x")
    n.connect("x", "x2")
    n.connect("y", "y1")
    n.connect("x", "x1")
    assert n.get_reachable("hub") == ["y", "x", "y1", "x2", "x1"]


def test_separate_parts_of_the_network_are_not_reached(network):
    network.add_lock("weir")
    network.add_lock("gate")
    network.connect("weir", "gate")
    assert network.get_reachable("weir") == ["gate"]
    assert "weir" not in network.get_reachable("middle")


def test_a_lock_with_no_channels_reaches_nothing(network):
    network.add_lock("weir")
    assert network.get_reachable("weir") == []


def test_reachable_follows_changes_to_the_network(network):
    network.disconnect("basin", "middle")
    assert network.get_reachable("basin") == []
    assert network.get_reachable("middle") == ["upper", "lower"]
    network.close_lock("middle")
    assert network.get_reachable("upper") == ["lower"]
    network.add_lock("weir")
    network.connect("weir", "basin")
    network.merge_locks("weir", "lower")
    assert network.get_reachable("upper") == ["lower", "basin"]


def test_locks_not_in_use_raise_key_error(network):
    with pytest.raises(KeyError):
        network.get_reachable("weir")
    network.close_lock("basin")
    with pytest.raises(KeyError):
        network.get_reachable("basin")


def test_get_reachable_changes_nothing(network):
    before = state(network)
    network.get_reachable("basin")
    network.get_reachable("upper")
    assert state(network) == before
