"""Hidden tests for the c_groups change (user groups). Never shown to the
writer or the editor.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/private/test_groups_new.py
"""

import pytest
from flags import FlagError, FlagStore


@pytest.fixture
def store():
    st = FlagStore()
    st.add_user("ann", 10)
    st.add_user("bob", 50)
    st.add_user("cat", 90)
    st.create_flag("dark_mode")
    st.create_flag("new_search")
    st.create_group("design")
    st.create_group("support")
    st.add_to_group("design", "cat")
    st.add_to_group("design", "ann")
    return st


def state(st):
    return {name: st.get_enabled_users(name) for name in st.get_flags()}


def test_group_members_are_listed_in_joining_order(store):
    assert store.get_group_members("design") == ["cat", "ann"]
    assert store.get_group_members("support") == []
    store.add_to_group("support", "bob")
    store.add_to_group("support", "ann")
    assert store.get_group_members("support") == ["bob", "ann"]


def test_a_group_switch_enables_every_member(store):
    store.enable_for_group("dark_mode", "design")
    assert store.is_enabled("dark_mode", "cat") is True
    assert store.is_enabled("dark_mode", "ann") is True
    assert store.is_enabled("dark_mode", "bob") is False
    assert store.get_enabled_users("dark_mode") == ["ann", "cat"]
    store.set_rollout("dark_mode", 60)  # users outside the group follow the rollout
    assert store.get_enabled_users("dark_mode") == ["ann", "bob", "cat"]


def test_a_group_switch_applies_to_one_flag_only(store):
    store.enable_for_group("dark_mode", "design")
    assert store.get_enabled_users("new_search") == []
    assert store.is_enabled("new_search", "cat") is False


def test_members_added_after_the_group_switch_count(store):
    store.enable_for_group("new_search", "support")
    assert store.get_enabled_users("new_search") == []
    store.add_to_group("support", "bob")
    assert store.is_enabled("new_search", "bob") is True
    assert store.get_enabled_users("new_search") == ["bob"]


def test_each_enabled_user_is_listed_once_in_registration_order(store):
    store.add_to_group("support", "ann")
    store.enable_for_group("dark_mode", "design")
    store.enable_for_group("dark_mode", "support")
    store.enable_for_user("dark_mode", "cat")
    store.set_rollout("dark_mode", 20)
    assert store.get_enabled_users("dark_mode") == ["ann", "cat"]


def test_joining_or_switching_on_a_group_twice_is_harmless(store):
    store.add_to_group("design", "cat")
    assert store.get_group_members("design") == ["cat", "ann"]
    store.enable_for_group("dark_mode", "design")
    store.enable_for_group("dark_mode", "design")
    assert store.get_enabled_users("dark_mode") == ["ann", "cat"]


@pytest.mark.parametrize("bad_name", ["", None, 4])
def test_invalid_group_names_are_rejected(store, bad_name):
    with pytest.raises(ValueError):
        store.create_group(bad_name)
    with pytest.raises(KeyError):
        store.get_group_members(bad_name)


def test_creating_a_group_twice_is_rejected(store):
    with pytest.raises(FlagError):
        store.create_group("design")
    assert store.get_group_members("design") == ["cat", "ann"]


def test_a_group_may_share_a_name_with_a_flag_or_user(store):
    store.create_group("dark_mode")
    store.create_group("bob")
    store.add_to_group("bob", "ann")
    assert store.get_group_members("bob") == ["ann"]
    assert store.get_flags() == ["dark_mode", "new_search"]


@pytest.mark.parametrize(
    "call",
    [
        lambda st: st.add_to_group("sales", "ann"),
        lambda st: st.get_group_members("sales"),
        lambda st: st.enable_for_group("dark_mode", "sales"),
        lambda st: st.enable_for_group("dark_mode", None),
    ],
)
def test_groups_that_do_not_exist_raise_key_error(store, call):
    before = state(store)
    with pytest.raises(KeyError):
        call(store)
    assert state(store) == before


def test_adding_an_unregistered_user_to_a_group_raises_key_error(store):
    with pytest.raises(KeyError):
        store.add_to_group("design", "dan")
    assert store.get_group_members("design") == ["cat", "ann"]


def test_group_errors_come_in_the_stated_order(store):
    with pytest.raises(KeyError, match="sales"):
        store.add_to_group("sales", "dan")  # group before user
    with pytest.raises(KeyError, match="night_mode"):
        store.enable_for_group("night_mode", "sales")  # flag before group
