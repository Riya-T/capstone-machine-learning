"""Public checks for the c_capacity change (freezer capacities). Shown to the
editor, never to the writer.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from freezers import Freezers, Full


def test_a_full_freezer_refuses_another_stored_sample():
    lab = Freezers()
    lab.add_freezer("A")
    assert lab.get_capacity("A") is None
    lab.set_capacity("A", 2)
    assert lab.get_capacity("A") == 2
    lab.store("A", "s1")
    lab.store("A", "s2")
    with pytest.raises(Full):
        lab.store("A", "s3")
    assert lab.get_samples("A") == ["s1", "s2"]


def test_moving_into_a_full_freezer_raises_full():
    lab = Freezers()
    lab.add_freezer("A")
    lab.add_freezer("B")
    lab.store("A", "s1")
    lab.store("B", "s2")
    lab.set_capacity("B", 1)
    with pytest.raises(Full):
        lab.move("s1", "B")
    assert lab.find("s1") == "A"
    assert lab.get_samples("B") == ["s2"]
