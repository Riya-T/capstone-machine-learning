"""Public checks for the c_version_check change (page versions and conflict
detection). Shown to the editor, never to the writer.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_version_check/public/test_version_check_public.py
"""

import pytest
from wiki import VersionConflict, Wiki


def test_versions_count_successful_edits():
    w = Wiki()
    w.create_page("home", "ann", "a")
    assert w.get_version("home") == 1
    w.edit_page("home", "bob", "b")
    assert w.get_version("home") == 2


def test_a_stale_expected_version_is_refused():
    w = Wiki()
    w.create_page("home", "ann", "a")
    w.edit_page("home", "bob", "b", expected_version=1)
    with pytest.raises(VersionConflict):
        w.edit_page("home", "cy", "c", expected_version=1)
    assert w.get_text("home") == "b"
    assert w.get_version("home") == 2
