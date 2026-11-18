"""Public checks for the c_install_many change (atomic_operation). Shown to
the editor, never to the writer.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_install_many/public/test_install_many_public.py
"""

import pytest
from racks import RackError, Racks


@pytest.fixture
def dc():
    r = Racks()
    r.add_rack("A")
    r.add_rack("B")
    r.install("A", "web1")
    return r


def test_install_many_appends_in_list_order(dc):
    assert dc.install_many("A", ["web2", "db1"]) == 2
    assert dc.get_servers("A") == ["web1", "web2", "db1"]


def test_one_bad_name_installs_none_of_the_list(dc):
    with pytest.raises(RackError):
        dc.install_many("B", ["app1", "web1", "app2"])
    assert dc.get_servers("B") == []
