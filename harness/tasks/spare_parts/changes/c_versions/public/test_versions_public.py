"""Public checks for the c_versions change (concurrency control). Shown to
the editor, never to the writer.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from parts import PartsStore, VersionConflict


def test_every_change_raises_the_version():
    s = PartsStore()
    assert s.get_version() == 0
    s.add_bin("A1")
    s.stock("A1", "bolt", 5)
    assert s.get_version() == 2
    s.get_count("A1", "bolt")
    assert s.get_version() == 2


def test_a_matching_expected_version_is_accepted():
    s = PartsStore()
    s.add_bin("A1", expected_version=0)
    s.stock("A1", "bolt", 5, expected_version=1)
    assert s.get_count("A1", "bolt") == 5


def test_an_outdated_expected_version_is_rejected():
    s = PartsStore()
    s.add_bin("A1")
    s.stock("A1", "bolt", 5)
    with pytest.raises(VersionConflict):
        s.take("A1", "bolt", 1, expected_version=1)
    assert s.get_count("A1", "bolt") == 5
    assert s.get_version() == 2
