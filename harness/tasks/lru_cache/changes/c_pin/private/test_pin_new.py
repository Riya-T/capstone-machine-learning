"""Hidden tests for the c_pin change (pinned entries). Never shown to the
writer or the editor.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pin/private/test_pin_new.py
"""

import pytest
from cache import Cache, CacheFull


@pytest.fixture
def cache():
    cac = Cache(3)
    cac.put("a", 1)
    cac.put("b", 2)
    cac.put("c", 3)
    return cac


def state(cac):
    keys = cac.get_keys()
    values = [cac.get(k) for k in reversed(keys)]
    return keys, values, [cac.is_pinned(k) for k in keys]


def test_entries_start_unpinned(cache):
    assert [cache.is_pinned(k) for k in ["a", "b", "c"]] == [False, False, False]


def test_pinning_and_unpinning_twice_is_harmless(cache):
    cache.pin("a")
    cache.pin("a")
    assert cache.is_pinned("a")
    cache.unpin("a")
    cache.unpin("a")
    assert not cache.is_pinned("a")
    assert not cache.is_pinned("b")


@pytest.mark.parametrize("method", ["pin", "unpin", "is_pinned"])
@pytest.mark.parametrize("key", ["zzz", None, 1])
def test_pin_methods_on_missing_keys_raise_key_error(cache, method, key):
    before = state(cache)
    with pytest.raises(KeyError):
        getattr(cache, method)(key)
    assert state(cache) == before


def test_pin_methods_do_not_change_recency(cache):
    cache.pin("a")
    cache.is_pinned("a")
    cache.unpin("a")
    assert cache.get_keys() == ["c", "b", "a"]


def test_the_least_recent_unpinned_entry_is_dropped(cache):
    cache.pin("a")
    cache.put("d", 4)
    assert cache.get_keys() == ["d", "c", "a"]
    cache.pin("c")
    cache.put("e", 5)
    assert cache.get_keys() == ["e", "c", "a"]


def test_pinned_entries_keep_their_values_and_can_be_read(cache):
    cache.pin("a")
    for i in range(5):
        cache.put(f"k{i}", i)
    assert cache.get("a") == 1
    assert cache.get_keys()[0] == "a"
    assert cache.get_size() == 3


def test_a_full_pinned_cache_raises_and_changes_nothing(cache):
    for key in ["a", "b", "c"]:
        cache.pin(key)
    before = state(cache)
    with pytest.raises(CacheFull):
        cache.put("d", 4)
    assert state(cache) == before
    with pytest.raises(KeyError):
        cache.get("d")


def test_replacing_a_value_works_when_everything_is_pinned(cache):
    for key in ["a", "b", "c"]:
        cache.pin(key)
    cache.put("a", 100)
    assert cache.get("a") == 100
    assert cache.is_pinned("a")
    assert cache.get_keys()[0] == "a"


def test_unpinning_lets_an_entry_be_dropped_again(cache):
    cache.pin("a")
    cache.put("d", 4)  # drops b
    cache.unpin("a")
    cache.put("e", 5)  # drops a, the least recent now
    assert cache.get_keys() == ["e", "d", "c"]


def test_a_dropped_key_put_again_is_not_pinned(cache):
    cache.pin("c")
    cache.put("d", 4)  # drops a
    cache.put("a", 1)  # drops b
    assert not cache.is_pinned("a")
    assert cache.is_pinned("c")


def test_bad_input_is_reported_before_cache_full(cache):
    for key in ["a", "b", "c"]:
        cache.pin(key)
    with pytest.raises(ValueError):
        cache.put("", 1)
    with pytest.raises(ValueError):
        cache.put("d", "4")


def test_cache_full_is_not_a_key_or_value_error():
    assert not issubclass(CacheFull, (KeyError, ValueError))
