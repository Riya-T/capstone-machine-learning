"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from racks import RackError, Racks


@pytest.fixture
def dc():
    r = Racks()
    for name in ["A", "B", "C"]:
        r.add_rack(name)
    for server in ["web1", "web2", "db1"]:
        r.install("A", server)
    r.install("B", "cache1")
    return r


def state(r):
    return [(name, r.get_servers(name)) for name in r.get_racks()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_install(dc):
    before = state(dc)
    dc.install("C", "app1")
    dc.undo()
    assert state(dc) == before
    with pytest.raises(KeyError):
        dc.remove("app1")


def test_an_undone_install_frees_the_name(dc):
    dc.install("C", "app1")
    dc.undo()
    dc.install("B", "app1")
    assert dc.get_servers("B") == ["cache1", "app1"]


def test_undo_of_remove_puts_the_server_back_in_its_place(dc):
    before = state(dc)
    dc.remove("web2")
    dc.undo()
    assert dc.get_servers("A") == ["web1", "web2", "db1"]
    assert state(dc) == before


def test_a_server_brought_back_is_installed_again(dc):
    dc.remove("web1")
    dc.undo()
    with pytest.raises(RackError):
        dc.install("C", "web1")
    dc.move("web1", "C")
    assert dc.get_servers("C") == ["web1"]


def test_undo_of_move_puts_the_server_back_in_its_place(dc):
    before = state(dc)
    dc.move("web1", "B")
    dc.undo()
    assert state(dc) == before
    assert dc.get_servers("A") == ["web1", "web2", "db1"]


def test_undo_of_migrate_all_restores_both_racks(dc):
    before = state(dc)
    assert dc.migrate_all("A", "B") == 3
    dc.undo()
    assert state(dc) == before
    assert dc.get_servers("B") == ["cache1"]


def test_undo_of_migrate_all_into_an_empty_rack(dc):
    before = state(dc)
    dc.migrate_all("A", "C")
    dc.undo()
    assert state(dc) == before
    assert dc.get_servers("C") == []


def test_undo_of_decommission_brings_the_rack_back_with_its_servers(dc):
    before = state(dc)
    assert dc.decommission_rack("A", "C") == 3
    dc.undo()
    assert state(dc) == before
    assert dc.get_racks() == ["A", "B", "C"]
    assert dc.get_servers("C") == []


def test_undo_of_decommission_keeps_its_place_in_the_list(dc):
    dc.add_rack("D")
    before = state(dc)
    dc.decommission_rack("B", "D")
    assert dc.get_racks() == ["A", "C", "D"]
    dc.undo()
    assert dc.get_racks() == ["A", "B", "C", "D"]
    assert state(dc) == before


def test_a_rack_brought_back_is_in_use_again(dc):
    dc.decommission_rack("A", "B")
    dc.undo()
    dc.install("A", "app1")
    assert dc.get_servers("A") == ["web1", "web2", "db1", "app1"]
    with pytest.raises(RackError):
        dc.add_rack("A")
    assert dc.decommission_rack("A", "C") == 4
    assert dc.get_racks() == ["B", "C"]


def test_undo_of_add_rack_removes_it_and_frees_the_name(dc):
    dc.add_rack("D")
    dc.undo()
    assert dc.get_racks() == ["A", "B", "C"]
    with pytest.raises(KeyError):
        dc.get_servers("D")
    dc.add_rack("D")
    assert dc.get_racks() == ["A", "B", "C", "D"]
    assert dc.get_servers("D") == []


def test_undo_of_two_decommissions_in_a_row(dc):
    before = state(dc)
    dc.decommission_rack("A", "B")
    dc.decommission_rack("B", "C")
    assert state(dc) == [("C", ["cache1", "web1", "web2", "db1"])]
    dc.undo()
    assert state(dc) == [("B", ["cache1", "web1", "web2", "db1"]), ("C", [])]
    dc.undo()
    assert state(dc) == before


# --- calls that move nothing --------------------------------------------------


def test_a_migrate_all_of_nothing_is_still_a_call(dc):
    dc.install("C", "app1")
    dc.remove("app1")
    assert dc.migrate_all("C", "A") == 0
    dc.undo()  # the migrate_all, which changed nothing
    assert dc.get_servers("C") == []
    dc.undo()  # the remove
    assert dc.get_servers("C") == ["app1"]


def test_decommissioning_an_empty_rack_can_be_undone(dc):
    dc.install("A", "app1")
    assert dc.decommission_rack("C", "A") == 0
    dc.undo()
    assert dc.get_racks() == ["A", "B", "C"]
    assert dc.get_servers("A") == ["web1", "web2", "db1", "app1"]
    dc.undo()
    assert dc.get_servers("A") == ["web1", "web2", "db1"]


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    r = Racks()
    calls = [
        lambda: r.add_rack("A"),
        lambda: r.add_rack("B"),
        lambda: r.install("A", "web1"),
        lambda: r.install("A", "web2"),
        lambda: r.install("A", "db1"),
        lambda: r.add_rack("C"),
        lambda: r.install("B", "cache1"),
        lambda: r.remove("web2"),
        lambda: r.move("web1", "C"),
        lambda: r.migrate_all("A", "C"),
        lambda: r.decommission_rack("B", "C"),
        lambda: r.add_rack("D"),
        lambda: r.install("D", "app1"),
        lambda: r.migrate_all("C", "D"),
        lambda: r.decommission_rack("D", "A"),
    ]
    states = [state(r)]
    for call in calls:
        call()
        states.append(state(r))
    assert state(r) == [("A", ["app1", "web1", "db1", "cache1"]), ("C", [])]
    for expected in reversed(states[:-1]):
        r.undo()
        assert state(r) == expected
    with pytest.raises(RackError):
        r.undo()
    assert r.get_racks() == []


def test_failed_calls_are_not_recorded(dc):
    dc.install("C", "app1")
    for call in (
        lambda: dc.add_rack("A"),
        lambda: dc.install("B", "web1"),
        lambda: dc.install("Z", "web9"),
        lambda: dc.remove("web9"),
        lambda: dc.move("web1", "Z"),
        lambda: dc.move("web9", "B"),
        lambda: dc.migrate_all("A", "A"),
        lambda: dc.migrate_all("A", "Z"),
        lambda: dc.decommission_rack("A", "A"),
        lambda: dc.decommission_rack("Z", "A"),
    ):
        with pytest.raises((ValueError, KeyError, RackError)):
            call()
    dc.undo()  # the install of app1
    assert dc.get_servers("C") == []
    assert dc.get_servers("A") == ["web1", "web2", "db1"]


def test_get_calls_are_not_recorded(dc):
    dc.install("C", "app1")
    dc.get_servers("C")
    dc.get_racks()
    dc.undo()
    assert dc.get_servers("C") == []
    assert dc.get_servers("B") == ["cache1"]


def test_there_is_no_redo():
    r = Racks()
    r.add_rack("A")
    r.install("A", "web1")
    r.undo()
    r.undo()
    assert r.get_racks() == []
    with pytest.raises(RackError):
        r.undo()


def test_new_calls_after_an_undo_are_undone_first(dc):
    dc.install("C", "app1")
    dc.undo()
    dc.install("C", "app2")
    dc.undo()
    assert dc.get_servers("C") == []
    dc.undo()  # the install of cache1 in the fixture
    assert dc.get_servers("B") == []
    assert dc.get_servers("A") == ["web1", "web2", "db1"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    r = Racks()
    with pytest.raises(RackError):
        r.undo()
    r.add_rack("A")
    r.undo()
    with pytest.raises(RackError):
        r.undo()
    assert r.get_racks() == []
    r.add_rack("A")
    r.install("A", "web1")
    assert r.get_servers("A") == ["web1"]


def test_the_whole_fixture_can_be_undone(dc):
    for _ in range(7):
        dc.undo()
    assert dc.get_racks() == []
    with pytest.raises(RackError):
        dc.undo()
