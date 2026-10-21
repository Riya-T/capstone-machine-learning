"""Hidden tests for the c_audit change (change audit). Never shown to the
writer or the editor.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest changes/c_audit/private/test_audit_new.py
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
    st.create_flag("beta_ui")
    return st


def test_a_new_flag_has_an_empty_audit(store):
    assert store.get_audit("dark_mode") == []
    assert store.get_audit("dark_mode", action="rollout") == []
    assert store.get_changed_flags() == []


def test_every_rollout_change_is_recorded_oldest_first(store):
    store.set_rollout("dark_mode", 10)
    store.set_rollout("dark_mode", 80)
    store.set_rollout("dark_mode", 0)
    store.set_rollout("dark_mode", 0)  # the same percent again is recorded again
    assert store.get_audit("dark_mode") == [
        ("rollout", 10),
        ("rollout", 80),
        ("rollout", 0),
        ("rollout", 0),
    ]


def test_a_user_switch_is_recorded_only_the_first_time(store):
    store.enable_for_user("dark_mode", "cat")
    store.enable_for_user("dark_mode", "cat")
    store.enable_for_user("dark_mode", "ann")
    assert store.get_audit("dark_mode") == [("enable_user", "cat"), ("enable_user", "ann")]


def test_rollouts_and_switches_are_interleaved_in_call_order(store):
    store.enable_for_user("dark_mode", "bob")
    store.set_rollout("dark_mode", 40)
    store.enable_for_user("dark_mode", "cat")
    assert store.get_audit("dark_mode") == [
        ("enable_user", "bob"),
        ("rollout", 40),
        ("enable_user", "cat"),
    ]


def test_calls_that_raise_are_not_recorded(store):
    store.set_rollout("dark_mode", 40)
    for call in (
        lambda: store.set_rollout("dark_mode", 101),
        lambda: store.set_rollout("dark_mode", "50"),
        lambda: store.enable_for_user("dark_mode", "dan"),
        lambda: store.enable_for_user("night_mode", "ann"),
    ):
        with pytest.raises((ValueError, KeyError)):
            call()
    assert store.get_audit("dark_mode") == [("rollout", 40)]
    assert store.get_changed_flags() == ["dark_mode"]


def test_audits_are_kept_per_flag(store):
    store.set_rollout("dark_mode", 40)
    store.enable_for_user("new_search", "ann")
    assert store.get_audit("dark_mode") == [("rollout", 40)]
    assert store.get_audit("new_search") == [("enable_user", "ann")]
    assert store.get_audit("beta_ui") == []


def test_filtering_by_action_keeps_the_order(store):
    store.enable_for_user("dark_mode", "bob")
    store.set_rollout("dark_mode", 40)
    store.enable_for_user("dark_mode", "cat")
    store.set_rollout("dark_mode", 70)
    assert store.get_audit("dark_mode", action="enable_user") == [
        ("enable_user", "bob"),
        ("enable_user", "cat"),
    ]
    assert store.get_audit("dark_mode", action="rollout") == [("rollout", 40), ("rollout", 70)]
    assert store.get_audit("dark_mode", action="deleted") == []


def test_audit_of_a_flag_that_does_not_exist_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_audit("night_mode")
    with pytest.raises(KeyError):
        store.get_audit("night_mode", action="rollout")
    with pytest.raises(KeyError):
        store.get_audit(None)


def test_flags_for_user_follow_flag_creation_order(store):
    store.enable_for_user("beta_ui", "cat")
    store.set_rollout("new_search", 100)
    store.set_rollout("dark_mode", 20)
    assert store.get_flags_for_user("cat") == ["new_search", "beta_ui"]
    assert store.get_flags_for_user("ann") == ["dark_mode", "new_search"]
    assert store.get_flags_for_user("bob") == ["new_search"]


def test_flags_for_user_reflects_later_changes(store):
    store.set_rollout("dark_mode", 100)
    assert store.get_flags_for_user("bob") == ["dark_mode"]
    store.set_rollout("dark_mode", 0)
    assert store.get_flags_for_user("bob") == []


def test_flags_for_an_unregistered_user_raise_key_error(store):
    with pytest.raises(KeyError):
        store.get_flags_for_user("dan")
    with pytest.raises(KeyError):
        store.get_flags_for_user(1)


def test_changed_flags_follow_creation_order(store):
    store.enable_for_user("beta_ui", "ann")
    store.set_rollout("dark_mode", 5)
    assert store.get_changed_flags() == ["dark_mode", "beta_ui"]
