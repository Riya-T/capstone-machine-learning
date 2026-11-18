"""Public checks for the c_revisions change (concurrency_control). Shown to
the editor, never to the writer.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_revisions/public/test_revisions_public.py
"""

import pytest
from silos import RevisionConflict, Silos


def test_the_revision_counts_successful_changes():
    s = Silos()
    assert s.get_revision() == 0
    s.add_silo("north")
    s.load("north", "wheat", 10)
    assert s.get_revision() == 2


def test_a_stale_expected_revision_is_rejected():
    s = Silos()
    s.add_silo("north")
    s.load("north", "wheat", 10, expected_revision=1)
    with pytest.raises(RevisionConflict):
        s.load("north", "wheat", 5, expected_revision=1)
    assert s.get_tonnes("north", "wheat") == 10
    assert s.get_revision() == 2
