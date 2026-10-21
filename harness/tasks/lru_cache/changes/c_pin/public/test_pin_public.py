"""Public checks for the c_pin change (pinned entries). Shown to the editor,
never to the writer.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pin/public/test_pin_public.py
"""

import pytest
from cache import Cache, CacheFull


def test_a_pinned_entry_survives_eviction():
    cache = Cache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.pin("a")
    cache.put("c", 3)
    assert cache.is_pinned("a")
    assert cache.get_keys() == ["c", "a"]
    with pytest.raises(KeyError):
        cache.get("b")


def test_a_full_cache_of_pinned_entries_refuses_new_keys():
    cache = Cache(1)
    cache.put("a", 1)
    cache.pin("a")
    with pytest.raises(CacheFull):
        cache.put("b", 2)
    assert cache.get_keys() == ["a"]
    cache.unpin("a")
    cache.put("b", 2)
    assert cache.get_keys() == ["b"]
