"""Hidden tests for the c_slots change (validation_rule). Never shown to the
writer or the editor.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_slots/private/test_slots_new.py
"""

import pytest
from racks import RackError, RackFull, Racks


@pytest.fixture
def dc():
    r = Racks()
    r.add_rack("A", slots=4)
    r.add_rack("B")
    r.add_rack("C", slots=3)
    for server in ["web1", "web2", "db1"]:
        r.install("A", server)
    r.install("C", "cache1")
    return r


def state(r):
    return [(name, r.get_servers(name)) for name in r.get_racks()]


# --- the slots setting ------------------------------------------------------


def test_racks_have_no_limit_by_default():
    r = Racks()
    r.add_rack("A")
    assert r.get_slots("A") is None
    for i in range(60):
        r.install("A", f"s{i}")
    assert len(r.get_servers("A")) == 60


def test_slots_can_be_none_explicitly():
    r = Racks()
    r.add_rack("A", slots=None)
    assert r.get_slots("A") is None


def test_slots_are_reported_per_rack(dc):
    assert dc.get_slots("A") == 4
    assert dc.get_slots("B") is None
    assert dc.get_slots("C") == 3


@pytest.mark.parametrize("slots", [0, -2])
def test_slots_of_0_or_less_are_rejected(dc, slots):
    before = state(dc)
    with pytest.raises(ValueError):
        dc.add_rack("D", slots=slots)
    assert state(dc) == before
    assert dc.get_racks() == ["A", "B", "C"]


def test_get_slots_of_a_rack_not_in_use_raises(dc):
    with pytest.raises(KeyError):
        dc.get_slots("Z")
    dc.decommission_rack("B", "A")
    with pytest.raises(KeyError):
        dc.get_slots("B")


def test_rack_full_is_a_rack_error():
    assert issubclass(RackFull, RackError)


# --- install and move -------------------------------------------------------


def test_install_into_a_full_rack_changes_nothing(dc):
    dc.install("A", "app1")
    before = state(dc)
    with pytest.raises(RackFull):
        dc.install("A", "app2")
    assert state(dc) == before


def test_a_removed_server_frees_its_slot(dc):
    dc.install("A", "app1")
    dc.remove("web1")
    dc.install("A", "app2")
    assert dc.get_servers("A") == ["web2", "db1", "app1", "app2"]


def test_move_into_a_rack_with_a_free_slot(dc):
    dc.move("web1", "C")
    dc.move("web2", "C")
    assert dc.get_servers("C") == ["cache1", "web1", "web2"]


def test_move_into_a_full_rack_changes_nothing(dc):
    dc.move("web1", "C")
    dc.move("web2", "C")
    before = state(dc)
    with pytest.raises(RackFull):
        dc.move("db1", "C")
    assert state(dc) == before


def test_the_rack_a_server_leaves_is_not_checked(dc):
    dc.install("A", "app1")
    dc.move("app1", "B")
    dc.remove("web1")
    assert dc.get_servers("A") == ["web2", "db1"]


# --- migrate_all and decommission_rack --------------------------------------


def test_migrate_all_may_fill_every_slot(dc):
    dc.remove("web1")
    assert dc.migrate_all("A", "C") == 2
    assert dc.get_servers("C") == ["cache1", "web2", "db1"]


def test_migrate_all_into_too_few_slots_moves_nothing(dc):
    before = state(dc)
    with pytest.raises(RackFull):
        dc.migrate_all("A", "C")
    assert state(dc) == before


def test_migrate_all_into_an_unlimited_rack(dc):
    assert dc.migrate_all("A", "B") == 3
    assert dc.get_servers("B") == ["web1", "web2", "db1"]


def test_decommission_into_too_few_slots_does_not_remove_the_rack(dc):
    before = state(dc)
    with pytest.raises(RackFull):
        dc.decommission_rack("A", "C")
    assert state(dc) == before
    assert dc.get_racks() == ["A", "B", "C"]


def test_decommission_into_a_rack_with_room(dc):
    assert dc.decommission_rack("C", "A") == 1
    assert dc.get_servers("A") == ["web1", "web2", "db1", "cache1"]
    assert dc.get_racks() == ["A", "B"]


def test_decommissioning_an_empty_rack_into_a_full_rack_is_allowed(dc):
    dc.install("A", "app1")
    assert dc.decommission_rack("B", "A") == 0
    assert dc.get_racks() == ["A", "C"]
