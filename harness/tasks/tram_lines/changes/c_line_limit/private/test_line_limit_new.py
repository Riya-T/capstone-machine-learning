"""Hidden tests for the c_line_limit change (at most 6 stops per line).
Never shown to the writer or the editor.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest changes/c_line_limit/private/test_line_limit_new.py
"""

import pytest
from trams import LineFull, TramError, TramNetwork


@pytest.fixture
def network():
    # Line 4 is full; line 1 has 4 stops, two of them shared with line 4;
    # line 7 has 2 stops of its own.
    n = TramNetwork()
    for name in ["4", "1", "7"]:
        n.add_line(name)
    for stop in ["Central", "Park", "Museum", "Harbour", "Market", "Bridge"]:
        n.add_stop("4", stop)
    for stop in ["Station", "Park", "Central", "Castle"]:
        n.add_stop("1", stop)
    for stop in ["Zoo", "Beach"]:
        n.add_stop("7", stop)
    return n


def state(n):
    return [(line, n.get_stops(line)) for line in n.get_lines()]


# --- add_stop -------------------------------------------------------------------


def test_six_stops_fit_on_a_line():
    n = TramNetwork()
    n.add_line("1")
    for stop in ["A", "B", "C", "D", "E", "F"]:
        n.add_stop("1", stop)
    assert n.get_stops("1") == ["A", "B", "C", "D", "E", "F"]


def test_add_stop_on_a_full_line_is_refused_and_changes_nothing(network):
    before = state(network)
    with pytest.raises(LineFull):
        network.add_stop("4", "Airport")
    assert state(network) == before
    assert network.get_lines_through("Airport") == []


def test_line_full_is_a_tram_error():
    assert issubclass(LineFull, TramError)


def test_the_limit_is_per_line(network):
    network.add_stop("1", "Airport")
    network.add_stop("1", "Bridge")
    assert network.get_stops("1") == ["Station", "Park", "Central", "Castle", "Airport", "Bridge"]
    network.add_stop("7", "Airport")
    assert network.get_lines_through("Airport") == ["1", "7"]
    with pytest.raises(LineFull):
        network.add_stop("1", "Zoo")


def test_a_full_line_has_room_after_remove_stop(network):
    network.remove_stop("4", "Museum")
    network.add_stop("4", "Airport")
    assert network.get_stops("4") == ["Central", "Park", "Harbour", "Market", "Bridge", "Airport"]
    with pytest.raises(LineFull):
        network.add_stop("4", "Museum")


def test_a_full_line_has_room_after_close_stop(network):
    assert network.close_stop("Park") == 2
    network.add_stop("4", "Airport")
    assert network.get_stops("4") == ["Central", "Museum", "Harbour", "Market", "Bridge", "Airport"]


def test_close_stop_works_on_a_full_line(network):
    assert network.close_stop("Bridge") == 1
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour", "Market"]


# --- merge_lines ----------------------------------------------------------------


def test_a_merge_that_ends_at_exactly_six_stops_is_allowed(network):
    network.merge_lines("1", "7")
    assert network.get_stops("1") == ["Station", "Park", "Central", "Castle", "Zoo", "Beach"]
    assert network.get_lines() == ["4", "1"]


def test_a_merge_that_would_go_over_six_stops_changes_nothing(network):
    network.add_stop("7", "Airport")
    before = state(network)
    with pytest.raises(LineFull):
        network.merge_lines("1", "7")
    assert state(network) == before
    assert network.get_lines() == ["4", "1", "7"]
    assert network.get_stops("7") == ["Zoo", "Beach", "Airport"]


def test_only_stops_the_first_line_does_not_have_count(network):
    # Line 1 has 4 stops and line 4 has 6, but only 4 of line 4's stops
    # are new to line 1: 8 in all, too many.
    with pytest.raises(LineFull):
        network.merge_lines("1", "4")
    network.remove_stop("4", "Market")
    network.remove_stop("4", "Bridge")
    # Now only Museum and Harbour are new to line 1: 6 in all.
    network.merge_lines("1", "4")
    assert network.get_stops("1") == ["Station", "Park", "Central", "Castle", "Museum", "Harbour"]
    assert network.get_lines() == ["1", "7"]


def test_merging_into_a_full_line_a_line_it_already_covers(network):
    network.add_line("9")
    network.add_stop("9", "Harbour")
    network.add_stop("9", "Central")
    network.merge_lines("4", "9")
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour", "Market", "Bridge"]
    assert network.get_lines() == ["4", "1", "7"]


def test_a_merge_into_a_full_line_with_a_new_stop_is_refused(network):
    before = state(network)
    with pytest.raises(LineFull):
        network.merge_lines("4", "7")
    assert state(network) == before


def test_a_refused_merge_can_be_retried_once_there_is_room(network):
    network.add_stop("7", "Airport")
    with pytest.raises(LineFull):
        network.merge_lines("1", "7")
    network.remove_stop("1", "Castle")
    network.merge_lines("1", "7")
    assert network.get_stops("1") == ["Station", "Park", "Central", "Zoo", "Beach", "Airport"]
    assert network.get_lines() == ["4", "1"]


def test_a_line_filled_by_a_merge_refuses_more_stops(network):
    network.merge_lines("1", "7")
    with pytest.raises(LineFull):
        network.add_stop("1", "Airport")
    network.add_line("9")
    network.add_stop("9", "Airport")
    with pytest.raises(LineFull):
        network.merge_lines("1", "9")
    assert network.get_lines() == ["4", "1", "9"]
