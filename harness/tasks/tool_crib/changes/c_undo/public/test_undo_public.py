"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from crib import CribError, ToolCrib


@pytest.fixture
def crib():
    c = ToolCrib()
    c.add_bin("drills")
    c.add_bin("saws")
    return c


def test_undo_takes_back_the_last_added_tool(crib):
    crib.add_tool("drills", "hammer drill")
    crib.add_tool("drills", "cordless drill")
    crib.undo()
    assert crib.get_tools("drills") == ["hammer drill"]
    crib.undo()
    assert crib.get_tools("drills") == []


def test_undo_takes_back_a_return(crib):
    crib.add_tool("saws", "jigsaw")
    crib.check_out("jigsaw", "ann")
    crib.return_tool("jigsaw", "drills")
    crib.undo()
    assert crib.get_holder("jigsaw") == "ann"
    assert crib.get_tools("drills") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(CribError):
        ToolCrib().undo()
