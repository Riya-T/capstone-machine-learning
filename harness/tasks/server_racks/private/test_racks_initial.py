"""Hidden tests for the initial server_racks spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest private/test_racks_initial.py
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
    """Every rack in order with its servers, to check that a failed call
    changed nothing."""
    return [(name, r.get_servers(name)) for name in r.get_racks()]


# --- racks --------------------------------------------------------------------


def test_a_new_rack_is_empty():
    r = Racks()
    r.add_rack("A")
    assert r.get_servers("A") == []


def test_a_new_object_has_no_racks():
    assert Racks().get_racks() == []


def test_racks_are_listed_in_the_order_added():
    r = Racks()
    for name in ["B", "C", "A"]:
        r.add_rack(name)
    assert r.get_racks() == ["B", "C", "A"]


def test_adding_a_name_in_use_is_rejected(dc):
    before = state(dc)
    with pytest.raises(RackError):
        dc.add_rack("A")
    assert state(dc) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.install("Z", "web9"),
        lambda r: r.move("web1", "Z"),
        lambda r: r.migrate_all("Z", "B"),
        lambda r: r.migrate_all("A", "Z"),
        lambda r: r.decommission_rack("Z", "B"),
        lambda r: r.decommission_rack("A", "Z"),
        lambda r: r.get_servers("Z"),
    ],
)
def test_racks_that_were_never_added_raise_key_error(dc, call):
    before = state(dc)
    with pytest.raises(KeyError):
        call(dc)
    assert state(dc) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.install("C", "web9"),
        lambda r: r.move("web1", "C"),
        lambda r: r.migrate_all("C", "B"),
        lambda r: r.migrate_all("A", "C"),
        lambda r: r.decommission_rack("C", "B"),
        lambda r: r.decommission_rack("A", "C"),
        lambda r: r.get_servers("C"),
    ],
)
def test_a_decommissioned_rack_is_not_in_use(dc, call):
    dc.decommission_rack("C", "B")  # C is empty
    before = state(dc)
    with pytest.raises(KeyError):
        call(dc)
    assert state(dc) == before


# --- installing and removing --------------------------------------------------


def test_servers_keep_the_order_they_were_installed_in(dc):
    dc.install("A", "app1")
    assert dc.get_servers("A") == ["web1", "web2", "db1", "app1"]
    assert dc.get_servers("B") == ["cache1"]


def test_a_name_installed_in_another_rack_is_rejected(dc):
    before = state(dc)
    with pytest.raises(RackError):
        dc.install("C", "web1")
    with pytest.raises(RackError):
        dc.install("A", "cache1")
    with pytest.raises(RackError):
        dc.install("B", "cache1")
    assert state(dc) == before


def test_remove_closes_the_gap(dc):
    dc.remove("web2")
    assert dc.get_servers("A") == ["web1", "db1"]
    dc.remove("web1")
    dc.remove("db1")
    assert dc.get_servers("A") == []
    assert dc.get_servers("B") == ["cache1"]


@pytest.mark.parametrize(
    "call",
    [lambda r: r.remove("web9"), lambda r: r.move("web9", "B")],
    ids=["remove", "move"],
)
def test_servers_that_are_not_installed_raise_key_error(dc, call):
    before = state(dc)
    with pytest.raises(KeyError):
        call(dc)
    assert state(dc) == before


def test_a_removed_server_is_not_installed(dc):
    dc.remove("web1")
    with pytest.raises(KeyError):
        dc.remove("web1")
    with pytest.raises(KeyError):
        dc.move("web1", "B")


# --- moving -------------------------------------------------------------------


def test_move_puts_the_server_at_the_end(dc):
    dc.move("web1", "B")
    assert dc.get_servers("A") == ["web2", "db1"]
    assert dc.get_servers("B") == ["cache1", "web1"]


def test_a_server_can_be_moved_into_an_empty_rack_and_back(dc):
    dc.move("web2", "C")
    assert dc.get_servers("C") == ["web2"]
    dc.move("web2", "A")
    assert dc.get_servers("A") == ["web1", "db1", "web2"]
    assert dc.get_servers("C") == []


def test_a_moved_server_is_still_a_taken_name(dc):
    dc.move("web1", "C")
    with pytest.raises(RackError):
        dc.install("A", "web1")
    dc.remove("web1")
    assert dc.get_servers("C") == []


# --- migrating ----------------------------------------------------------------


def test_migrate_all_appends_in_the_same_order(dc):
    assert dc.migrate_all("A", "B") == 3
    assert dc.get_servers("B") == ["cache1", "web1", "web2", "db1"]
    assert dc.get_servers("A") == []
    assert dc.get_racks() == ["A", "B", "C"]


def test_migrate_all_into_an_empty_rack(dc):
    assert dc.migrate_all("A", "C") == 3
    assert dc.get_servers("C") == ["web1", "web2", "db1"]


def test_migrating_an_empty_rack_moves_nothing(dc):
    before = state(dc)
    assert dc.migrate_all("C", "A") == 0
    assert state(dc) == before


def test_a_migrated_rack_stays_in_use(dc):
    dc.migrate_all("A", "C")
    dc.install("A", "app1")
    dc.move("web1", "A")
    assert dc.get_servers("A") == ["app1", "web1"]
    assert dc.migrate_all("C", "A") == 2
    assert dc.get_servers("A") == ["app1", "web1", "web2", "db1"]


def test_migrated_servers_can_be_moved_and_removed(dc):
    dc.migrate_all("A", "B")
    dc.move("web2", "C")
    dc.remove("cache1")
    assert state(dc) == [("A", []), ("B", ["web1", "db1"]), ("C", ["web2"])]


# --- decommissioning --------------------------------------------------------------


def test_decommission_moves_every_server_and_removes_the_rack(dc):
    assert dc.decommission_rack("A", "B") == 3
    assert dc.get_racks() == ["B", "C"]
    assert dc.get_servers("B") == ["cache1", "web1", "web2", "db1"]


def test_decommissioning_an_empty_rack_moves_nothing(dc):
    assert dc.decommission_rack("C", "A") == 0
    assert dc.get_racks() == ["A", "B"]
    assert dc.get_servers("A") == ["web1", "web2", "db1"]


def test_the_other_racks_keep_their_order_after_a_decommission(dc):
    dc.add_rack("D")
    dc.decommission_rack("B", "D")
    assert dc.get_racks() == ["A", "C", "D"]
    dc.decommission_rack("A", "C")
    assert dc.get_racks() == ["C", "D"]
    assert state(dc) == [("C", ["web1", "web2", "db1"]), ("D", ["cache1"])]


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.migrate_all("A", "A"),
        lambda r: r.decommission_rack("A", "A"),
        lambda r: r.migrate_all("C", "C"),
    ],
    ids=["migrate_all", "decommission_rack", "migrate_all_empty"],
)
def test_the_same_rack_on_both_sides_is_rejected(dc, call):
    before = state(dc)
    with pytest.raises(ValueError):
        call(dc)
    assert state(dc) == before


# --- general ------------------------------------------------------------------


def test_objects_do_not_share_racks():
    first, second = Racks(), Racks()
    first.add_rack("A")
    first.install("A", "web1")
    assert second.get_racks() == []
    second.add_rack("A")
    second.install("A", "web1")
    assert second.get_servers("A") == ["web1"]
