"""Hidden tests for the c_install_many change (atomic_operation). Never shown
to the writer or the editor.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_install_many/private/test_install_many_new.py
"""

import pytest
from racks import RackError, Racks


@pytest.fixture
def dc():
    r = Racks()
    for name in ["A", "B", "C"]:
        r.add_rack(name)
    for server in ["web1", "web2"]:
        r.install("A", server)
    r.install("B", "cache1")
    return r


def state(r):
    return [(name, r.get_servers(name)) for name in r.get_racks()]


# --- successful batches -----------------------------------------------------


def test_install_many_into_an_empty_rack(dc):
    assert dc.install_many("C", ["app1", "app2", "app3"]) == 3
    assert dc.get_servers("C") == ["app1", "app2", "app3"]


def test_install_many_goes_after_the_servers_already_there(dc):
    assert dc.install_many("A", ["db1", "db2"]) == 2
    assert dc.get_servers("A") == ["web1", "web2", "db1", "db2"]
    assert dc.get_servers("B") == ["cache1"]


def test_a_single_server(dc):
    assert dc.install_many("B", ["cache2"]) == 1
    assert dc.get_servers("B") == ["cache1", "cache2"]


def test_an_empty_list_installs_nothing(dc):
    before = state(dc)
    assert dc.install_many("C", []) == 0
    assert state(dc) == before


def test_servers_installed_together_are_ordinary_servers(dc):
    dc.install_many("C", ["app1", "app2"])
    dc.move("app1", "A")
    dc.remove("app2")
    with pytest.raises(RackError):
        dc.install("B", "app1")
    assert state(dc) == [("A", ["web1", "web2", "app1"]), ("B", ["cache1"]), ("C", [])]


def test_install_many_after_install_many(dc):
    dc.install_many("C", ["app1"])
    dc.install_many("C", ["app2", "app3"])
    assert dc.get_servers("C") == ["app1", "app2", "app3"]


# --- failing batches install nothing ----------------------------------------


@pytest.mark.parametrize(
    "servers",
    [
        ["app1", "app2", "web1"],
        ["cache1", "app1"],
        ["app1", "web2", "app2"],
    ],
    ids=["last_installed", "first_installed", "middle_installed"],
)
def test_a_name_already_installed_installs_none(dc, servers):
    before = state(dc)
    with pytest.raises(RackError):
        dc.install_many("C", servers)
    assert state(dc) == before


@pytest.mark.parametrize(
    "servers",
    [["app1", "app2", "app1"], ["app1", "app1"]],
)
def test_a_name_twice_in_the_list_installs_none(dc, servers):
    before = state(dc)
    with pytest.raises(RackError):
        dc.install_many("C", servers)
    assert state(dc) == before


def test_a_rack_not_in_use_raises_key_error(dc):
    before = state(dc)
    with pytest.raises(KeyError):
        dc.install_many("Z", ["app1"])
    dc.decommission_rack("C", "A")
    with pytest.raises(KeyError):
        dc.install_many("C", ["app1"])
    assert dc.get_racks() == ["A", "B"]
    assert state(dc) == before[:2]


def test_names_from_a_failed_batch_are_still_free(dc):
    with pytest.raises(RackError):
        dc.install_many("C", ["app1", "app2", "web1"])
    dc.install("B", "app1")
    assert dc.install_many("C", ["app2", "app3"]) == 2
    assert state(dc) == [("A", ["web1", "web2"]), ("B", ["cache1", "app1"]), ("C", ["app2", "app3"])]
