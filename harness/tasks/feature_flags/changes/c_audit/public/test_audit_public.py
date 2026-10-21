"""Public checks for the c_audit change (change audit). Shown to the editor,
never to the writer.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest changes/c_audit/public/test_audit_public.py
"""

import pytest
from flags import FlagStore


@pytest.fixture
def store():
    st = FlagStore()
    st.add_user("ann", 10)
    st.add_user("bob", 90)
    st.create_flag("dark_mode")
    st.create_flag("new_search")
    return st


def test_rollouts_and_user_switches_are_recorded_in_order(store):
    store.set_rollout("dark_mode", 20)
    store.enable_for_user("dark_mode", "bob")
    store.set_rollout("dark_mode", 50)
    assert store.get_audit("dark_mode") == [
        ("rollout", 20),
        ("enable_user", "bob"),
        ("rollout", 50),
    ]
    assert store.get_audit("new_search") == []


def test_the_audit_can_be_filtered_by_action(store):
    store.set_rollout("dark_mode", 20)
    store.enable_for_user("dark_mode", "bob")
    assert store.get_audit("dark_mode", action="rollout") == [("rollout", 20)]


def test_flags_for_user_lists_the_flags_enabled_for_that_user(store):
    store.set_rollout("dark_mode", 50)
    store.enable_for_user("new_search", "bob")
    assert store.get_flags_for_user("ann") == ["dark_mode"]
    assert store.get_flags_for_user("bob") == ["new_search"]
    assert store.get_changed_flags() == ["dark_mode", "new_search"]
