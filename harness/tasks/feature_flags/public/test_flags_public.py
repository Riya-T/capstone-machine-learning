"""Public checks for flags.py.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest public/test_flags_public.py
"""

import pytest
from flags import FlagStore


@pytest.fixture
def store():
    st = FlagStore()
    st.add_user("ann", 10)
    st.add_user("bob", 90)
    st.create_flag("dark_mode")
    return st


def test_a_new_flag_is_enabled_for_nobody(store):
    assert store.is_enabled("dark_mode", "ann") is False
    assert store.get_enabled_users("dark_mode") == []


def test_a_rollout_reaches_the_low_buckets(store):
    store.set_rollout("dark_mode", 50)
    assert store.is_enabled("dark_mode", "ann") is True
    assert store.is_enabled("dark_mode", "bob") is False


def test_switching_on_a_user_ignores_the_rollout(store):
    store.enable_for_user("dark_mode", "bob")
    assert store.is_enabled("dark_mode", "bob") is True
    assert store.is_enabled("dark_mode", "ann") is False


def test_enabled_users_follow_registration_order(store):
    store.enable_for_user("dark_mode", "bob")
    store.set_rollout("dark_mode", 20)
    assert store.get_enabled_users("dark_mode") == ["ann", "bob"]


def test_unknown_flag_raises_key_error(store):
    with pytest.raises(KeyError):
        store.is_enabled("night_mode", "ann")


def test_a_percent_over_100_raises_value_error(store):
    with pytest.raises(ValueError):
        store.set_rollout("dark_mode", 101)
