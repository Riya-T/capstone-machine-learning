"""Public checks for the c_reachable change (reachable locks). Shown to the
editor, never to the writer.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reachable/public/test_reachable_public.py
"""

import pytest
from canals import CanalNetwork


@pytest.fixture
def network():
    n = CanalNetwork()
    for name in ["upper", "middle", "lower", "weir"]:
        n.add_lock(name)
    n.connect("upper", "middle")
    n.connect("middle", "lower")
    return n


def test_reachable_locks_nearest_first(network):
    assert network.get_reachable("upper") == ["middle", "lower"]
    assert network.get_reachable("middle") == ["upper", "lower"]


def test_a_lock_with_no_channels_reaches_nothing(network):
    assert network.get_reachable("weir") == []
