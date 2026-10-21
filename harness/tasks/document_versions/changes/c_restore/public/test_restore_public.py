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
    with pytest.raises(IndexError):
        w.get_revision("home", 2)


def test_restore_then_edit_reuses_the_next_number():
    w = Wiki()
    w.create_page("home", "ann", "a")
    w.edit_page("home", "bob", "b")
    w.restore("home", 1)
    w.edit_page("home", "cy", "c")
    assert w.get_revision_count("home") == 2
    assert w.get_revision("home", 2) == "c"
