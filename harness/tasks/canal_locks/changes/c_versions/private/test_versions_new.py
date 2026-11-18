"""Hidden tests for the c_versions change (version numbers). Never shown to
the writer or the editor.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from canals import CanalError, CanalNetwork, VersionConflict


@pytest.fixture
def network():
    n = CanalNetwork()
    for name in ["upper", "middle", "lower", "basin"]:
        n.add_lock(name)
    n.connect("upper", "middle")
    n.connect("middle", "lower")
    n.connect("basin", "middle")
    n.connect("lower", "upper")
    return n  # version 8


def state(n):
    return [(lock, n.get_channels(lock)) for lock in n.get_locks()]


# --- counting -----------------------------------------------------------------


def test_a_new_network_is_at_version_0():
    assert CanalNetwork().get_version() == 0


def test_every_successful_change_counts_once(network):
    assert network.get_version() == 8
    network.disconnect("lower", "upper")
    assert network.get_version() == 9
    network.add_lock("weir")
    network.connect("weir", "basin")
    assert network.get_version() == 11
    assert network.merge_locks("basin", "lower") == 1
    assert network.get_version() == 12
    assert network.close_lock("weir") == 1
    assert network.get_version() == 13


def test_calls_that_change_little_still_count(network):
    network.add_lock("weir")
    assert network.close_lock("weir") == 0
    assert network.get_version() == 10
    assert network.merge_locks("basin", "upper") == 0
    assert network.get_version() == 11


def test_failed_calls_do_not_count(network):
    for call in (
        lambda: network.add_lock("upper"),
        lambda: network.connect("upper", "upper"),
        lambda: network.connect("upper", "weir"),
        lambda: network.disconnect("basin", "weir"),
        lambda: network.close_lock("weir"),
        lambda: network.merge_locks("weir", "upper"),
    ):
        with pytest.raises((KeyError, ValueError, CanalError)):
            call()
    assert network.get_version() == 8


def test_reading_does_not_count(network):
    network.get_locks()
    network.get_channels("middle")
    network.get_version()
    assert network.get_version() == 8


def test_networks_have_their_own_versions(network):
    other = CanalNetwork()
    other.add_lock("upper")
    assert other.get_version() == 1
    assert network.get_version() == 8


# --- expected_version ---------------------------------------------------------


def test_the_current_version_is_accepted_by_every_change(network):
    network.add_lock("weir", expected_version=8)
    network.connect("weir", "basin", expected_version=9)
    network.disconnect("upper", "lower", expected_version=10)
    assert network.merge_locks("basin", "upper", expected_version=11) == 1
    assert network.close_lock("weir", expected_version=12) == 1
    assert network.get_version() == 13
    assert state(network) == [
        ("upper", ["middle"]),
        ("middle", ["upper", "lower"]),
        ("lower", ["middle"]),
    ]


def test_none_means_no_check(network):
    network.connect("basin", "upper", expected_version=None)
    assert network.get_channels("basin") == ["middle", "upper"]
    assert network.get_version() == 9


@pytest.mark.parametrize(
    "call",
    [
        lambda n, v: n.add_lock("weir", expected_version=v),
        lambda n, v: n.connect("basin", "upper", expected_version=v),
        lambda n, v: n.disconnect("upper", "middle", expected_version=v),
        lambda n, v: n.close_lock("middle", expected_version=v),
        lambda n, v: n.merge_locks("middle", "basin", expected_version=v),
    ],
    ids=["add_lock", "connect", "disconnect", "close_lock", "merge_locks"],
)
@pytest.mark.parametrize("version", [7, 9, 0])
def test_any_other_version_is_refused_and_changes_nothing(network, call, version):
    before = state(network)
    with pytest.raises(VersionConflict):
        call(network, version)
    assert state(network) == before
    assert network.get_version() == 8


def test_a_version_read_before_another_change_is_stale(network):
    seen = network.get_version()
    network.disconnect("basin", "middle")  # someone else's change
    with pytest.raises(VersionConflict):
        network.close_lock("basin", expected_version=seen)
    assert network.get_locks() == ["upper", "middle", "lower", "basin"]
    network.close_lock("basin", expected_version=network.get_version())
    assert network.get_locks() == ["upper", "middle", "lower"]


def test_version_conflict_is_a_canal_error():
    assert issubclass(VersionConflict, CanalError)
