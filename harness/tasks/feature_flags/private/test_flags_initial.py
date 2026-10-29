"""Hidden tests for the initial feature_flags spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with flags.py importable, e.g. in the sandbox):
    python -m pytest private/test_flags_initial.py
"""

import pytest
from flags import FlagError, FlagStore

BAD_NAMES = ["", None, 7]
BAD_BUCKETS = [-1, 100, 2.5, "10", None]
BAD_PERCENTS = [-1, 101, 2.5, "50", None]


@pytest.fixture
def store():
    st = FlagStore()
    st.add_user("ann", 10)
    st.add_user("bob", 50)
    st.add_user("cat", 90)
    st.create_flag("dark_mode")
    st.create_flag("new_search")
    return st


def state(st):
    """Every flag's enabled users, to check that a failed call changed nothing."""
    return {name: st.get_enabled_users(name) for name in st.get_flags()}


# --- users ------------------------------------------------------------------


@pytest.mark.parametrize("bad_id", BAD_NAMES)
def test_invalid_user_ids_are_rejected(store, bad_id):
    with pytest.raises(ValueError):
        store.add_user(bad_id, 5)
    store.set_rollout("dark_mode", 100)
    assert store.get_enabled_users("dark_mode") == ["ann", "bob", "cat"]


@pytest.mark.parametrize("bucket", BAD_BUCKETS)
def test_invalid_buckets_are_rejected(store, bucket):
    with pytest.raises(ValueError):
        store.add_user("dan", bucket)
    with pytest.raises(KeyError):
        store.is_enabled("dark_mode", "dan")


def test_registering_a_user_twice_is_rejected(store):
    store.set_rollout("dark_mode", 20)
    with pytest.raises(FlagError):
        store.add_user("ann", 95)
    assert store.is_enabled("dark_mode", "ann") is True
    assert store.get_enabled_users("dark_mode") == ["ann"]


def test_buckets_0_and_99_are_valid():
    st = FlagStore()
    st.add_user("low", 0)
    st.add_user("high", 99)
    st.create_flag("f")
    st.set_rollout("f", 1)
    assert st.get_enabled_users("f") == ["low"]
    st.set_rollout("f", 100)
    assert st.get_enabled_users("f") == ["low", "high"]


@pytest.mark.parametrize(
    "call",
    [
        lambda st: st.enable_for_user("dark_mode", "dan"),
        lambda st: st.is_enabled("dark_mode", "dan"),
        lambda st: st.enable_for_user("dark_mode", None),
        lambda st: st.is_enabled("dark_mode", 1),
    ],
)
def test_users_that_are_not_registered_raise_key_error(store, call):
    store.set_rollout("dark_mode", 60)
    before = state(store)
    with pytest.raises(KeyError):
        call(store)
    assert state(store) == before


# --- flags ------------------------------------------------------------------


def test_flags_are_listed_in_creation_order():
    st = FlagStore()
    for name in ["zeta", "alpha", "mid"]:
        st.create_flag(name)
    assert st.get_flags() == ["zeta", "alpha", "mid"]


@pytest.mark.parametrize("bad_name", BAD_NAMES)
def test_invalid_flag_names_are_rejected(store, bad_name):
    with pytest.raises(ValueError):
        store.create_flag(bad_name)
    assert store.get_flags() == ["dark_mode", "new_search"]


def test_creating_a_flag_twice_is_rejected(store):
    store.set_rollout("dark_mode", 100)
    store.enable_for_user("new_search", "cat")
    before = state(store)
    with pytest.raises(FlagError):
        store.create_flag("dark_mode")
    assert store.get_flags() == ["dark_mode", "new_search"]
    assert state(store) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda st: st.set_rollout("night_mode", 10),
        lambda st: st.enable_for_user("night_mode", "ann"),
        lambda st: st.is_enabled("night_mode", "ann"),
        lambda st: st.get_enabled_users("night_mode"),
        lambda st: st.get_enabled_users(None),
        lambda st: st.is_enabled(1, "ann"),
    ],
)
def test_flags_that_do_not_exist_raise_key_error(store, call):
    store.set_rollout("dark_mode", 60)
    before = state(store)
    with pytest.raises(KeyError):
        call(store)
    assert state(store) == before
    assert store.get_flags() == ["dark_mode", "new_search"]


