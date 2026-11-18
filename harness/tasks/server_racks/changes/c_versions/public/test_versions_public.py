"""Public checks for the c_versions change (concurrency_control). Shown to the
editor, never to the writer.

Usage (with racks.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from racks import Racks, VersionConflict


def test_the_version_counts_successful_changes():
    r = Racks()
    assert r.get_version() == 0
    r.add_rack("A")
    r.install("A", "web1")
    assert r.get_version() == 2


def test_a_stale_expected_version_is_rejected():
    r = Racks()
    r.add_rack("A")
    r.install("A", "web1", expected_version=1)
    with pytest.raises(VersionConflict):
        r.install("A", "web2", expected_version=1)
    assert r.get_servers("A") == ["web1"]
    assert r.get_version() == 2
