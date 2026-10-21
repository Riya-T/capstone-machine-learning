"""Hidden tests for the c_kill_switch change (kill switch). Never shown to
the writer or the editor.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest changes/c_kill_switch/private/test_kill_switch_new.py
"""

import pytest
from flags import FlagStore


@pytest.fixture
def store():
    st = FlagStore()
    st.add_user("ann", 10)
    st.add_user("bob", 50)
    st.add_user("cat", 90)
    st.create_flag("dark_mode")
    st.create_flag("new_search")
    st.set_rollout("dark_mode", 60)
    st.enable_for_user("dark_mode", "cat")
    return st


def test_flags_start_alive(store):
    assert store.is_killed("dark_mode") is False
    assert store.is_killed("new_search") is False


def test_a_killed_flag_is_enabled_for_nobody(store):
    store.kill("dark_mode")
    assert store.is_killed("dark_mode") is True
    for user in ["ann", "bob", "cat"]:
        assert store.is_enabled("dark_mode", user) is False
    assert store.get_enabled_users("dark_mode") == []


def test_a_rollout_of_100_does_not_beat_the_kill_switch(store):
    store.set_rollout("new_search", 100)
    store.kill("new_search")
    assert store.get_enabled_users("new_search") == []


def test_reviving_restores_rollout_and_switches(store):
    store.kill("dark_mode")
    store.revive("dark_mode")
    assert store.is_killed("dark_mode") is False
    assert store.get_enabled_users("dark_mode") == ["ann", "bob", "cat"]
    assert store.is_enabled("dark_mode", "cat") is True


def test_killing_or_reviving_twice_is_harmless(store):
    store.kill("dark_mode")
    store.kill("dark_mode")
    assert store.is_killed("dark_mode") is True
    store.revive("dark_mode")
    store.revive("dark_mode")
    assert store.is_killed("dark_mode") is False
    assert store.get_enabled_users("dark_mode") == ["ann", "bob", "cat"]


def test_reviving_a_flag_that_was_never_killed_changes_nothing(store):
    store.revive("dark_mode")
    assert store.is_killed("dark_mode") is False
    assert store.get_enabled_users("dark_mode") == ["ann", "bob", "cat"]


def test_changes_made_while_killed_apply_after_revive(store):
    store.kill("new_search")
    store.set_rollout("new_search", 20)
    store.enable_for_user("new_search", "bob")
    assert store.get_enabled_users("new_search") == []
    store.revive("new_search")
    assert store.get_enabled_users("new_search") == ["ann", "bob"]


def test_killing_one_flag_leaves_the_others_alone(store):
    store.set_rollout("new_search", 100)
    store.kill("dark_mode")
    assert store.is_killed("new_search") is False
    assert store.get_enabled_users("new_search") == ["ann", "bob", "cat"]
    assert store.get_flags() == ["dark_mode", "new_search"]


@pytest.mark.parametrize("method", ["kill", "revive", "is_killed"])
def test_kill_switch_methods_reject_flags_that_do_not_exist(store, method):
    with pytest.raises(KeyError):
        getattr(store, method)("night_mode")
    with pytest.raises(KeyError):
        getattr(store, method)(None)
    assert store.get_enabled_users("dark_mode") == ["ann", "bob", "cat"]


def test_key_errors_still_apply_to_a_killed_flag(store):
    store.kill("dark_mode")
    with pytest.raises(KeyError):
        store.is_enabled("dark_mode", "dan")
    with pytest.raises(KeyError):
        store.is_enabled("night_mode", "ann")
