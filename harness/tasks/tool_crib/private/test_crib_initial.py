"""Hidden tests for the initial tool_crib spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest private/test_crib_initial.py
"""

import pytest
from crib import CribError, ToolCrib

BINS = ["drills", "saws", "clamps", "spare"]
TOOLS = ["hammer drill", "cordless drill", "drill press", "jigsaw", "hacksaw"]


@pytest.fixture
def crib():
    c = ToolCrib()
    for name in ["drills", "saws", "clamps"]:
        c.add_bin(name)
    for tool in ["hammer drill", "cordless drill", "drill press"]:
        c.add_tool("drills", tool)
    for tool in ["jigsaw", "hacksaw"]:
        c.add_tool("saws", tool)
    return c


def state(c):
    """The tools of every bin (None for a bin not in use) and the holder of
    every tool, to check that a failed call changed nothing."""
    bins = {}
    for name in BINS:
        try:
            bins[name] = c.get_tools(name)
        except KeyError:
            bins[name] = None
    return bins, {t: c.get_holder(t) for t in TOOLS}


# --- bins and tools -----------------------------------------------------------


def test_a_new_bin_is_empty():
    c = ToolCrib()
    c.add_bin("drills")
    assert c.get_tools("drills") == []


def test_tools_keep_the_order_they_were_added_in(crib):
    crib.add_tool("clamps", "c-clamp")
    crib.add_tool("clamps", "bar clamp")
    crib.add_tool("drills", "angle drill")
    assert crib.get_tools("clamps") == ["c-clamp", "bar clamp"]
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press", "angle drill"]


def test_tools_in_bins_have_no_holder(crib):
    assert [crib.get_holder(t) for t in TOOLS] == [None] * 5


def test_adding_a_bin_name_in_use_is_rejected(crib):
    before = state(crib)
    with pytest.raises(CribError):
        crib.add_bin("saws")
    assert state(crib) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.add_tool("spare", "mallet"),
        lambda c: c.close_bin("spare", "saws"),
        lambda c: c.close_bin("saws", "spare"),
        lambda c: c.get_tools("spare"),
        lambda c: c.check_out("mallet", "ann"),
        lambda c: c.return_tool("jigsaw", "drills"),  # jigsaw is in a bin
    ],
)
def test_unknown_bins_and_tools_raise_key_error(crib, call):
    before = state(crib)
    with pytest.raises(KeyError):
        call(crib)
    assert state(crib) == before


# --- checking out and returning ----------------------------------------------


def test_check_out_takes_the_tool_out_of_its_bin(crib):
    crib.check_out("cordless drill", "ann")
    assert crib.get_tools("drills") == ["hammer drill", "drill press"]
    assert crib.get_holder("cordless drill") == "ann"
    assert crib.get_holder("hammer drill") is None


def test_a_returned_tool_goes_to_the_end_of_the_bin(crib):
    crib.check_out("hammer drill", "ann")
    crib.add_tool("drills", "angle drill")
    crib.return_tool("hammer drill", "drills")
    assert crib.get_tools("drills") == ["cordless drill", "drill press", "angle drill", "hammer drill"]
    assert crib.get_holder("hammer drill") is None


def test_a_tool_can_be_returned_to_any_bin(crib):
    crib.check_out("jigsaw", "ann")
    crib.return_tool("jigsaw", "clamps")
    assert crib.get_tools("clamps") == ["jigsaw"]
    assert crib.get_tools("saws") == ["hacksaw"]
    crib.check_out("jigsaw", "bob")
    assert crib.get_tools("clamps") == []
    assert crib.get_holder("jigsaw") == "bob"


def test_checking_out_a_checked_out_tool_changes_nothing(crib):
    crib.check_out("jigsaw", "ann")
    before = state(crib)
    with pytest.raises(KeyError):
        crib.check_out("jigsaw", "bob")
    with pytest.raises(KeyError):
        crib.check_out("jigsaw", "ann")
    assert state(crib) == before


def test_returning_a_tool_that_is_in_a_bin_changes_nothing(crib):
    before = state(crib)
    with pytest.raises(KeyError):
        crib.return_tool("hacksaw", "saws")
    assert state(crib) == before


def test_returning_to_a_bin_not_in_use_changes_nothing(crib):
    crib.check_out("jigsaw", "ann")
    before = state(crib)
    with pytest.raises(KeyError):
        crib.return_tool("jigsaw", "spare")
    with pytest.raises(KeyError):
        crib.return_all("ann", "spare")
    assert state(crib) == before


