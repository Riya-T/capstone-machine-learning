"""Public checks for racks.py.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest public/test_racks_public.py
"""

import pytest
from racks import RackError, Racks


@pytest.fixture
def dc():
    r = Racks()
    r.add_rack("A")
    r.add_rack("B")
    for server in ["web1", "web2", "db1"]:
        r.install("A", server)
    return r


def test_servers_are_kept_in_the_order_installed(dc):
    assert dc.get_servers("A") == ["web1", "web2", "db1"]
    assert dc.get_servers("B") == []
    assert dc.get_racks() == ["A", "B"]


def test_installing_a_name_twice_is_rejected(dc):
    with pytest.raises(RackError):
        dc.install("A", "web1")
    assert dc.get_servers("A") == ["web1", "web2", "db1"]


def test_removing_a_server_closes_the_gap(dc):
    dc.remove("web2")
    assert dc.get_servers("A") == ["web1", "db1"]
    with pytest.raises(KeyError):
        dc.remove("web2")


def test_a_moved_server_goes_to_the_end(dc):
    dc.install("B", "cache1")
    dc.move("web1", "B")
    assert dc.get_servers("A") == ["web2", "db1"]
    assert dc.get_servers("B") == ["cache1", "web1"]


def test_migrate_all_keeps_the_order_after_the_servers_already_there(dc):
    dc.install("B", "cache1")
    assert dc.migrate_all("A", "B") == 3
    assert dc.get_servers("B") == ["cache1", "web1", "web2", "db1"]
    assert dc.get_servers("A") == []
    assert dc.get_racks() == ["A", "B"]


def test_a_decommissioned_rack_is_gone(dc):
    assert dc.decommission_rack("A", "B") == 3
    assert dc.get_racks() == ["B"]
    assert dc.get_servers("B") == ["web1", "web2", "db1"]
    with pytest.raises(KeyError):
        dc.get_servers("A")
    with pytest.raises(KeyError):
        dc.install("A", "web9")
