"""Public checks for the c_slots change (validation_rule). Shown to the
editor, never to the writer.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_slots/public/test_slots_public.py
"""

import pytest
from racks import RackFull, Racks


@pytest.fixture
def dc():
    r = Racks()
    r.add_rack("A", slots=2)
    r.add_rack("B")
    return r


def test_slots_are_reported(dc):
    assert dc.get_slots("A") == 2
    assert dc.get_slots("B") is None


def test_every_slot_can_be_filled(dc):
    dc.install("A", "web1")
    dc.install("A", "web2")
    assert dc.get_servers("A") == ["web1", "web2"]


def test_installing_into_a_full_rack_raises(dc):
    dc.install("A", "web1")
    dc.install("A", "web2")
    with pytest.raises(RackFull):
        dc.install("A", "web3")
    assert dc.get_servers("A") == ["web1", "web2"]
