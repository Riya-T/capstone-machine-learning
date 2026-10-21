"""Public checks for the c_kill_switch change (kill switch). Shown to the
editor, never to the writer.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest changes/c_kill_switch/public/test_kill_switch_public.py
"""

import pytest
from flags import FlagStore


@pytest.fixture
def store():
    st = FlagStore()
    st.add_user("ann", 10)
    st.add_user("bob", 90)
    st.create_flag("dark_mode")
    st.set_rollout("dark_mode", 50)
    st.enable_for_user("dark_mode", "bob")
    return st


def test_a_killed_flag_is_off_for_everybody(store):
    store.kill("dark_mode")
    assert store.is_killed("dark_mode") is True
    assert store.is_enabled("dark_mode", "ann") is False
    assert store.is_enabled("dark_mode", "bob") is False
    assert store.get_enabled_users("dark_mode") == []


def test_reviving_brings_the_old_settings_back(store):
    store.kill("dark_mode")
    store.revive("dark_mode")
    assert store.is_killed("dark_mode") is False
    assert store.get_enabled_users("dark_mode") == ["ann", "bob"]


def test_killing_a_flag_that_does_not_exist_raises_key_error(store):
    with pytest.raises(KeyError):
        store.kill("night_mode")
