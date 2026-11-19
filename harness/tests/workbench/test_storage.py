"""Check native non-overwriting publication, interruption and competing writers.

Usage: python -m pytest tests/workbench/test_storage.py
The Windows branch is exercised on Windows, not emulated by changing os.name.
"""

import os

import pytest

from harness.evaluation.records import EvaluationError
from harness.workbench.storage import publish_new


def test_complete_publication_and_replay_never_replace_different_evidence(tmp_path):
    path = tmp_path / "saved.json"
    publish_new(path, b"complete")
    publish_new(path, b"complete")
    with pytest.raises(EvaluationError, match="overwrite"):
        publish_new(path, b"different")
    assert path.read_bytes() == b"complete"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["saved.json"]


@pytest.mark.skipif(os.name != "nt", reason="Native Windows publication control")
def test_windows_publication_does_not_require_hard_links(tmp_path, monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("Windows reports must not require hard-link privileges")

    monkeypatch.setattr("os.link", forbidden)
    publish_new(tmp_path / "saved.json", b"complete")
    assert (tmp_path / "saved.json").read_bytes() == b"complete"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows publication control")
def test_racing_windows_publisher_cannot_overwrite_a_competitor(tmp_path, monkeypatch):
    path = tmp_path / "saved.json"
    rename = os.rename

    def competitor(source, destination):
        path.write_bytes(b"other evidence")
        return rename(source, destination)

    monkeypatch.setattr("harness.workbench.storage.os.rename", competitor)
    with pytest.raises(EvaluationError, match="overwrite"):
        publish_new(path, b"ours")
    assert path.read_bytes() == b"other evidence"
    assert len(list(tmp_path.iterdir())) == 1
