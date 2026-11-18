"""Public checks for the c_lock change (locked bins). Shown to the editor,
never to the writer.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/public/test_lock_public.py
"""

import pytest
from crib import BinLocked, ToolCrib


@pytest.fixture
def crib():
    c = ToolCrib()
    c.add_bin("drills")
    c.add_bin("saws")
    c.add_tool("drills", "hammer drill")
    c.add_tool("saws", "jigsaw")
    return c


def test_no_tool_comes_out_of_a_locked_bin(crib):
    crib.lock_bin("drills")
    with pytest.raises(BinLocked):
        crib.check_out("hammer drill", "ann")
    assert crib.get_tools("drills") == ["hammer drill"]
    assert crib.get_holder("hammer drill") is None


def test_no_tool_goes_into_a_locked_bin(crib):
    crib.check_out("jigsaw", "ann")
    crib.lock_bin("saws")
    with pytest.raises(BinLocked):
        crib.return_tool("jigsaw", "saws")
    assert crib.get_holder("jigsaw") == "ann"
    crib.unlock_bin("saws")
    crib.return_tool("jigsaw", "saws")
    assert crib.get_tools("saws") == ["jigsaw"]
