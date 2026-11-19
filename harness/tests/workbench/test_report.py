"""Verify report replay, safe rendering and immutable publication controls.

Usage: python -m pytest tests/workbench/test_report.py
No browser network access or model service is needed.
"""

import copy
import hashlib
import json

import pytest

from harness.evaluation.records import EvaluationError
from harness.workbench.analysis import compare_collections
from harness.workbench.report import (
    FILES,
    encoded,
    render_html,
    table_csv,
    verify_report,
    write_report,
)
from tests.workbench.helpers import fixture


def report(tmp_path):
    _, data = fixture(tmp_path)
    result = compare_collections([data], bootstrap_samples=20)
    out = tmp_path / "report"
    write_report(result, out)
    return result, out


def test_saved_report_recomputes_and_identical_replay_is_byte_exact(tmp_path):
    result, out = report(tmp_path)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    assert set(before) == FILES | {"manifest.json"}
    receipt = verify_report(out)
    assert receipt["verified"] and receipt["analysis_recomputed"]
    assert receipt["model_calls"] == 0
    write_report(result, out)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}
    assert "SYNTHETIC FIXTURE" in (out / "report.md").read_text()
    assert "identification bounds" in (out / "report.md").read_text().lower()


def test_existing_nonidentical_file_blocks_the_entire_publish(tmp_path):
    result, out = report(tmp_path)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    other = copy.deepcopy(result)
    other["reference"] = "different"
    with pytest.raises(EvaluationError, match="overwrite"):
        write_report(other, out)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}


def test_checksum_tamper_and_consistently_rehashed_false_analysis_are_rejected(tmp_path):
    _, out = report(tmp_path)
    source = out / "comparison.json"
    saved = json.loads(source.read_bytes())
    saved["methods"]["base"]["common_selected_cohort"]["selected_completion"]["estimate"] = 0.99
    source.write_bytes(encoded(saved))
    with pytest.raises(EvaluationError, match="checksum"):
        verify_report(out)
    manifest = json.loads((out / "manifest.json").read_bytes())
    manifest["files"]["comparison.json"] = hashlib.sha256(source.read_bytes()).hexdigest()
    (out / "manifest.json").write_bytes(encoded(manifest))
    with pytest.raises(EvaluationError, match="recompute"):
        verify_report(out)


def test_manifest_cannot_read_paths_outside_the_bundle(tmp_path):
    _, out = report(tmp_path)
    manifest = json.loads((out / "manifest.json").read_bytes())
    manifest["files"]["../../secret"] = "f" * 64
    (out / "manifest.json").write_bytes(encoded(manifest))
    with pytest.raises(EvaluationError, match="manifest"):
        verify_report(out)


def test_saved_strings_are_escaped_and_dashboard_has_no_external_assets(tmp_path):
    result, _ = report(tmp_path)
    payload = "</pre><script>alert('untrusted')</script>"
    result["task_summaries"]["base"][0]["task"] = payload
    text = render_html(result)
    assert payload not in text
    assert "&lt;script&gt;" in text
    assert "https://" not in text and "http://" not in text
    assert "default-src 'none'" in text
    assert 'aria-live="polite"' in text


def test_unreached_checkpoints_do_not_become_new_failures(tmp_path):
    _, out = report(tmp_path)
    import csv

    rows = list(csv.DictReader((out / "checkpoints.csv").open()))
    failed = [r for r in rows if r["status"] == "fail_new"]
    unreached = [r for r in rows if r["status"] == "not_reached"]
    assert len(failed) == len(unreached) == 4
    assert all(r["recorded"] == "False" for r in unreached)


def test_symlink_output_cannot_redirect_publication(tmp_path):
    result, _ = report(tmp_path)
    target = tmp_path / "unrelated"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symlinks requires privileges on this platform")
    with pytest.raises(EvaluationError, match="symlink"):
        write_report(result, link / "nested")
    assert not list(target.iterdir())


def test_csv_strings_cannot_become_spreadsheet_formulas():
    text = table_csv([{"label": " =2+2", "difference": -0.5}], ["label", "difference"]).decode()
    assert "' =2+2" in text
    assert "-0.5" in text
