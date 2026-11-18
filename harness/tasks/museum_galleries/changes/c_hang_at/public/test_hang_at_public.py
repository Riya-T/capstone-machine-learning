"""Public checks for the c_hang_at change (where new artworks go). Shown to
the editor, never to the writer.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hang_at/public/test_hang_at_public.py
"""

import pytest
from museum import Museum


def test_galleries_hang_at_the_end_by_default():
    m = Museum()
    m.add_gallery("east")
    assert m.get_hang_at("east") == "end"
    m.hang("lilies", "east")
    m.hang("harbor", "east")
    assert m.get_artworks("east") == ["lilies", "harbor"]


def test_a_museum_can_hang_at_the_start():
    m = Museum(hang_at="start")
    m.add_gallery("east")
    assert m.get_hang_at("east") == "start"
    m.hang("lilies", "east")
    m.hang("harbor", "east")
    assert m.get_artworks("east") == ["harbor", "lilies"]


def test_an_invalid_setting_is_rejected():
    with pytest.raises(ValueError):
        Museum(hang_at="middle")
