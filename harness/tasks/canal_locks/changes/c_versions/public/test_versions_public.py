"""Public checks for the c_versions change (version numbers). Shown to the
editor, never to the writer.

Usage (with canals.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from canals import CanalNetwork, VersionConflict


def test_the_version_counts_changes():
    n = CanalNetwork()
    assert n.get_version() == 0
    n.add_lock("upper")
    n.add_lock("lower")
    n.connect("upper", "lower")
    assert n.get_version() == 3


def test_a_stale_version_is_refused():
    n = CanalNetwork()
    n.add_lock("upper")
    n.add_lock("lower")
    with pytest.raises(VersionConflict):
        n.connect("upper", "lower", expected_version=1)
    assert n.get_channels("upper") == []
    n.connect("upper", "lower", expected_version=2)
    assert n.get_channels("upper") == ["lower"]
