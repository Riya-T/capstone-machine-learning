"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_tram_undo_new.py
"""

import pytest
from trams import TramError, TramNetwork


@pytest.fixture
def network():
    n = TramNetwork()
    for name in ["4", "1", "7"]:
        n.add_line(name)
    for stop in ["Central", "Park", "Museum", "Harbour"]:
        n.add_stop("4", stop)
    for stop in ["Station", "Park", "Central"]:
        n.add_stop("1", stop)
    n.add_stop("7", "Zoo")
    return n


def state(n):
    return [(line, n.get_stops(line)) for line in n.get_lines()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_add_stop(network):
    before = state(network)
    network.add_stop("7", "Beach")
    network.undo()
    assert state(network) == before


@pytest.mark.parametrize("stop", ["Central", "Park", "Museum", "Harbour"])
def test_undo_of_remove_stop_puts_it_back_in_its_place(network, stop):
    before = state(network)
    network.remove_stop("4", stop)
    network.undo()
    assert state(network) == before
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour"]


def test_undo_of_close_stop_puts_it_back_on_every_line_in_one_go(network):
    before = state(network)
    assert network.close_stop("Park") == 2
    network.undo()
    assert state(network) == before
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour"]
    assert network.get_stops("1") == ["Station", "Park", "Central"]
    assert network.get_lines_through("Park") == ["4", "1"]


def test_undo_of_close_stop_at_different_places_on_each_line(network):
    before = state(network)
    assert network.close_stop("Central") == 2  # first on 4, last on 1
    network.undo()
    assert state(network) == before


def test_undo_of_close_stop_that_emptied_a_line(network):
    before = state(network)
    network.close_stop("Zoo")
    assert network.get_stops("7") == []
    network.undo()
    assert state(network) == before


def test_undo_of_merge_lines_brings_the_second_line_back_in_its_place(network):
    before = state(network)
    network.merge_lines("7", "1")
    assert network.get_lines() == ["4", "7"]
    network.undo()
    assert state(network) == before
    assert network.get_lines() == ["4", "1", "7"]
    assert network.get_stops("7") == ["Zoo"]


def test_undo_of_merge_lines_with_shared_stops(network):
    before = state(network)
    network.merge_lines("4", "1")
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour", "Station"]
    network.undo()
    assert state(network) == before
    assert network.get_lines_through("Central") == ["4", "1"]


def test_a_line_brought_back_is_in_use_again(network):
    network.merge_lines("4", "1")
    network.undo()
    network.add_stop("1", "Airport")
    assert network.get_stops("1") == ["Station", "Park", "Central", "Airport"]
    with pytest.raises(TramError):
        network.add_line("1")
    network.merge_lines("7", "1")
    assert network.get_stops("7") == ["Zoo", "Station", "Park", "Central", "Airport"]


def test_undo_of_add_line_removes_it_and_frees_the_name(network):
    network.add_line("9")
    network.undo()
    assert network.get_lines() == ["4", "1", "7"]
    with pytest.raises(KeyError):
        network.get_stops("9")
    network.add_line("9")
    assert network.get_lines() == ["4", "1", "7", "9"]
    assert network.get_stops("9") == []


def test_undo_of_a_stop_closed_and_then_added_again(network):
    network.close_stop("Park")
    network.add_stop("1", "Park")
    assert network.get_stops("1") == ["Station", "Central", "Park"]
    network.undo()  # the add_stop
    assert network.get_lines_through("Park") == []
    network.undo()  # the close_stop
    assert network.get_stops("1") == ["Station", "Park", "Central"]
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour"]


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    n = TramNetwork()
    calls = [
        lambda: n.add_line("1"),
        lambda: n.add_line("2"),
        lambda: n.add_stop("1", "Central"),
        lambda: n.add_stop("1", "Park"),
        lambda: n.add_stop("1", "Harbour"),
        lambda: n.add_stop("2", "Station"),
        lambda: n.add_stop("2", "Park"),
        lambda: n.add_line("3"),
        lambda: n.add_stop("3", "Zoo"),
        lambda: n.add_stop("3", "Central"),
        lambda: n.remove_stop("1", "Park"),
        lambda: n.close_stop("Central"),
        lambda: n.merge_lines("3", "1"),
        lambda: n.add_stop("3", "Beach"),
        lambda: n.merge_lines("2", "3"),
        lambda: n.close_stop("Park"),
    ]
    states = [state(n)]
    for call in calls:
        call()
        states.append(state(n))
    assert n.get_lines() == ["2"]
    assert n.get_stops("2") == ["Station", "Zoo", "Harbour", "Beach"]
    for expected in reversed(states[:-1]):
        n.undo()
        assert state(n) == expected
    with pytest.raises(TramError):
        n.undo()
    assert n.get_lines() == []


def test_failed_calls_are_not_recorded(network):
    network.add_stop("7", "Beach")
    for call in (
        lambda: network.add_line("4"),
        lambda: network.add_stop("4", "Park"),
        lambda: network.add_stop("9", "Park"),
        lambda: network.remove_stop("7", "Park"),
        lambda: network.close_stop("Airport"),
        lambda: network.merge_lines("4", "4"),
        lambda: network.merge_lines("4", "9"),
    ):
        with pytest.raises((KeyError, ValueError, TramError)):
            call()
    network.undo()  # the add_stop of Beach
    assert network.get_stops("7") == ["Zoo"]
    assert network.get_lines() == ["4", "1", "7"]


def test_get_calls_are_not_recorded(network):
    network.add_stop("7", "Beach")
    network.get_stops("7")
    network.get_lines()
    network.get_lines_through("Beach")
    network.undo()
    assert network.get_stops("7") == ["Zoo"]
    assert network.get_stops("1") == ["Station", "Park", "Central"]


def test_there_is_no_redo():
    n = TramNetwork()
    n.add_line("1")
    n.add_stop("1", "Central")
    n.undo()
    n.undo()
    assert n.get_lines() == []
    with pytest.raises(TramError):
        n.undo()


def test_new_calls_after_an_undo_are_undone_first(network):
    network.add_stop("7", "Beach")
    network.undo()
    network.add_stop("7", "Airport")
    network.undo()
    assert network.get_stops("7") == ["Zoo"]
    network.undo()  # the add_stop of Zoo in the fixture
    assert network.get_stops("7") == []
    assert network.get_stops("1") == ["Station", "Park", "Central"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    n = TramNetwork()
    with pytest.raises(TramError):
        n.undo()
    n.add_line("1")
    n.undo()
    with pytest.raises(TramError):
        n.undo()
    assert n.get_lines() == []
    n.add_line("1")
    n.add_stop("1", "Central")
    assert n.get_stops("1") == ["Central"]


def test_the_whole_fixture_can_be_undone(network):
    for _ in range(11):
        network.undo()
    assert network.get_lines() == []
    with pytest.raises(TramError):
        network.undo()


def test_undo_restores_stops_that_a_later_call_checks(network):
    network.close_stop("Park")
    network.undo()
    with pytest.raises(TramError):
        network.add_stop("4", "Park")
    assert network.close_stop("Park") == 2
    with pytest.raises(TramError):
        network.remove_stop("1", "Park")
