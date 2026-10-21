"""Hidden tests for the c_stats change (hit, miss and eviction statistics).
Never shown to the writer or the editor.

Usage (with cache.py importable, e.g. in the sandbox):
    python -m pytest changes/c_stats/private/test_stats_new.py
"""

import pytest
from cache import Cache


@pytest.fixture
def cache():
    cac = Cache(2)
    cac.put("a", 1)
    cac.put("b", 2)
    return cac


def test_each_successful_get_is_one_hit(cache):
    cache.get("a")
    cache.get("b")
    cache.get("a")
    assert cache.get_stats() == (3, 0, 0)
    assert cache.get_hit_count("a") == 2
    assert cache.get_hit_count("b") == 1


def test_each_failed_get_is_one_miss(cache):
    for key in ["zzz", "zzz", None, 1]:
        with pytest.raises(KeyError):
            cache.get(key)
    assert cache.get_stats() == (0, 4, 0)


def test_only_room_making_drops_count_as_evictions(cache):
    cache.put("a", 10)  # replacement
    cache.put("b", 20)
    assert cache.get_stats() == (0, 0, 0)
    assert cache.get_evicted() == []
    cache.put("c", 3)
    assert cache.get_stats() == (0, 0, 1)
    assert cache.get_evicted() == ["a"]


def test_evicted_keys_are_listed_oldest_first_with_repeats(cache):
    cache.put("c", 3)  # drops a
    cache.put("a", 1)  # drops b
    cache.put("b", 2)  # drops c
    cache.put("c", 3)  # drops a again
    assert cache.get_evicted() == ["a", "b", "c", "a"]
    assert cache.get_stats()[2] == 4


def test_hit_counts_start_at_zero_for_new_entries(cache):
    assert cache.get_hit_count("a") == 0
    cache.put("c", 3)
    assert cache.get_hit_count("c") == 0


def test_replacing_a_value_keeps_the_hit_count(cache):
    cache.get("a")
    cache.get("a")
    cache.put("a", 100)
    assert cache.get_hit_count("a") == 2


def test_an_entry_that_comes_back_starts_counting_again(cache):
    cache.get("a")
    cache.put("c", 3)  # drops b
    cache.put("d", 4)  # drops a
    cache.put("a", 1)  # drops c
    assert cache.get_hit_count("a") == 0
    assert cache.get_stats() == (1, 0, 3)
    assert cache.get_evicted() == ["b", "a", "c"]


@pytest.mark.parametrize("key", ["zzz", None, 1])
def test_hit_count_of_a_missing_key_raises_without_a_miss(cache, key):
    with pytest.raises(KeyError):
        cache.get_hit_count(key)
    assert cache.get_stats() == (0, 0, 0)


def test_hit_count_does_not_touch_recency(cache):
    cache.get_hit_count("a")
    assert cache.get_keys() == ["b", "a"]
    cache.put("c", 3)
    assert cache.get_evicted() == ["a"]


def test_statistics_are_per_cache():
    first, second = Cache(1), Cache(1)
    first.put("a", 1)
    first.get("a")
    first.put("b", 2)
    assert first.get_stats() == (1, 0, 1)
    assert second.get_stats() == (0, 0, 0)
    assert second.get_evicted() == []


def test_failed_puts_change_no_statistic(cache):
    for key, value in [("", 1), ("c", "1"), (None, 1)]:
        with pytest.raises(ValueError):
            cache.put(key, value)
    assert cache.get_stats() == (0, 0, 0)
    assert cache.get_evicted() == []
