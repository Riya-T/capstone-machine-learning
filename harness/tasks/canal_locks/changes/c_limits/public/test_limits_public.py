"""Public checks for the c_limits change (channel limits). Shown to the
editor, never to the writer.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limits/public/test_limits_public.py
"""

import pytest
from canals import CanalNetwork, TooManyChannels


@pytest.fixture
def network():
    n = CanalNetwork()
    for name in ["upper", "middle", "lower"]:
        n.add_lock(name)
    return n


def test_locks_start_without_a_limit(network):
    assert network.get_max_channels("upper") is None
    network.set_max_channels("upper", 2)
    assert network.get_max_channels("upper") == 2


def test_connect_stops_at_the_limit(network):
    network.set_max_channels("middle", 1)
    network.connect("middle", "upper")
    with pytest.raises(TooManyChannels):
        network.connect("lower", "middle")
    assert network.get_channels("middle") == ["upper"]
    assert network.get_channels("lower") == []


def test_an_invalid_limit_is_rejected(network):
    with pytest.raises(ValueError):
        network.set_max_channels("upper", 0)
    assert network.get_max_channels("upper") is None
