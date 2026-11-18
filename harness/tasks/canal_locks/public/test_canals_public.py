"""Public checks for canals.py.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest public/test_canals_public.py
"""

import pytest
from canals import CanalError, CanalNetwork


@pytest.fixture
def network():
    n = CanalNetwork()
    for name in ["upper", "middle", "lower"]:
        n.add_lock(name)
    n.connect("upper", "middle")
    n.connect("lower", "middle")
    return n


def test_locks_and_channels_are_listed_in_the_order_added(network):
    assert network.get_locks() == ["upper", "middle", "lower"]
    assert network.get_channels("middle") == ["upper", "lower"]
    assert network.get_channels("lower") == ["middle"]


def test_adding_a_name_in_use_is_rejected(network):
    with pytest.raises(CanalError):
        network.add_lock("middle")
    assert network.get_locks() == ["upper", "middle", "lower"]


def test_a_new_channel_is_listed_last_on_both_sides(network):
    network.connect("upper", "lower")
    assert network.get_channels("upper") == ["middle", "lower"]
    assert network.get_channels("lower") == ["middle", "upper"]


def test_disconnect_keeps_the_order_of_the_other_channels(network):
    network.disconnect("middle", "upper")
    assert network.get_channels("middle") == ["lower"]
    assert network.get_channels("upper") == []


def test_close_lock_removes_the_lock_and_its_channels(network):
    assert network.close_lock("middle") == 2
    assert network.get_locks() == ["upper", "lower"]
    assert network.get_channels("upper") == []
    with pytest.raises(KeyError):
        network.get_channels("middle")


def test_merge_locks_lists_the_moved_channels_last(network):
    network.add_lock("weir")
    network.add_lock("basin")
    network.connect("lower", "basin")
    # middle: upper, lower; lower: middle, basin
    assert network.merge_locks("middle", "weir") == 2
    assert network.get_locks() == ["upper", "lower", "weir", "basin"]
    assert network.get_channels("weir") == ["upper", "lower"]
    assert network.get_channels("lower") == ["basin", "weir"]
    assert network.get_channels("upper") == ["weir"]
