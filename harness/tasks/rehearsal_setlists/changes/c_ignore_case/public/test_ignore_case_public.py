"""Public checks for the c_ignore_case change (configuration). Shown to the
editor, never to the writer.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_ignore_case/public/test_ignore_case_public.py
"""

import pytest
from setlists import SetlistError, Setlists


def test_titles_are_compared_exactly_by_default():
    s = Setlists()
    assert s.get_ignore_case() is False
    s.create_setlist("friday")
    s.add_song("friday", "Blue")
    s.add_song("friday", "BLUE")
    assert s.get_songs("friday") == ["Blue", "BLUE"]


def test_with_ignore_case_capitals_do_not_matter():
    s = Setlists(ignore_case=True)
    assert s.get_ignore_case() is True
    s.create_setlist("friday")
    s.add_song("friday", "Blue")
    with pytest.raises(SetlistError):
        s.add_song("friday", "BLUE")
    s.remove_song("friday", "blue")
    assert s.get_songs("friday") == []
