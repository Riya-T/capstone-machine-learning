"""Hidden tests for the c_many change (checking out several tools in one
call). Never shown to the writer or the editor.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest changes/c_many/private/test_many_new.py
"""

import pytest
from crib import ToolCrib

BINS = ["drills", "saws", "clamps", "spare"]
TOOLS = ["hammer drill", "cordless drill", "drill press", "jigsaw", "hacksaw", "c-clamp"]


@pytest.fixture
def crib():
    c = ToolCrib()
    for name in BINS:
        c.add_bin(name)
    for tool in ["hammer drill", "cordless drill", "drill press"]:
        c.add_tool("drills", tool)
    c.add_tool("saws", "jigsaw")
    c.add_tool("saws", "hacksaw")
    c.add_tool("clamps", "c-clamp")
    return c


def state(c):
    return {b: c.get_tools(b) for b in BINS}, {t: c.get_holder(t) for t in TOOLS}


# --- checking out -------------------------------------------------------------


def test_many_tools_from_several_bins_leave_their_bins(crib):
    crib.check_out_many(["cordless drill", "hacksaw", "c-clamp"], "ann")
    assert crib.get_tools("drills") == ["hammer drill", "drill press"]
    assert crib.get_tools("saws") == ["jigsaw"]
    assert crib.get_tools("clamps") == []
    assert [crib.get_holder(t) for t in ["cordless drill", "hacksaw", "c-clamp"]] == ["ann"] * 3


def test_the_list_order_is_kept_not_the_bin_order(crib):
    crib.check_out_many(["drill press", "hammer drill", "jigsaw"], "bob")
    assert crib.return_all("bob", "spare") == 3
    assert crib.get_tools("spare") == ["drill press", "hammer drill", "jigsaw"]


def test_the_tools_come_after_tools_the_person_already_has(crib):
    crib.check_out("hacksaw", "ann")
    crib.check_out_many(["c-clamp", "hammer drill"], "ann")
    crib.return_all("ann", "spare")
    assert crib.get_tools("spare") == ["hacksaw", "c-clamp", "hammer drill"]


def test_a_list_of_one_tool_works_like_check_out(crib):
    crib.check_out_many(["jigsaw"], "ann")
    assert crib.get_holder("jigsaw") == "ann"
    assert crib.get_tools("saws") == ["hacksaw"]


def test_tools_checked_out_together_are_returned_like_any_other(crib):
    crib.check_out_many(["hammer drill", "jigsaw", "drill press"], "ann")
    crib.return_tool("jigsaw", "saws")
    assert crib.get_tools("saws") == ["hacksaw", "jigsaw"]
    assert crib.return_all("ann", "drills") == 2
    assert crib.get_tools("drills") == ["cordless drill", "hammer drill", "drill press"]
    assert crib.get_holder("hammer drill") is None


def test_people_keep_their_own_tools(crib):
    crib.check_out_many(["jigsaw", "hacksaw"], "ann")
    crib.check_out_many(["c-clamp"], "bob")
    assert crib.get_holder("hacksaw") == "ann"
    assert crib.get_holder("c-clamp") == "bob"
    assert crib.return_all("bob", "spare") == 1
    assert crib.get_tools("spare") == ["c-clamp"]


# --- all or nothing -----------------------------------------------------------


def test_an_unknown_tool_stops_the_whole_call(crib):
    before = state(crib)
    with pytest.raises(KeyError):
        crib.check_out_many(["hammer drill", "jigsaw", "mallet"], "ann")
    assert state(crib) == before


def test_a_tool_checked_out_to_someone_else_stops_the_whole_call(crib):
    crib.check_out("c-clamp", "bob")
    before = state(crib)
    with pytest.raises(KeyError):
        crib.check_out_many(["hammer drill", "jigsaw", "c-clamp"], "ann")
    assert state(crib) == before


def test_a_tool_the_person_already_has_stops_the_whole_call(crib):
    crib.check_out("jigsaw", "ann")
    before = state(crib)
    with pytest.raises(KeyError):
        crib.check_out_many(["drill press", "jigsaw"], "ann")
    assert state(crib) == before


def test_a_tool_named_twice_stops_the_whole_call(crib):
    before = state(crib)
    with pytest.raises(ValueError):
        crib.check_out_many(["hacksaw", "drill press", "hacksaw"], "ann")
    assert state(crib) == before


def test_an_empty_list_is_rejected(crib):
    before = state(crib)
    with pytest.raises(ValueError):
        crib.check_out_many([], "ann")
    assert state(crib) == before


def test_a_failed_call_can_be_retried_once_the_problem_is_gone(crib):
    crib.check_out("jigsaw", "bob")
    with pytest.raises(KeyError):
        crib.check_out_many(["hammer drill", "jigsaw"], "ann")
    crib.return_tool("jigsaw", "saws")
    crib.check_out_many(["hammer drill", "jigsaw"], "ann")
    assert crib.get_holder("jigsaw") == "ann"
    assert crib.get_tools("saws") == ["hacksaw"]
