"""Hidden tests for the c_lock change (locked bins). Never shown to the
writer or the editor.

Usage (with crib.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/private/test_lock_new.py
"""

import pytest
from crib import BinLocked, CribError, ToolCrib

BINS = ["drills", "saws", "clamps", "spare"]
TOOLS = ["hammer drill", "cordless drill", "drill press", "jigsaw", "hacksaw", "coping saw"]


@pytest.fixture
def crib():
    c = ToolCrib()
    for name in ["drills", "saws", "clamps"]:
        c.add_bin(name)
    for tool in ["hammer drill", "cordless drill", "drill press"]:
        c.add_tool("drills", tool)
    c.add_tool("saws", "jigsaw")
    c.add_tool("saws", "hacksaw")
    return c


def state(c):
    bins = {}
    for name in BINS:
        try:
            bins[name] = c.get_tools(name)
        except KeyError:
            bins[name] = None
    return bins, {t: c.get_holder(t) for t in TOOLS}


# --- locking and unlocking ----------------------------------------------------


def test_bin_locked_is_a_crib_error():
    assert issubclass(BinLocked, CribError)


def test_new_bins_are_unlocked(crib):
    crib.add_bin("spare")
    crib.add_tool("spare", "mallet")
    crib.check_out("mallet", "ann")
    crib.return_tool("mallet", "spare")
    assert crib.get_tools("spare") == ["mallet"]


def test_a_bin_added_again_under_a_closed_name_is_unlocked(crib):
    crib.lock_bin("clamps")
    crib.unlock_bin("clamps")
    crib.close_bin("clamps", "saws")
    crib.add_bin("clamps")
    crib.add_tool("clamps", "c-clamp")
    assert crib.get_tools("clamps") == ["c-clamp"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.lock_bin("spare"),
        lambda c: c.unlock_bin("spare"),
        lambda c: c.lock_bin("clamps"),  # closed below
        lambda c: c.unlock_bin("clamps"),
    ],
)
def test_bins_not_in_use_raise_key_error(crib, call):
    crib.close_bin("clamps", "saws")
    with pytest.raises(KeyError):
        call(crib)


def test_locking_twice_or_unlocking_an_unlocked_bin_raises(crib):
    with pytest.raises(CribError):
        crib.unlock_bin("saws")
    crib.lock_bin("saws")
    with pytest.raises(CribError):
        crib.lock_bin("saws")
    crib.unlock_bin("saws")
    crib.add_tool("saws", "coping saw")
    assert crib.get_tools("saws") == ["jigsaw", "hacksaw", "coping saw"]


def test_locking_changes_no_tools(crib):
    crib.check_out("jigsaw", "ann")
    before = state(crib)
    crib.lock_bin("saws")
    crib.lock_bin("drills")
    assert state(crib) == before


# --- single tools -------------------------------------------------------------


def test_add_tool_into_a_locked_bin_raises(crib):
    crib.lock_bin("saws")
    before = state(crib)
    with pytest.raises(BinLocked):
        crib.add_tool("saws", "coping saw")
    assert state(crib) == before
    crib.add_tool("clamps", "coping saw")
    assert crib.get_tools("clamps") == ["coping saw"]


def test_check_out_from_a_locked_bin_raises(crib):
    crib.lock_bin("drills")
    before = state(crib)
    with pytest.raises(BinLocked):
        crib.check_out("drill press", "ann")
    assert state(crib) == before
    crib.check_out("jigsaw", "ann")
    assert crib.get_holder("jigsaw") == "ann"


def test_return_into_a_locked_bin_raises_and_the_person_keeps_the_tool(crib):
    crib.check_out("cordless drill", "bob")
    crib.lock_bin("clamps")
    before = state(crib)
    with pytest.raises(BinLocked):
        crib.return_tool("cordless drill", "clamps")
    assert state(crib) == before
    crib.return_tool("cordless drill", "saws")
    assert crib.get_tools("saws") == ["jigsaw", "hacksaw", "cordless drill"]


