"""Hidden tests for the initial lru_cache spec. They decide whether a program
is correct to begin with. Never shown to the writer or the editor.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest private/test_cache_initial.py
"""

import pytest
from cache import Cache

BAD_KEYS = ["", None, 5]
BAD_VALUES = ["1", 1.5, None, [1]]


@pytest.fixture
def cache():
    cac = Cache(3)
    cac.put("a", 1)
    cac.put("b", 2)
    cac.put("c", 3)
    return cac


def state(cac):
    """Keys in recency order plus their values, read least recent first so
    the reads leave the order unchanged. Checks that a failed call changed nothing."""
    keys = cac.get_keys()
    values = [cac.get(k) for k in reversed(keys)]
    return keys, values, cac.get_size()


# --- capacity ---------------------------------------------------------------


def test_a_new_cache_is_empty():
    cac = Cache(4)
    assert cac.get_keys() == []
    assert cac.get_size() == 0
    assert cac.get_capacity() == 4


@pytest.mark.parametrize("capacity", [0, -1, 2.5, "3", None])
def test_invalid_capacities_are_rejected(capacity):
    with pytest.raises(ValueError):
        Cache(capacity)


def test_a_cache_of_one_keeps_only_the_last_key():
    cac = Cache(1)
    cac.put("a", 1)
    cac.put("b", 2)
    assert cac.get_keys() == ["b"]
    assert cac.get("b") == 2
    with pytest.raises(KeyError):
        cac.get("a")


def test_size_never_exceeds_capacity(cache):
    for i in range(10):
        cache.put(f"k{i}", i)
        assert cache.get_size() == 3
    assert cache.get_keys() == ["k9", "k8", "k7"]


# --- putting ----------------------------------------------------------------


def test_put_replaces_the_value_of_a_cached_key(cache):
    cache.put("a", 10)
    assert cache.get("a") == 10
    assert cache.get_size() == 3
    assert sorted(cache.get_keys()) == ["a", "b", "c"]


def test_put_on_a_cached_key_makes_it_most_recently_used(cache):
    cache.put("a", 10)
    assert cache.get_keys() == ["a", "c", "b"]
    cache.put("d", 4)
    assert cache.get_keys() == ["d", "a", "c"]
    with pytest.raises(KeyError):
        cache.get("b")


def test_replacing_a_value_never_drops_an_entry(cache):
    cache.put("b", 20)
    cache.put("c", 30)
    assert cache.get_size() == 3
    assert cache.get("a") == 1


def test_the_dropped_entry_is_the_least_recently_used_not_the_oldest(cache):
    cache.get("a")
    cache.put("d", 4)
    assert cache.get_keys() == ["d", "a", "c"]
    cache.put("e", 5)
    assert cache.get_keys() == ["e", "d", "a"]


@pytest.mark.parametrize("key", BAD_KEYS)
def test_invalid_keys_are_rejected(cache, key):
    before = state(cache)
    with pytest.raises(ValueError):
        cache.put(key, 1)
    assert state(cache) == before


@pytest.mark.parametrize("value", BAD_VALUES)
def test_invalid_values_are_rejected(cache, value):
    before = state(cache)
    with pytest.raises(ValueError):
        cache.put("a", value)
    with pytest.raises(ValueError):
        cache.put("new", value)
    assert state(cache) == before


def test_negative_and_zero_values_are_stored(cache):
    cache.put("z", 0)
    cache.put("n", -7)
    assert cache.get("z") == 0
    assert cache.get("n") == -7


# --- getting ----------------------------------------------------------------


def test_get_returns_the_stored_values(cache):
    assert [cache.get(k) for k in ["a", "b", "c"]] == [1, 2, 3]


def test_get_makes_the_key_most_recently_used(cache):
    cache.get("b")
    assert cache.get_keys() == ["b", "c", "a"]
    cache.get("a")
    assert cache.get_keys() == ["a", "b", "c"]


def test_getting_the_most_recent_key_changes_nothing(cache):
    cache.get("c")
    assert cache.get_keys() == ["c", "b", "a"]


@pytest.mark.parametrize("key", ["zzz", None, 1])
def test_missing_keys_raise_key_error_and_change_nothing(cache, key):
    before = state(cache)
    with pytest.raises(KeyError):
        cache.get(key)
    assert state(cache) == before


def test_a_dropped_key_can_be_put_again(cache):
    cache.put("d", 4)
    with pytest.raises(KeyError):
        cache.get("a")
    cache.put("a", 100)
    assert cache.get("a") == 100
    assert cache.get_keys() == ["a", "d", "c"]


# --- general ----------------------------------------------------------------


def test_keys_are_listed_most_recently_used_first(cache):
    assert cache.get_keys() == ["c", "b", "a"]
    assert len(cache.get_keys()) == cache.get_size()


def test_caches_do_not_share_entries():
    first, second = Cache(2), Cache(2)
    first.put("a", 1)
    assert second.get_keys() == []
    second.put("a", 2)
    assert first.get("a") == 1
    assert second.get("a") == 2
