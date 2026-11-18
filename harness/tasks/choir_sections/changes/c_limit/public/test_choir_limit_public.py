"""Public checks for the c_limit change (a limit per section). Shown to the
editor, never to the writer.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/public/test_choir_limit_public.py
"""

import pytest
from choir import Choir, SectionFull


@pytest.fixture
def choir():
    c = Choir()
    c.add_section("alto")
    c.add_section("tenor")
    return c


def test_a_full_section_refuses_new_singers(choir):
    assert choir.get_limit("alto") is None
    choir.set_limit("alto", 2)
    assert choir.get_limit("alto") == 2
    choir.add_singer("alto", "Ada")
    choir.add_singer("alto", "Bea")
    with pytest.raises(SectionFull):
        choir.add_singer("alto", "Cal")
    assert choir.get_singers("alto") == ["Ada", "Bea"]


def test_a_move_into_a_full_section_raises(choir):
    choir.add_singer("alto", "Ada")
    choir.add_singer("tenor", "Bea")
    choir.set_limit("tenor", 1)
    with pytest.raises(SectionFull):
        choir.move_singer("Ada", "tenor")
    assert choir.get_singers("alto") == ["Ada"]
    assert choir.get_singers("tenor") == ["Bea"]
