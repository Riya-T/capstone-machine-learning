"""Public checks for the c_line_limit change (at most 6 stops per line).
Shown to the editor, never to the writer.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest changes/c_line_limit/public/test_line_limit_public.py
"""

import pytest
from trams import LineFull, TramNetwork

SIX = ["A", "B", "C", "D", "E", "F"]


@pytest.fixture
def network():
    n = TramNetwork()
    n.add_line("1")
    n.add_line("2")
    return n


def test_a_seventh_stop_is_refused(network):
    for stop in SIX:
        network.add_stop("1", stop)
    with pytest.raises(LineFull):
        network.add_stop("1", "G")
    assert network.get_stops("1") == SIX


def test_a_merge_that_would_make_a_line_too_long_is_refused(network):
    for stop in ["A", "B", "C", "D"]:
        network.add_stop("1", stop)
    for stop in ["E", "F", "G"]:
        network.add_stop("2", stop)
    with pytest.raises(LineFull):
        network.merge_lines("1", "2")
    assert network.get_stops("1") == ["A", "B", "C", "D"]
    assert network.get_stops("2") == ["E", "F", "G"]
    assert network.get_lines() == ["1", "2"]
