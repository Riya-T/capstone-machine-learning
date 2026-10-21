"""Public checks for the c_stats change (hit, miss and eviction statistics).
Shown to the editor, never to the writer.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest changes/c_stats/public/test_stats_public.py
"""

import pytest
from cache import Cache


def test_hits_and_misses_are_counted():
    cache = Cache(2)
    cache.put("a", 1)
    cache.get("a")
    cache.get("a")
    with pytest.raises(KeyError):
        cache.get("b")
    assert cache.get_stats() == (2, 1, 0)
    assert cache.get_hit_count("a") == 2


def test_evictions_are_counted_and_listed():
    cache = Cache(1)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get_stats() == (0, 0, 2)
    assert cache.get_evicted() == ["a", "b"]


def test_a_new_cache_has_no_statistics():
    cache = Cache(2)
    assert cache.get_stats() == (0, 0, 0)
    assert cache.get_evicted() == []
