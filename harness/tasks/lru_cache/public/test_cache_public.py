"""Public checks for cache.py.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest public/test_cache_public.py
"""

import pytest
from cache import Cache


def test_put_then_get():
    cache = Cache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    assert cache.get("b") == 2
    assert cache.get_size() == 2
    assert cache.get_capacity() == 2


def test_a_full_cache_drops_the_least_recently_used_entry():
    cache = Cache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get_keys() == ["c", "b"]
    with pytest.raises(KeyError):
        cache.get("a")


def test_getting_a_key_makes_it_most_recently_used():
    cache = Cache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert cache.get_keys() == ["c", "a"]


def test_a_missing_key_raises_key_error():
    cache = Cache(1)
    with pytest.raises(KeyError):
        cache.get("zzz")
    assert cache.get_size() == 0


def test_bad_keys_and_values_are_rejected():
    cache = Cache(1)
    with pytest.raises(ValueError):
        cache.put("", 1)
    with pytest.raises(ValueError):
        cache.put("a", "1")
    assert cache.get_keys() == []
