"""Public checks for the c_groups change (user groups). Shown to the editor,
never to the writer.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/public/test_groups_public.py
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
    st.create_group("design")
    st.add_to_group("design", "cat")
    return st


def test_switching_on_a_group_enables_its_members(store):
    store.enable_for_group("dark_mode", "design")
    assert store.is_enabled("dark_mode", "cat") is True
    assert store.is_enabled("dark_mode", "ann") is False
    assert store.get_enabled_users("dark_mode") == ["cat"]
    assert store.get_group_members("design") == ["cat"]


def test_members_joining_later_are_enabled_too(store):
    store.enable_for_group("dark_mode", "design")
    store.add_to_group("design", "ann")
    assert store.is_enabled("dark_mode", "ann") is True
    assert store.get_enabled_users("dark_mode") == ["ann", "cat"]


def test_a_group_that_does_not_exist_raises_key_error(store):
    with pytest.raises(KeyError):
        store.enable_for_group("dark_mode", "sales")
    with pytest.raises(KeyError):
        store.add_to_group("sales", "ann")
