"""Public checks for the c_find change (where a singer stands). Shown to the
editor, never to the writer.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest changes/c_find/public/test_choir_find_public.py
"""

import pytest
from choir import Choir


@pytest.fixture
def choir():
    c = Choir()
    c.add_section("alto")
    c.add_section("tenor")
    c.add_singer("alto", "Ada")
    c.add_singer("alto", "Bea")
    return c


def test_section_and_position_of_a_singer(choir):
    assert choir.get_section_of("Bea") == "alto"
    assert choir.get_position("Ada") == 1
    assert choir.get_position("Bea") == 2


def test_a_moved_singer_has_a_new_section_and_position(choir):
    choir.add_singer("tenor", "Cal")
    choir.move_singer("Ada", "tenor")
    assert choir.get_section_of("Ada") == "tenor"
    assert choir.get_position("Ada") == 2
    assert choir.get_position("Bea") == 1


def test_an_unknown_singer_raises_key_error(choir):
    with pytest.raises(KeyError):
        choir.get_section_of("Zed")
