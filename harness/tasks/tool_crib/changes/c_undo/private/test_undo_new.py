"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from crib import CribError, ToolCrib

BINS = ["drills", "saws", "clamps", "spare"]
TOOLS = ["hammer drill", "cordless drill", "drill press", "jigsaw", "hacksaw", "mallet", "chisel"]


@pytest.fixture
def crib():
    c = ToolCrib()
    for name in ["drills", "saws", "clamps"]:
        c.add_bin(name)
    for tool in ["hammer drill", "cordless drill", "drill press"]:
        c.add_tool("drills", tool)
    c.add_tool("saws", "jigsaw")
    return c


def state(c):
    bins = {}
    for name in BINS:
        try:
            bins[name] = c.get_tools(name)
        except KeyError:
            bins[name] = None
    return bins, {t: c.get_holder(t) for t in TOOLS}


# --- each call can be undone ------------------------------------------------


def test_undoing_a_check_out_puts_the_tool_back_in_its_old_place(crib):
    before = state(crib)
    crib.check_out("cordless drill", "ann")
    crib.undo()
    assert state(crib) == before
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press"]


def test_undoing_a_return_gives_the_tool_back(crib):
    crib.check_out("jigsaw", "bob")
    before = state(crib)
    crib.return_tool("jigsaw", "drills")
    crib.undo()
    assert state(crib) == before
    assert crib.get_holder("jigsaw") == "bob"
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press"]


def test_one_undo_takes_back_a_whole_return_all(crib):
    crib.check_out("hammer drill", "ann")
    crib.check_out("jigsaw", "ann")
    crib.check_out("drill press", "ann")
    crib.check_out("cordless drill", "bob")
    before = state(crib)
    assert crib.return_all("ann", "clamps") == 3
    crib.undo()
    assert state(crib) == before
    assert crib.get_tools("clamps") == []
    assert [crib.get_holder(t) for t in ["hammer drill", "jigsaw", "drill press"]] == ["ann"] * 3


def test_an_undone_return_all_keeps_the_checkout_order(crib):
    crib.check_out("drill press", "ann")
    crib.check_out("jigsaw", "ann")
    crib.check_out("hammer drill", "ann")
    crib.return_all("ann", "saws")
    crib.undo()
    assert crib.return_all("ann", "clamps") == 3
    assert crib.get_tools("clamps") == ["drill press", "jigsaw", "hammer drill"]


def test_an_undone_return_keeps_the_checkout_order(crib):
    crib.check_out("drill press", "ann")
    crib.check_out("jigsaw", "ann")
    crib.check_out("hammer drill", "ann")
    crib.return_tool("drill press", "saws")
    crib.undo()
    crib.return_all("ann", "clamps")
    assert crib.get_tools("clamps") == ["drill press", "jigsaw", "hammer drill"]


def test_one_undo_takes_back_a_whole_close_bin(crib):
    crib.add_tool("clamps", "c-clamp")
    before = state(crib)
    assert crib.close_bin("drills", "clamps") == 3
    crib.undo()
    assert state(crib) == before
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press"]
    assert crib.get_tools("clamps") == ["c-clamp"]


def test_a_bin_brought_back_is_in_use_again(crib):
    crib.close_bin("saws", "clamps")
    crib.undo()
    with pytest.raises(CribError):
        crib.add_bin("saws")
    crib.add_tool("saws", "hacksaw")
    assert crib.get_tools("saws") == ["jigsaw", "hacksaw"]
    crib.check_out("jigsaw", "ann")
    assert crib.get_tools("saws") == ["hacksaw"]


def test_closing_an_empty_bin_can_be_undone(crib):
    assert crib.close_bin("clamps", "saws") == 0
    crib.undo()
    assert crib.get_tools("clamps") == []
    assert crib.get_tools("saws") == ["jigsaw"]


def test_undoing_add_bin_removes_it_and_frees_the_name(crib):
    crib.add_bin("spare")
    crib.undo()
    with pytest.raises(KeyError):
        crib.get_tools("spare")
    crib.add_bin("spare")
    assert crib.get_tools("spare") == []


def test_undoing_add_tool_removes_it_and_frees_the_name(crib):
    crib.add_tool("saws", "hacksaw")
    crib.undo()
    assert crib.get_tools("saws") == ["jigsaw"]
    with pytest.raises(KeyError):
        crib.check_out("hacksaw", "ann")
    crib.add_tool("clamps", "hacksaw")
    assert crib.get_tools("clamps") == ["hacksaw"]