# --- return_all ---------------------------------------------------------------


def test_return_all_returns_in_the_order_checked_out(crib):
    crib.check_out("drill press", "ann")
    crib.check_out("jigsaw", "ann")
    crib.check_out("hammer drill", "ann")
    crib.check_out("hacksaw", "bob")
    assert crib.return_all("ann", "clamps") == 3
    assert crib.get_tools("clamps") == ["drill press", "jigsaw", "hammer drill"]
    assert [crib.get_holder(t) for t in ["drill press", "jigsaw", "hammer drill"]] == [None] * 3
    assert crib.get_holder("hacksaw") == "bob"


def test_return_all_appends_after_the_tools_in_the_bin(crib):
    crib.check_out("hacksaw", "cy")
    crib.check_out("cordless drill", "cy")
    assert crib.return_all("cy", "saws") == 2
    assert crib.get_tools("saws") == ["jigsaw", "hacksaw", "cordless drill"]
    assert crib.get_tools("drills") == ["hammer drill", "drill press"]


def test_people_keep_their_tools_apart(crib):
    crib.check_out("jigsaw", "ann")
    crib.check_out("hacksaw", "bob")
    crib.check_out("drill press", "ann")
    assert crib.return_all("bob", "clamps") == 1
    assert crib.return_all("ann", "clamps") == 2
    assert crib.get_tools("clamps") == ["hacksaw", "jigsaw", "drill press"]


# --- closing bins -------------------------------------------------------------


def test_close_bin_appends_the_tools_in_order(crib):
    crib.add_tool("clamps", "c-clamp")
    assert crib.close_bin("drills", "clamps") == 3
    assert crib.get_tools("clamps") == ["c-clamp", "hammer drill", "cordless drill", "drill press"]
    assert crib.get_tools("saws") == ["jigsaw", "hacksaw"]


def test_closing_an_empty_bin_moves_nothing(crib):
    assert crib.close_bin("clamps", "saws") == 0
    assert crib.get_tools("saws") == ["jigsaw", "hacksaw"]
    with pytest.raises(KeyError):
        crib.get_tools("clamps")


def test_moved_tools_can_be_checked_out_from_the_new_bin(crib):
    crib.close_bin("saws", "clamps")
    crib.check_out("jigsaw", "ann")
    assert crib.get_tools("clamps") == ["hacksaw"]
    assert crib.get_holder("jigsaw") == "ann"


def test_closing_a_bin_leaves_checked_out_tools_alone(crib):
    crib.check_out("jigsaw", "ann")
    assert crib.close_bin("saws", "drills") == 1
    assert crib.get_holder("jigsaw") == "ann"
    crib.return_tool("jigsaw", "drills")
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press", "hacksaw", "jigsaw"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.add_tool("saws", "mallet"),
        lambda c: c.close_bin("saws", "drills"),
        lambda c: c.close_bin("drills", "saws"),
        lambda c: c.get_tools("saws"),
    ],
)
def test_a_closed_bin_is_not_in_use(crib, call):
    crib.close_bin("saws", "clamps")
    before = state(crib)
    with pytest.raises(KeyError):
        call(crib)
    assert state(crib) == before


def test_a_closed_name_can_be_added_again_as_a_new_empty_bin(crib):
    crib.close_bin("drills", "clamps")
    crib.add_bin("drills")
    assert crib.get_tools("drills") == []
    crib.add_tool("drills", "angle drill")
    assert crib.get_tools("drills") == ["angle drill"]
    assert len(crib.get_tools("clamps")) == 3


def test_closing_a_bin_into_itself_raises(crib):
    before = state(crib)
    with pytest.raises(ValueError):
        crib.close_bin("drills", "drills")
    assert state(crib) == before


# --- general ------------------------------------------------------------------


def test_cribs_do_not_share_bins():
    first, second = ToolCrib(), ToolCrib()
    first.add_bin("drills")
    first.add_tool("drills", "hammer drill")
    second.add_bin("drills")
    assert second.get_tools("drills") == []
    second.add_tool("drills", "hammer drill")
    second.check_out("hammer drill", "ann")
    assert first.get_tools("drills") == ["hammer drill"]
    assert first.get_holder("hammer drill") is None
