"""Hidden tests for the c_versions change (concurrency_control). Never shown
to the writer or the editor.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from racks import RackError, Racks, VersionConflict


@pytest.fixture
def dc():
    r = Racks()
    for name in ["A", "B", "C"]:
        r.add_rack(name)
    for server in ["web1", "web2", "db1"]:
        r.install("A", server)
    r.install("B", "cache1")
    return r  # version 7


def state(r):
    return [(name, r.get_servers(name)) for name in r.get_racks()]


CHANGES = [
    lambda r, **kw: r.add_rack("D", **kw),
    lambda r, **kw: r.install("C", "app1", **kw),
    lambda r, **kw: r.remove("web2", **kw),
    lambda r, **kw: r.move("web1", "B", **kw),
    lambda r, **kw: r.migrate_all("A", "C", **kw),
    lambda r, **kw: r.decommission_rack("A", "B", **kw),
]
IDS = ["add_rack", "install", "remove", "move", "migrate_all", "decommission_rack"]


# --- counting -----------------------------------------------------------------


def test_a_new_object_is_at_version_0():
    assert Racks().get_version() == 0


def test_each_successful_change_adds_1(dc):
    assert dc.get_version() == 7


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_every_kind_of_change_adds_exactly_1(dc, call):
    call(dc)
    assert dc.get_version() == 8


def test_moving_many_servers_still_adds_1(dc):
    assert dc.migrate_all("A", "C") == 3
    assert dc.get_version() == 8
    assert dc.decommission_rack("C", "B") == 3
    assert dc.get_version() == 9


def test_moving_no_servers_still_adds_1(dc):
    assert dc.migrate_all("C", "A") == 0
    assert dc.get_version() == 8
    assert dc.decommission_rack("C", "A") == 0
    assert dc.get_version() == 9


def test_failed_calls_leave_the_version_unchanged(dc):
    for call in (
        lambda: dc.add_rack("A"),
        lambda: dc.install("C", "web1"),
        lambda: dc.install("Z", "app1"),
        lambda: dc.remove("web9"),
        lambda: dc.move("web1", "Z"),
        lambda: dc.migrate_all("A", "A"),
        lambda: dc.decommission_rack("Z", "A"),
    ):
        with pytest.raises((KeyError, ValueError, RackError)):
            call()
    assert dc.get_version() == 7


def test_get_calls_leave_the_version_unchanged(dc):
    dc.get_servers("A")
    dc.get_racks()
    dc.get_version()
    assert dc.get_version() == 7


def test_objects_count_their_own_versions(dc):
    other = Racks()
    other.add_rack("A")
    assert other.get_version() == 1
    assert dc.get_version() == 7


# --- expected_version -------------------------------------------------------------


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_the_current_version_is_accepted(dc, call):
    call(dc, expected_version=7)
    assert dc.get_version() == 8


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
@pytest.mark.parametrize("stale", [6, 8, 0])
def test_any_other_version_is_rejected_and_changes_nothing(dc, call, stale):
    before = state(dc)
    with pytest.raises(VersionConflict):
        call(dc, expected_version=stale)
    assert state(dc) == before
    assert dc.get_version() == 7


def test_none_means_no_check(dc):
    dc.install("C", "app1", expected_version=None)
    assert dc.get_servers("C") == ["app1"]
    assert dc.get_version() == 8


def test_two_consoles_editing_from_the_same_version(dc):
    seen = dc.get_version()
    dc.move("web1", "C", expected_version=seen)
    with pytest.raises(VersionConflict):
        dc.migrate_all("A", "B", expected_version=seen)
    assert dc.get_servers("A") == ["web2", "db1"]
    dc.migrate_all("A", "B", expected_version=dc.get_version())
    assert dc.get_servers("B") == ["cache1", "web2", "db1"]
    assert dc.get_version() == 9


def test_version_conflict_is_a_rack_error():
    assert issubclass(VersionConflict, RackError)
