"""Public checks for crib.py.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest public/test_crib_public.py
"""

import pytest
from crib import ToolCrib


@pytest.fixture
def crib():
    c = ToolCrib()
    c.add_bin("drills")
    c.add_bin("saws")
    for tool in ["hammer drill", "cordless drill", "drill press"]:
        c.add_tool("drills", tool)
    c.add_tool("saws", "jigsaw")
    return c


def test_tools_are_listed_in_the_order_added(crib):
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press"]
    assert crib.get_tools("saws") == ["jigsaw"]


def test_a_returned_tool_goes_to_the_end_of_the_bin(crib):
    crib.check_out("hammer drill", "ann")
    assert crib.get_tools("drills") == ["cordless drill", "drill press"]
    assert crib.get_holder("hammer drill") == "ann"
    crib.return_tool("hammer drill", "drills")
    assert crib.get_tools("drills") == ["cordless drill", "drill press", "hammer drill"]
    assert crib.get_holder("hammer drill") is None


def test_a_tool_can_be_returned_to_another_bin(crib):
    crib.check_out("jigsaw", "ann")
    crib.return_tool("jigsaw", "drills")
    assert crib.get_tools("saws") == []
    assert crib.get_tools("drills")[-1] == "jigsaw"


def test_checking_out_a_checked_out_tool_raises_key_error(crib):
    crib.check_out("jigsaw", "ann")
    with pytest.raises(KeyError):
        crib.check_out("jigsaw", "bob")
    assert crib.get_holder("jigsaw") == "ann"


def test_return_all_returns_only_that_persons_tools(crib):
    crib.check_out("jigsaw", "ann")
    crib.check_out("drill press", "bob")
    assert crib.return_all("ann", "saws") == 1
    assert crib.get_tools("saws") == ["jigsaw"]
    assert crib.get_holder("jigsaw") is None
    assert crib.get_holder("drill press") == "bob"


def test_close_bin_moves_its_tools_and_frees_its_name(crib):
    assert crib.close_bin("drills", "saws") == 3
    assert crib.get_tools("saws") == ["jigsaw", "hammer drill", "cordless drill", "drill press"]
    with pytest.raises(KeyError):
        crib.get_tools("drills")
    crib.add_bin("drills")
    assert crib.get_tools("drills") == []
