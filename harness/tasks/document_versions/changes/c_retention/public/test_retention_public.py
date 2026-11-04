"""Public checks for the c_retention change (adjustable number of
revisions in the history). Shown to the editor, never to the writer.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_retention/public/test_retention_public.py
"""

from wiki import Wiki


def test_retention_wiki_wide_limit():
    w = Wiki(keep=2)
    w.create_page("home", "ann", "a")
    w.edit_page("home", "bob", "b")
    w.edit_page("home", "bob", "c")
    assert w.get_keep("home") == 2
    assert w.get_history("home") == [(2, "b"), (3, "c")]
    assert w.get_revision_count("home") == 3


def test_retention_page_limit_overrides_the_default():
    w = Wiki()
    w.create_page("home", "ann", "a", keep=8)
    assert w.get_keep("home") == 8
    for text in "bcdefgh":
        w.edit_page("home", "bob", text)
    assert [n for n, _ in w.get_history("home")] == [1, 2, 3, 4, 5, 6, 7, 8]
