"""Hidden tests for the c_limits change (channel limits). Never shown to the
writer or the editor.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limits/private/test_limits_new.py
"""

import pytest
from canals import CanalError, CanalNetwork, TooManyChannels


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
    return [(lock, n.get_channels(lock), n.get_max_channels(lock)) for lock in n.get_locks()]


# --- setting a limit ----------------------------------------------------------


def test_every_lock_starts_without_a_limit(network):
    assert [network.get_max_channels(lock) for lock in network.get_locks()] == [None] * 4


def test_set_max_channels_replaces_the_limit(network):
    network.set_max_channels("upper", 5)
    assert network.get_max_channels("upper") == 5
    network.set_max_channels("upper", 2)
    assert network.get_max_channels("upper") == 2
    network.set_max_channels("upper", None)
    assert network.get_max_channels("upper") is None
    assert network.get_max_channels("lower") is None


def test_a_limit_equal_to_the_current_count_is_allowed(network):
    network.set_max_channels("middle", 3)
    assert network.get_max_channels("middle") == 3


@pytest.mark.parametrize("limit", [0, -1, 2.5, "3"])
def test_invalid_limits_are_rejected(network, limit):
    network.set_max_channels("basin", 4)
    with pytest.raises(ValueError):
        network.set_max_channels("basin", limit)
    assert network.get_max_channels("basin") == 4


def test_a_limit_below_the_current_count_is_rejected(network):
    before = state(network)
    with pytest.raises(ValueError):
        network.set_max_channels("middle", 2)
    assert state(network) == before


def test_locks_not_in_use_raise_key_error(network):
    network.close_lock("basin")
    for call in (
        lambda: network.set_max_channels("weir", 2),
        lambda: network.get_max_channels("weir"),
        lambda: network.set_max_channels("basin", 2),
        lambda: network.get_max_channels("basin"),
    ):
        with pytest.raises(KeyError):
            call()


def test_a_lock_added_again_does_not_keep_the_old_limit(network):
    network.set_max_channels("basin", 1)
    network.close_lock("basin")
    network.add_lock("basin")
    assert network.get_max_channels("basin") is None
    network.set_max_channels("upper", 4)
    network.merge_locks("upper", "lower")
    network.add_lock("upper")
    assert network.get_max_channels("upper") is None


def test_too_many_channels_is_a_canal_error():
    assert issubclass(TooManyChannels, CanalError)


# --- connect ------------------------------------------------------------------


def test_connect_is_rejected_when_either_lock_is_full(network):
    network.set_max_channels("basin", 1)
    before = state(network)
    with pytest.raises(TooManyChannels):
        network.connect("basin", "upper")
    with pytest.raises(TooManyChannels):
        network.connect("lower", "basin")
    assert state(network) == before


def test_connect_works_below_the_limit(network):
    network.set_max_channels("basin", 3)
    network.set_max_channels("upper", 3)
    network.connect("basin", "upper")
    assert network.get_channels("basin") == ["middle", "upper"]
    assert network.get_channels("upper") == ["middle", "lower", "basin"]
    network.add_lock("weir")
    with pytest.raises(TooManyChannels):
        network.connect("upper", "weir")
    network.connect("basin", "weir")
    assert network.get_channels("basin") == ["middle", "upper", "weir"]


def test_a_disconnect_makes_room_again(network):
    network.set_max_channels("middle", 3)
    network.add_lock("weir")
    with pytest.raises(TooManyChannels):
        network.connect("weir", "middle")
    network.disconnect("middle", "upper")
    network.connect("weir", "middle")
    assert network.get_channels("middle") == ["lower", "basin", "weir"]


def test_disconnect_and_close_lock_work_on_a_full_lock(network):
    network.set_max_channels("middle", 3)
    network.disconnect("basin", "middle")
    assert network.close_lock("middle") == 2
    assert network.get_locks() == ["upper", "lower", "basin"]


# --- merge_locks --------------------------------------------------------------


def test_a_merge_that_would_overfill_into_is_rejected(network):
    network.add_lock("weir")
    network.connect("weir", "basin")
    network.set_max_channels("lower", 2)
    before = state(network)
    # basin's channels to middle (already joined to lower) and weir (new)
    with pytest.raises(TooManyChannels):
        network.merge_locks("basin", "lower")
    assert state(network) == before


def test_a_merge_that_fills_into_exactly_is_allowed(network):
    network.add_lock("weir")
    network.connect("weir", "basin")
    network.set_max_channels("lower", 3)
    assert network.merge_locks("basin", "lower") == 1
    assert network.get_channels("lower") == ["middle", "upper", "weir"]


def test_the_dropped_channel_between_source_and_into_is_not_counted(network):
    network.set_max_channels("upper", 2)
    # middle: upper (dropped), lower (already joined to upper), basin (new)
    assert network.merge_locks("middle", "upper") == 1
    assert network.get_channels("upper") == ["lower", "basin"]


def test_only_the_limit_of_into_is_checked(network):
    network.set_max_channels("middle", 3)
    network.set_max_channels("lower", 2)
    network.add_lock("weir")
    network.connect("weir", "upper")
    network.set_max_channels("weir", 1)
    network.set_max_channels("upper", 3)
    # Every lock but basin is full. upper: middle (already joined to
    # basin), lower, weir.
    assert network.merge_locks("upper", "basin") == 2
    assert network.get_channels("basin") == ["middle", "lower", "weir"]
    assert network.get_channels("weir") == ["basin"]
