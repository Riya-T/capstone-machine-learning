"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from racks import RackError, Racks


@pytest.fixture
def dc():
    r = Racks()
    r.add_rack("A")
    r.add_rack("B")
    return r


def test_undo_takes_back_the_last_install(dc):
    dc.install("A", "web1")
    dc.install("A", "web2")
    dc.undo()
    assert dc.get_servers("A") == ["web1"]
    dc.undo()
    assert dc.get_servers("A") == []


def test_undo_takes_back_a_move(dc):
    dc.install("A", "web1")
    dc.install("A", "web2")
    dc.move("web1", "B")
    dc.undo()
    assert dc.get_servers("A") == ["web1", "web2"]
    assert dc.get_servers("B") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(RackError):
        Racks().undo()
