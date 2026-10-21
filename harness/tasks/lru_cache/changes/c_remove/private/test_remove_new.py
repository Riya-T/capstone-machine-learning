"""Hidden tests for the c_remove change (removing entries by hand). Never
shown to the writer or the editor.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/private/test_remove_new.py
"""

import pytest
from cache import Cache


@pytest.fixture
def cache():
    cac = Cache(4)
    cac.put("u:1", 1)
    cac.put("i:1", 2)
    cac.put("u:2", 3)
    cac.put("i:2", 4)
    return cac


def state(cac):
    keys = cac.get_keys()
    values = [cac.get(k) for k in reversed(keys)]
    return keys, values, cac.get_size()


def test_remove_gives_back_the_stored_value(cache):
    assert cache.remove("i:1") == 2
    assert cache.remove("u:2") == 3
    assert cache.get_size() == 2


def test_remove_keeps_the_order_of_the_other_entries(cache):
    cache.remove("u:2")
    assert cache.get_keys() == ["i:2", "i:1", "u:1"]
    cache.remove("i:2")
    assert cache.get_keys() == ["i:1", "u:1"]


@pytest.mark.parametrize("key", ["zzz", None, 1])
def test_removing_a_missing_key_raises_and_changes_nothing(cache, key):
    before = state(cache)
    with pytest.raises(KeyError):
        cache.remove(key)
    assert state(cache) == before


def test_a_removed_key_is_missing_until_put_again(cache):
    cache.remove("u:1")
    with pytest.raises(KeyError):
        cache.get("u:1")
    cache.put("u:1", 10)
    assert cache.get("u:1") == 10
    assert cache.get_keys() == ["u:1", "i:2", "u:2", "i:1"]


def test_removal_makes_room_so_nothing_is_dropped(cache):
    cache.remove("u:1")
    cache.put("n", 5)
    assert cache.get_size() == 4
    assert sorted(cache.get_keys()) == ["i:1", "i:2", "n", "u:2"]


def test_clear_prefix_returns_the_removed_keys_most_recent_first(cache):
    cache.get("u:1")
    assert cache.clear_prefix("u:") == ["u:1", "u:2"]
    assert cache.get_keys() == ["i:2", "i:1"]


def test_clear_prefix_with_no_match_changes_nothing(cache):
    before = state(cache)
    assert cache.clear_prefix("x:") == []
    assert cache.clear_prefix("u:1:extra") == []
    assert state(cache) == before


def test_clear_prefix_matches_a_key_equal_to_the_prefix(cache):
    assert cache.clear_prefix("i:2") == ["i:2"]
    assert cache.get_keys() == ["u:2", "i:1", "u:1"]


def test_the_empty_prefix_clears_everything(cache):
    assert cache.clear_prefix("") == ["i:2", "u:2", "i:1", "u:1"]
    assert cache.get_keys() == []
    assert cache.get_size() == 0
    cache.put("a", 1)
    assert cache.get_keys() == ["a"]


@pytest.mark.parametrize("prefix", [None, 1, ["u:"]])
def test_a_non_string_prefix_is_rejected(cache, prefix):
    before = state(cache)
    with pytest.raises(ValueError):
        cache.clear_prefix(prefix)
    assert state(cache) == before


def test_clear_prefix_keeps_the_order_of_the_rest(cache):
    cache.get("i:1")
    cache.clear_prefix("u:")
    assert cache.get_keys() == ["i:1", "i:2"]
