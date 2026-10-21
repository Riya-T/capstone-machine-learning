"""Public checks for the c_remove change (removing entries by hand). Shown to
the editor, never to the writer.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/public/test_remove_public.py
"""

import pytest
from cache import Cache


def test_remove_returns_the_value_and_drops_the_entry():
    cache = Cache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.remove("a") == 1
    assert cache.get_keys() == ["b"]
    assert cache.get_size() == 1
    with pytest.raises(KeyError):
        cache.get("a")
    with pytest.raises(KeyError):
        cache.remove("a")


def test_clear_prefix_removes_every_matching_key():
    cache = Cache(4)
    cache.put("user:1", 1)
    cache.put("item:1", 2)
    cache.put("user:2", 3)
    cache.put("item:2", 4)
    assert cache.clear_prefix("user:") == ["user:2", "user:1"]
    assert cache.get_keys() == ["item:2", "item:1"]
    assert cache.clear_prefix("other:") == []
