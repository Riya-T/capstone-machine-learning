"""Public checks for the c_restore change (restoring an earlier revision).
Shown to the editor, never to the writer.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_restore/public/test_restore_public.py
"""

import pytest
from wiki import Wiki


def test_restore_discards_later_revisions():
    w = Wiki()
    w.create_page("home", "ann", "good")
    w.edit_page("home", "vandal", "bad")
    w.restore("home", 1)
    assert w.get_text("home") == "good"
    assert w.get_revision_count("home") == 1
    assert w.get_authors("home") == ["ann"]
    assert w.get_version("home") == 3
    assert w.get_history("home") == [(1, "good")]


def test_restore_then_edit_reuses_the_next_number():
    w = Wiki()
    w.create_page("home", "ann", "a")
    w.edit_page("home", "bob", "b")
    w.restore("home", 1)
    w.edit_page("home", "cy", "c")
    assert w.get_revision_count("home") == 2
    assert w.get_history("home") == [(1, "a"), (2, "c")]


def test_restore_to_a_revision_older_than_the_history_raises_index_error():
    w = Wiki(keep=2)
    w.create_page("home", "ann", "r1")
    for n in range(2, 5):
        w.edit_page("home", "bob", f"r{n}")
    with pytest.raises(IndexError):
        w.restore("home", 2)
    assert w.get_history("home") == [(3, "r3"), (4, "r4")]