# --- rollouts ---------------------------------------------------------------


def test_a_rollout_covers_buckets_below_the_percent():
    st = FlagStore()
    st.add_user("u0", 0)
    st.add_user("u29", 29)
    st.add_user("u30", 30)
    st.add_user("u99", 99)
    st.create_flag("f")
    st.set_rollout("f", 30)
    assert st.is_enabled("f", "u0") is True
    assert st.is_enabled("f", "u29") is True
    assert st.is_enabled("f", "u30") is False
    assert st.is_enabled("f", "u99") is False
    assert st.get_enabled_users("f") == ["u0", "u29"]


def test_rollout_zero_reaches_nobody_and_hundred_everybody(store):
    store.set_rollout("dark_mode", 0)
    assert store.get_enabled_users("dark_mode") == []
    store.set_rollout("dark_mode", 100)
    assert store.get_enabled_users("dark_mode") == ["ann", "bob", "cat"]


def test_set_rollout_replaces_the_previous_percent(store):
    store.set_rollout("dark_mode", 100)
    store.set_rollout("dark_mode", 60)
    assert store.get_enabled_users("dark_mode") == ["ann", "bob"]
    store.set_rollout("dark_mode", 5)
    assert store.get_enabled_users("dark_mode") == []


def test_users_registered_after_the_rollout_are_covered(store):
    store.set_rollout("dark_mode", 40)
    store.add_user("dan", 39)
    store.add_user("eve", 40)
    assert store.is_enabled("dark_mode", "dan") is True
    assert store.is_enabled("dark_mode", "eve") is False
    assert store.get_enabled_users("dark_mode") == ["ann", "dan"]


@pytest.mark.parametrize("percent", BAD_PERCENTS)
def test_invalid_percents_are_rejected(store, percent):
    store.set_rollout("dark_mode", 60)
    before = state(store)
    with pytest.raises(ValueError):
        store.set_rollout("dark_mode", percent)
    assert state(store) == before


def test_rollouts_are_per_flag(store):
    store.set_rollout("dark_mode", 100)
    assert store.get_enabled_users("new_search") == []
    assert store.is_enabled("new_search", "ann") is False


# --- switching on single users -----------------------------------------------


def test_a_switched_on_user_is_enabled_whatever_the_rollout(store):
    store.enable_for_user("dark_mode", "cat")
    assert store.is_enabled("dark_mode", "cat") is True
    assert store.is_enabled("dark_mode", "ann") is False
    store.set_rollout("dark_mode", 0)
    assert store.is_enabled("dark_mode", "cat") is True


def test_switching_on_a_user_twice_is_harmless(store):
    store.enable_for_user("dark_mode", "bob")
    store.enable_for_user("dark_mode", "bob")
    assert store.get_enabled_users("dark_mode") == ["bob"]


def test_switches_are_per_flag(store):
    store.enable_for_user("dark_mode", "bob")
    assert store.is_enabled("new_search", "bob") is False
    assert store.get_enabled_users("new_search") == []


def test_enabled_users_mix_switches_and_rollout_in_registration_order(store):
    store.enable_for_user("dark_mode", "cat")
    store.set_rollout("dark_mode", 20)
    assert store.get_enabled_users("dark_mode") == ["ann", "cat"]
    store.enable_for_user("dark_mode", "ann")  # already covered by the rollout
    assert store.get_enabled_users("dark_mode") == ["ann", "cat"]


def test_is_enabled_returns_real_bools(store):
    store.set_rollout("dark_mode", 20)
    assert store.is_enabled("dark_mode", "ann") is True
    assert store.is_enabled("dark_mode", "cat") is False


# --- error order ------------------------------------------------------------


def test_a_missing_flag_is_reported_before_a_bad_percent(store):
    with pytest.raises(KeyError):
        store.set_rollout("night_mode", -1)


def test_stores_do_not_share_users_or_flags():
    first, second = FlagStore(), FlagStore()
    first.add_user("ann", 1)
    first.create_flag("f")
    assert second.get_flags() == []
    second.create_flag("f")
    with pytest.raises(KeyError):
        second.is_enabled("f", "ann")
