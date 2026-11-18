"""Hidden tests for the initial canal_locks spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest private/test_canals_initial.py
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
    """Every lock in order with its channels in order, to check that a
    failed call changed nothing."""
    return [(lock, list(n.get_channels(lock))) for lock in list(n.get_locks())]


FIXTURE = [
    ("upper", ["middle", "lower"]),
    ("middle", ["upper", "lower", "basin"]),
    ("lower", ["middle", "upper"]),
    ("basin", ["middle"]),
]


# --- locks --------------------------------------------------------------------


def test_a_new_network_has_no_locks():
    assert CanalNetwork().get_locks() == []


def test_a_new_lock_has_no_channels():
    n = CanalNetwork()
    n.add_lock("upper")
    assert n.get_channels("upper") == []


def test_locks_are_listed_in_the_order_added():
    n = CanalNetwork()
    for name in ["weir", "upper", "basin"]:
        n.add_lock(name)
    assert n.get_locks() == ["weir", "upper", "basin"]


def test_adding_a_name_in_use_is_rejected(network):
    with pytest.raises(CanalError):
        network.add_lock("middle")
    assert state(network) == FIXTURE


NOT_IN_USE = [
    lambda n, x: n.connect("upper", x),
    lambda n, x: n.connect(x, "upper"),
    lambda n, x: n.disconnect(x, "middle"),
    lambda n, x: n.close_lock(x),
    lambda n, x: n.merge_locks(x, "upper"),
    lambda n, x: n.merge_locks("upper", x),
    lambda n, x: n.get_channels(x),
]


@pytest.mark.parametrize("call", NOT_IN_USE)
def test_locks_that_were_never_added_raise_key_error(network, call):
    with pytest.raises(KeyError):
        call(network, "weir")
    assert state(network) == FIXTURE


@pytest.mark.parametrize("call", NOT_IN_USE)
def test_a_closed_lock_is_not_in_use(network, call):
    network.close_lock("basin")
    before = state(network)
    with pytest.raises(KeyError):
        call(network, "basin")
    assert state(network) == before


@pytest.mark.parametrize("call", NOT_IN_USE)
def test_a_merged_lock_is_not_in_use(network, call):
    network.merge_locks("basin", "lower")
    before = state(network)
    with pytest.raises(KeyError):
        call(network, "basin")
    assert state(network) == before


def test_a_closed_name_can_be_added_again_as_a_new_lock(network):
    network.close_lock("middle")
    network.add_lock("middle")
    assert network.get_locks() == ["upper", "lower", "basin", "middle"]
    assert network.get_channels("middle") == []
    assert network.get_channels("upper") == ["lower"]


def test_a_merged_name_can_be_added_again_as_a_new_lock(network):
    network.merge_locks("basin", "upper")
    network.add_lock("basin")
    assert network.get_channels("basin") == []
    assert network.get_locks() == ["upper", "middle", "lower", "basin"]


# --- channels -----------------------------------------------------------------


def test_channels_are_listed_in_the_order_added_on_both_sides(network):
    assert state(network) == FIXTURE


def test_connect_lists_the_channel_last_on_both_sides(network):
    network.connect("basin", "lower")
    assert network.get_channels("basin") == ["middle", "lower"]
    assert network.get_channels("lower") == ["middle", "upper", "basin"]


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.connect("upper", "upper"),
        lambda n: n.disconnect("middle", "middle"),
        lambda n: n.merge_locks("lower", "lower"),
        lambda n: n.connect("basin", "basin"),
    ],
    ids=["connect", "disconnect", "merge_locks", "connect_basin"],
)
def test_the_same_lock_on_both_sides_is_rejected(network, call):
    with pytest.raises(ValueError):
        call(network)
    assert state(network) == FIXTURE


def test_disconnect_removes_the_channel_on_both_sides(network):
    network.disconnect("middle", "upper")
    assert network.get_channels("middle") == ["lower", "basin"]
    assert network.get_channels("upper") == ["lower"]


def test_disconnect_takes_the_locks_in_either_order(network):
    network.disconnect("lower", "middle")
    assert network.get_channels("middle") == ["upper", "basin"]
    assert network.get_channels("lower") == ["upper"]


def test_disconnecting_the_only_channel_leaves_none(network):
    network.disconnect("basin", "middle")
    assert network.get_channels("basin") == []
    assert network.get_channels("middle") == ["upper", "lower"]


def test_a_channel_added_again_is_listed_last(network):
    network.disconnect("upper", "middle")
    network.connect("upper", "middle")
    assert network.get_channels("upper") == ["lower", "middle"]
    assert network.get_channels("middle") == ["lower", "basin", "upper"]


# --- closing ------------------------------------------------------------------


def test_close_lock_removes_every_channel_and_the_lock(network):
    assert network.close_lock("middle") == 3
    assert state(network) == [
        ("upper", ["lower"]),
        ("lower", ["upper"]),
        ("basin", []),
    ]


def test_closing_a_lock_with_no_channels_removes_nothing_else(network):
    network.add_lock("weir")
    assert network.close_lock("weir") == 0
    assert state(network) == FIXTURE


def test_the_other_locks_keep_their_order_after_a_close(network):
    network.close_lock("upper")
    assert network.get_locks() == ["middle", "lower", "basin"]
    assert network.get_channels("middle") == ["lower", "basin"]


# --- merging ------------------------------------------------------------------


def test_merge_moves_new_channels_to_the_end_of_both_lists(network):
    network.add_lock("weir")
    network.connect("weir", "basin")
    # basin: middle, weir
    assert network.merge_locks("basin", "lower") == 1
    assert state(network) == [
        ("upper", ["middle", "lower"]),
        ("middle", ["upper", "lower"]),
        ("lower", ["middle", "upper", "weir"]),
        ("weir", ["lower"]),
    ]


def test_merge_skips_locks_already_joined_to_into(network):
    assert network.merge_locks("basin", "upper") == 0
    assert state(network) == [
        ("upper", ["middle", "lower"]),
        ("middle", ["upper", "lower"]),
        ("lower", ["middle", "upper"]),
    ]


def test_merge_drops_the_channel_between_source_and_into(network):
    assert network.merge_locks("middle", "upper") == 1
    assert state(network) == [
        ("upper", ["lower", "basin"]),
        ("lower", ["upper"]),
        ("basin", ["upper"]),
    ]


def test_merge_adds_channels_in_the_order_source_lists_them():
    n = CanalNetwork()
    for name in ["a", "b", "c", "d", "e"]:
        n.add_lock(name)
    n.connect("a", "d")
    n.connect("a", "c")
    n.connect("b", "e")
    n.connect("c", "e")
    assert n.merge_locks("a", "b") == 2
    assert state(n) == [
        ("b", ["e", "d", "c"]),
        ("c", ["e", "b"]),
        ("d", ["b"]),
        ("e", ["b", "c"]),
    ]


def test_merging_a_lock_with_no_channels_just_removes_it(network):
    network.add_lock("weir")
    assert network.merge_locks("weir", "basin") == 0
    assert state(network) == FIXTURE


# --- general ------------------------------------------------------------------


def test_networks_do_not_share_locks():
    first, second = CanalNetwork(), CanalNetwork()
    first.add_lock("upper")
    first.add_lock("lower")
    first.connect("upper", "lower")
    assert second.get_locks() == []
    second.add_lock("upper")
    assert second.get_channels("upper") == []
