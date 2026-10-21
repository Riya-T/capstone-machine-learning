"""Public checks for the c_search change (finding pages and contributions).
Shown to the editor, never to the writer.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/public/test_search_public.py
"""

from wiki import Wiki


def test_search_finds_pages_by_current_text():
    w = Wiki()
    w.create_page("home", "ann", "Welcome to the wiki")
    w.create_page("faq", "bob", "Questions")
    w.create_page("help", "ann", "The wiki explained")
    assert w.find_pages("wiki") == ["home", "help"]
    assert w.find_pages("nothing") == []


def test_search_contributions_across_pages():
    w = Wiki()
    w.create_page("home", "ann", "a")
    w.create_page("faq", "bob", "b")
    w.edit_page("home", "bob", "c")
    assert w.get_contributions("bob") == [("faq", 1), ("home", 2)]
    assert w.get_contributions("zed") == []
