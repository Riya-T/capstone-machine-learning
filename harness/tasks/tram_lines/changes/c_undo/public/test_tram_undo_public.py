"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_tram_undo_public.py
"""

import pytest
from trams import TramError, TramNetwork


@pytest.fixture
def network():
    n = TramNetwork()
    n.add_line("1")
    n.add_line("2")
    return n


def test_undo_takes_back_the_last_stop_added(network):
    network.add_stop("1", "Central")
    network.add_stop("1", "Park")
    network.undo()
    assert network.get_stops("1") == ["Central"]
    network.undo()
    assert network.get_stops("1") == []


def test_undo_takes_back_the_removal_of_the_last_stop(network):
    network.add_stop("1", "Central")
    network.add_stop("1", "Park")
    network.remove_stop("1", "Park")
    network.undo()
    assert network.get_stops("1") == ["Central", "Park"]


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(TramError):
        TramNetwork().undo()
