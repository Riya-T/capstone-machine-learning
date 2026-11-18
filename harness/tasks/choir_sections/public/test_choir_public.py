"""Public checks for choir.py.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest public/test_choir_public.py
"""

import pytest
from choir import Choir, ChoirError


@pytest.fixture
def choir():
    c = Choir()
    c.add_section("alto")
    c.add_section("tenor")
    return c


def test_singers_stand_in_the_order_they_joined(choir):
    choir.add_singer("alto", "Ada")
    choir.add_singer("alto", "Bea")
    choir.add_singer("tenor", "Cal")
    choir.add_singer("alto", "Dot")
    assert choir.get_singers("alto") == ["Ada", "Bea", "Dot"]
    assert choir.get_singers("tenor") == ["Cal"]
    assert choir.get_sections() == ["alto", "tenor"]


def test_a_moved_singer_goes_to_the_end(choir):
    for name in ["Ada", "Bea", "Cal"]:
        choir.add_singer("alto", name)
    choir.add_singer("tenor", "Dot")
    choir.move_singer("Bea", "tenor")
    assert choir.get_singers("alto") == ["Ada", "Cal"]
    assert choir.get_singers("tenor") == ["Dot", "Bea"]


def test_a_singer_name_in_another_section_is_taken(choir):
    choir.add_singer("alto", "Ada")
    with pytest.raises(ChoirError):
        choir.add_singer("tenor", "Ada")
    assert choir.get_singers("tenor") == []


def test_move_all_appends_the_singers_in_order_and_keeps_the_source(choir):
    choir.add_singer("alto", "Ada")
    choir.add_singer("alto", "Bea")
    choir.add_singer("tenor", "Cal")
    assert choir.move_all("alto", "tenor") == 2
    assert choir.get_singers("tenor") == ["Cal", "Ada", "Bea"]
    assert choir.get_singers("alto") == []
    assert choir.get_sections() == ["alto", "tenor"]


def test_merge_appends_the_singers_in_order_and_removes_the_source(choir):
    choir.add_singer("alto", "Ada")
    choir.add_singer("alto", "Bea")
    choir.add_singer("tenor", "Cal")
    assert choir.merge_sections("alto", "tenor") == 2
    assert choir.get_sections() == ["tenor"]
    assert choir.get_singers("tenor") == ["Cal", "Ada", "Bea"]
    with pytest.raises(KeyError):
        choir.get_singers("alto")


def test_removing_a_singer_keeps_the_others_in_order(choir):
    for name in ["Ada", "Bea", "Cal"]:
        choir.add_singer("alto", name)
    choir.remove_singer("Bea")
    assert choir.get_singers("alto") == ["Ada", "Cal"]
    with pytest.raises(KeyError):
        choir.remove_singer("Bea")
