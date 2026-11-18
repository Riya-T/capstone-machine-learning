"""Public checks for the c_many change (checking out several tools in one
call). Shown to the editor, never to the writer.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest changes/c_many/public/test_many_public.py
"""

import pytest
from crib import ToolCrib


@pytest.fixture
def crib():
    c = ToolCrib()
    c.add_bin("drills")
    c.add_bin("saws")
    c.add_tool("drills", "hammer drill")
    c.add_tool("drills", "drill press")
    c.add_tool("saws", "jigsaw")
    return c


def test_check_out_many_takes_every_tool(crib):
    crib.check_out_many(["jigsaw", "hammer drill"], "ann")
    assert crib.get_holder("jigsaw") == "ann"
    assert crib.get_holder("hammer drill") == "ann"
    assert crib.get_tools("drills") == ["drill press"]
    assert crib.get_tools("saws") == []


def test_one_checked_out_tool_stops_the_whole_call(crib):
    crib.check_out("jigsaw", "bob")
    with pytest.raises(KeyError):
        crib.check_out_many(["hammer drill", "jigsaw"], "ann")
    assert crib.get_holder("hammer drill") is None
    assert crib.get_tools("drills") == ["hammer drill", "drill press"]
