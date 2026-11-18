"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from canals import CanalError, CanalNetwork


@pytest.fixture
def network():
    n = CanalNetwork()
    for name in ["upper", "middle", "lower", "basin"]:
        n.add_lock(name)
    n.connect("upper", "middle")
    n.connect("middle", "lower")
    n.connect("basin", "middle")
    n.connect("lower", "upper")
    return n


def state(n):
    return [(lock, n.get_channels(lock)) for lock in n.get_locks()]


# --- each call can be undone --------------------------------------------------


def test_undo_of_a_connect(network):
    before = state(network)
    network.connect("basin", "upper")
    network.undo()
    assert state(network) == before
    network.connect("upper", "basin")
    assert network.get_channels("upper") == ["middle", "lower", "basin"]


def test_undo_of_a_disconnect_puts_the_channel_back_in_place(network):
    before = state(network)
    network.disconnect("upper", "middle")
    network.undo()
    assert state(network) == before
    assert network.get_channels("middle") == ["upper", "lower", "basin"]
    network.disconnect("middle", "upper")  # the channel is there again
    assert network.get_channels("middle") == ["lower", "basin"]
    assert network.get_channels("upper") == ["lower"]


def test_undo_of_close_lock_brings_back_every_channel_in_place(network):
    before = state(network)
    assert network.close_lock("middle") == 3
    network.undo()
    assert state(network) == before
    assert network.get_channels("upper") == ["middle", "lower"]
    assert network.get_channels("basin") == ["middle"]


def test_undo_of_close_lock_keeps_its_place_in_the_list(network):
    network.close_lock("upper")
    assert network.get_locks() == ["middle", "lower", "basin"]
    network.undo()
    assert network.get_locks() == ["upper", "middle", "lower", "basin"]
    assert network.get_channels("lower") == ["middle", "upper"]


def test_a_lock_brought_back_is_in_use_again(network):
    network.close_lock("lower")
    network.undo()
    with pytest.raises(CanalError):
        network.add_lock("lower")
    network.disconnect("lower", "middle")
    assert network.get_channels("lower") == ["upper"]
    assert network.close_lock("lower") == 1


def test_closing_a_lock_with_no_channels_can_be_undone(network):
    network.add_lock("weir")
    assert network.close_lock("weir") == 0
    network.undo()
    assert network.get_locks() == ["upper", "middle", "lower", "basin", "weir"]
    assert network.get_channels("weir") == []


def test_undo_of_merge_locks_restores_both_locks_and_every_list(network):
    network.add_lock("weir")
    network.connect("weir", "basin")
    before = state(network)
    assert network.merge_locks("basin", "lower") == 1
    network.undo()
    assert state(network) == before
    assert network.get_channels("lower") == ["middle", "upper"]
    assert network.get_channels("weir") == ["basin"]


def test_undo_of_a_merge_that_dropped_and_skipped_channels(network):
    before = state(network)
    assert network.merge_locks("middle", "upper") == 1
    network.undo()
    assert state(network) == before
    assert network.get_locks() == ["upper", "middle", "lower", "basin"]


def test_undo_of_a_merge_that_added_nothing(network):
    before = state(network)
    assert network.merge_locks("basin", "upper") == 0
    network.undo()
    assert state(network) == before


def test_a_merged_lock_brought_back_is_in_use_again(network):
    network.merge_locks("upper", "basin")
    network.undo()
    network.disconnect("upper", "lower")
    assert network.get_channels("upper") == ["middle"]
    assert network.get_channels("basin") == ["middle"]


def test_undo_of_add_lock_removes_it_and_frees_the_name(network):
    network.add_lock("weir")
    network.undo()
    assert network.get_locks() == ["upper", "middle", "lower", "basin"]
    with pytest.raises(KeyError):
        network.get_channels("weir")
    network.add_lock("weir")
    assert network.get_locks() == ["upper", "middle", "lower", "basin", "weir"]


