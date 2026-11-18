"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from canals import CanalError, CanalNetwork


@pytest.fixture
def network():
    n = CanalNetwork()
    for name in ["upper", "middle", "lower"]:
        n.add_lock(name)
    return n


def test_undo_takes_back_the_last_connect(network):
    network.connect("upper", "middle")
    network.connect("lower", "middle")
    network.undo()
    assert network.get_channels("middle") == ["upper"]
    network.undo()
    assert network.get_channels("middle") == []


def test_undo_takes_back_a_disconnect(network):
    network.connect("middle", "upper")
    network.connect("middle", "lower")
    network.disconnect("middle", "upper")
    network.undo()
    assert network.get_channels("middle") == ["upper", "lower"]
    assert network.get_channels("upper") == ["middle"]


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(CanalError):
        CanalNetwork().undo()