def test_undo_through_a_name_that_was_closed_and_added_again(crib):
    crib.add_bin("spare")
    crib.add_tool("spare", "mallet")
    crib.close_bin("spare", "clamps")
    crib.add_bin("spare")  # a new, empty spare
    crib.add_tool("spare", "chisel")
    crib.undo()  # the chisel
    crib.undo()  # the new spare
    with pytest.raises(KeyError):
        crib.get_tools("spare")
    crib.undo()  # the close: the old spare comes back with its mallet
    assert crib.get_tools("spare") == ["mallet"]
    assert crib.get_tools("clamps") == []
    crib.undo()  # the mallet
    crib.undo()  # the first spare
    with pytest.raises(KeyError):
        crib.get_tools("spare")


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    c = ToolCrib()
    calls = [
        lambda: c.add_bin("drills"),
        lambda: c.add_bin("saws"),
        lambda: c.add_tool("drills", "hammer drill"),
        lambda: c.add_tool("saws", "jigsaw"),
        lambda: c.add_tool("drills", "drill press"),
        lambda: c.check_out("hammer drill", "ann"),
        lambda: c.check_out("jigsaw", "ann"),
        lambda: c.check_out("drill press", "bob"),
        lambda: c.return_tool("hammer drill", "saws"),
        lambda: c.add_bin("clamps"),
        lambda: c.check_out("hammer drill", "ann"),
        lambda: c.return_all("ann", "clamps"),
        lambda: c.return_all("bob", "drills"),
        lambda: c.close_bin("drills", "clamps"),
        lambda: c.close_bin("saws", "clamps"),
    ]
    states = [state(c)]
    for call in calls:
        call()
        states.append(state(c))
    assert c.get_tools("clamps") == ["jigsaw", "hammer drill", "drill press"]
    for expected in reversed(states[:-1]):
        c.undo()
        assert state(c) == expected
    with pytest.raises(CribError):
        c.undo()


def test_failed_calls_are_not_recorded(crib):
    crib.check_out("jigsaw", "ann")
    for call in (
        lambda: crib.add_bin("drills"),
        lambda: crib.add_tool("spare", "mallet"),
        lambda: crib.check_out("jigsaw", "bob"),
        lambda: crib.check_out("mallet", "bob"),
        lambda: crib.return_tool("hammer drill", "saws"),
        lambda: crib.return_tool("jigsaw", "spare"),
        lambda: crib.return_all("ann", "spare"),
        lambda: crib.close_bin("saws", "spare"),
        lambda: crib.close_bin("drills", "drills"),
    ):
        with pytest.raises((CribError, KeyError, ValueError)):
            call()
    crib.undo()  # the check_out of the jigsaw
    assert crib.get_tools("saws") == ["jigsaw"]
    assert crib.get_holder("jigsaw") is None


def test_get_calls_are_not_recorded(crib):
    crib.check_out("jigsaw", "ann")
    crib.get_tools("saws")
    crib.get_holder("jigsaw")
    crib.undo()
    assert crib.get_holder("jigsaw") is None
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press"]


def test_new_calls_after_an_undo_are_undone_first(crib):
    crib.check_out("jigsaw", "ann")
    crib.undo()
    crib.check_out("drill press", "bob")
    crib.undo()
    assert crib.get_holder("drill press") is None
    crib.undo()  # the jigsaw added in the fixture
    assert crib.get_tools("saws") == []
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press"]


def test_there_is_no_redo():
    c = ToolCrib()
    c.add_bin("drills")
    c.add_tool("drills", "hammer drill")
    c.undo()
    c.undo()
    with pytest.raises(KeyError):
        c.get_tools("drills")
    with pytest.raises(CribError):
        c.undo()


def test_nothing_left_to_undo_raises_and_changes_nothing():
    c = ToolCrib()
    with pytest.raises(CribError):
        c.undo()
    c.add_bin("drills")
    c.undo()
    with pytest.raises(CribError):
        c.undo()
    c.add_bin("drills")
    c.add_tool("drills", "hammer drill")
    assert c.get_tools("drills") == ["hammer drill"]


def test_the_whole_fixture_can_be_undone(crib):
    for _ in range(7):
        crib.undo()
    for name in ["drills", "saws", "clamps"]:
        with pytest.raises(KeyError):
            crib.get_tools(name)
    with pytest.raises(CribError):
        crib.undo()


def test_undo_restores_what_a_later_call_checks(crib):
    crib.check_out("jigsaw", "ann")
    crib.return_all("ann", "drills")
    crib.undo()
    with pytest.raises(KeyError):
        crib.check_out("jigsaw", "bob")  # the jigsaw is out again
    assert crib.return_all("ann", "saws") == 1
    assert crib.get_tools("saws") == ["jigsaw"]