def test_undo_through_a_name_that_was_closed_and_added_again(network):
    network.close_lock("basin")
    network.add_lock("basin")  # a new basin with no channels
    network.connect("basin", "upper")
    network.undo()  # the new channel
    network.undo()  # the new basin
    assert network.get_locks() == ["upper", "middle", "lower"]
    network.undo()  # the close: the old basin comes back
    assert network.get_channels("basin") == ["middle"]
    assert network.get_channels("middle") == ["upper", "lower", "basin"]
    assert network.get_channels("upper") == ["middle", "lower"]


# --- what is and is not recorded ----------------------------------------------


def test_each_undo_goes_one_call_further_back():
    n = CanalNetwork()
    calls = [
        lambda: n.add_lock("a"),
        lambda: n.add_lock("b"),
        lambda: n.add_lock("c"),
        lambda: n.connect("a", "b"),
        lambda: n.connect("c", "a"),
        lambda: n.add_lock("d"),
        lambda: n.connect("d", "b"),
        lambda: n.connect("c", "d"),
        lambda: n.disconnect("a", "b"),
        lambda: n.add_lock("e"),
        lambda: n.connect("e", "a"),
        lambda: n.merge_locks("c", "e"),
        lambda: n.connect("a", "b"),
        lambda: n.close_lock("d"),
        lambda: n.merge_locks("a", "b"),
        lambda: n.add_lock("a"),
    ]
    states = [state(n)]
    for call in calls:
        call()
        states.append(state(n))
    assert n.get_locks() == ["b", "e", "a"]
    assert n.get_channels("b") == ["e"]
    for expected in reversed(states[:-1]):
        n.undo()
        assert state(n) == expected
    with pytest.raises(CanalError):
        n.undo()
    assert n.get_locks() == []


def test_failed_calls_are_not_recorded(network):
    network.add_lock("weir")
    for call in (
        lambda: network.add_lock("upper"),
        lambda: network.connect("upper", "upper"),
        lambda: network.connect("upper", "gate"),
        lambda: network.disconnect("basin", "gate"),
        lambda: network.close_lock("gate"),
        lambda: network.merge_locks("middle", "middle"),
        lambda: network.merge_locks("gate", "middle"),
    ):
        with pytest.raises((KeyError, ValueError, CanalError)):
            call()
    network.undo()  # the weir
    assert network.get_locks() == ["upper", "middle", "lower", "basin"]
    assert network.get_channels("upper") == ["middle", "lower"]


def test_get_calls_are_not_recorded(network):
    network.disconnect("basin", "middle")
    network.get_channels("basin")
    network.get_locks()
    network.undo()
    assert network.get_channels("basin") == ["middle"]
    assert network.get_channels("upper") == ["middle", "lower"]


def test_there_is_no_redo():
    n = CanalNetwork()
    n.add_lock("a")
    n.add_lock("b")
    n.connect("a", "b")
    n.undo()
    n.undo()
    n.undo()
    assert n.get_locks() == []
    with pytest.raises(CanalError):
        n.undo()


def test_new_calls_after_an_undo_are_undone_first(network):
    network.close_lock("middle")
    network.undo()
    network.disconnect("lower", "middle")
    network.undo()
    assert network.get_channels("lower") == ["middle", "upper"]
    network.undo()  # the lower-upper channel from the fixture
    assert network.get_channels("lower") == ["middle"]
    assert network.get_channels("upper") == ["middle"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    n = CanalNetwork()
    with pytest.raises(CanalError):
        n.undo()
    n.add_lock("a")
    n.undo()
    with pytest.raises(CanalError):
        n.undo()
    assert n.get_locks() == []
    n.add_lock("a")
    n.add_lock("b")
    n.connect("a", "b")
    assert n.get_channels("a") == ["b"]


def test_the_whole_fixture_can_be_undone(network):
    for _ in range(8):
        network.undo()
    assert network.get_locks() == []
    with pytest.raises(CanalError):
        network.undo()
