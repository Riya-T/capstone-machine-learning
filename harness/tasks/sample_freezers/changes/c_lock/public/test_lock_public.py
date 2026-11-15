"""Public checks for the c_lock change (locked freezers). Shown to the
editor, never to the writer.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/public/test_lock_public.py
"""

import pytest
from freezers import Freezers, Locked


def test_a_locked_freezer_refuses_new_samples():
    lab = Freezers()
    lab.add_freezer("A")
    lab.lock("A")
    with pytest.raises(Locked):
        lab.store("A", "s1")
    assert lab.get_samples("A") == []
    lab.unlock("A")
    lab.store("A", "s1")
    assert lab.get_samples("A") == ["s1"]


def test_a_sample_in_a_locked_freezer_cannot_be_discarded():
    lab = Freezers()
    lab.add_freezer("A")
    lab.store("A", "s1")
    lab.lock("A")
    with pytest.raises(Locked):
        lab.discard("s1")
    assert lab.find("s1") == "A"