def test_a_locked_bin_can_still_be_read(crib):
    crib.check_out("hacksaw", "ann")
    crib.lock_bin("saws")
    assert crib.get_tools("saws") == ["jigsaw"]
    assert crib.get_holder("hacksaw") == "ann"
    assert crib.get_holder("jigsaw") is None


# --- return_all and close_bin -------------------------------------------------


def test_return_all_into_a_locked_bin_returns_nothing(crib):
    crib.check_out("jigsaw", "ann")
    crib.check_out("hammer drill", "ann")
    crib.lock_bin("clamps")
    before = state(crib)
    with pytest.raises(BinLocked):
        crib.return_all("ann", "clamps")
    assert state(crib) == before
    assert crib.get_holder("jigsaw") == "ann"


def test_return_all_works_when_other_bins_are_locked(crib):
    crib.check_out("jigsaw", "ann")
    crib.check_out("drill press", "ann")
    crib.lock_bin("drills")
    crib.lock_bin("saws")
    assert crib.return_all("ann", "clamps") == 2
    assert crib.get_tools("clamps") == ["jigsaw", "drill press"]


def test_close_bin_from_a_locked_bin_raises(crib):
    crib.lock_bin("saws")
    before = state(crib)
    with pytest.raises(BinLocked):
        crib.close_bin("saws", "clamps")
    assert state(crib) == before


def test_close_bin_into_a_locked_bin_raises(crib):
    crib.lock_bin("clamps")
    before = state(crib)
    with pytest.raises(BinLocked):
        crib.close_bin("drills", "clamps")
    assert state(crib) == before


def test_closing_an_empty_locked_bin_raises(crib):
    crib.lock_bin("clamps")
    with pytest.raises(BinLocked):
        crib.close_bin("clamps", "saws")
    assert crib.get_tools("clamps") == []


def test_unlocking_lets_the_bin_be_closed(crib):
    crib.lock_bin("clamps")
    crib.unlock_bin("clamps")
    assert crib.close_bin("drills", "clamps") == 3
    assert crib.get_tools("clamps") == ["hammer drill", "cordless drill", "drill press"]


# --- undo -----------------------------------------------------------------------


def test_undoing_lock_bin_unlocks_the_bin(crib):
    crib.lock_bin("drills")
    crib.undo()
    crib.check_out("drill press", "ann")
    assert crib.get_holder("drill press") == "ann"


def test_undoing_unlock_bin_locks_the_bin_again(crib):
    crib.lock_bin("saws")
    crib.unlock_bin("saws")
    crib.undo()
    with pytest.raises(BinLocked):
        crib.add_tool("saws", "coping saw")
    crib.undo()
    crib.add_tool("saws", "coping saw")
    assert crib.get_tools("saws") == ["jigsaw", "hacksaw", "coping saw"]


def test_undo_of_a_tool_call_keeps_the_locks(crib):
    crib.lock_bin("saws")
    crib.check_out("hammer drill", "bob")
    crib.undo()
    assert crib.get_tools("drills") == ["hammer drill", "cordless drill", "drill press"]
    with pytest.raises(BinLocked):
        crib.check_out("jigsaw", "bob")


def test_failed_calls_on_locked_bins_are_not_recorded(crib):
    crib.check_out("jigsaw", "ann")
    crib.lock_bin("saws")
    for call in (
        lambda: crib.add_tool("saws", "coping saw"),
        lambda: crib.check_out("hacksaw", "bob"),
        lambda: crib.return_tool("jigsaw", "saws"),
        lambda: crib.return_all("ann", "saws"),
        lambda: crib.close_bin("drills", "saws"),
    ):
        with pytest.raises(BinLocked):
            call()
    crib.undo()  # the lock
    assert crib.return_all("ann", "saws") == 1
    assert crib.get_tools("saws") == ["hacksaw", "jigsaw"]
