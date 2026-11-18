"""Public checks for the c_queries change (query). Shown to the editor, never
to the writer.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_queries/public/test_queries_public.py
"""

from setlists import Setlists


def make():
    s = Setlists()
    s.create_setlist("friday")
    s.create_setlist("saturday")
    for title in ["Intro", "Blue", "Run"]:
        s.add_song("friday", title)
    for title in ["Run", "Rain", "Intro"]:
        s.add_song("saturday", title)
    return s


def test_get_setlists_with_lists_every_setlist_holding_the_title():
    s = make()
    assert s.get_setlists_with("Run") == ["friday", "saturday"]
    assert s.get_setlists_with("Blue") == ["friday"]
    assert s.get_setlists_with("Storm") == []


def test_get_common_songs_keeps_the_order_of_the_first_setlist():
    s = make()
    assert s.get_common_songs("friday", "saturday") == ["Intro", "Run"]
    assert s.get_common_songs("saturday", "friday") == ["Run", "Intro"]
