"""Exercise native failure cases, bounded previews and evidence-based human review.

Usage: python -m pytest tests/workbench/test_review.py
Authored status fixtures are not experimental outcomes or established causes.
"""

import csv
import hashlib
import json
from pathlib import Path

import pytest

from harness.evaluation.records import EvaluationError
from harness.evaluation.review import ANNOTATION_FIELDS, preview_diff
from harness.workbench.analysis import compare_collections
from harness.workbench.report import encoded, verify_report, write_report
from harness.workbench.review import compile_pack, make_pack
from tests.workbench.helpers import fixture
from tests.workbench.test_export import hashes


def primary(tmp_path, **kwargs):
    cfg, data = fixture(tmp_path, **kwargs)
    path = tmp_path / "primary"
    write_report(compare_collections([data], bootstrap_samples=20), path)
    return cfg, path


def annotation(
    path,
    case,
    *,
    reviewer="one",
    category="uncertain",
    confidence="hypothesis",
    evidence="",
    notes="Software review fixture only",
):
    with path.open("w", newline="", encoding="utf8") as stream:
        writer = csv.DictWriter(stream, fieldnames=ANNOTATION_FIELDS)
        writer.writeheader()
        writer.writerow(
            dict(
                case_id=case["case_id"],
                reviewer=reviewer,
                category=category,
                confidence=confidence,
                evidence=evidence,
                notes=notes,
            )
        )
    return path


def rehash(directory, name):
    manifest = json.loads((directory / "manifest.json").read_bytes())
    manifest["files"][name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
    (directory / "manifest.json").write_bytes(encoded(manifest))


def test_cases_are_terminal_stops_and_missing_or_overcap_work_is_separate(tmp_path):
    _, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    payload = json.loads((tmp_path / "pack/cases.json").read_bytes())
    assert len(payload["cases"]) == 6
    assert sum(c["stage"] == "edit" for c in payload["cases"]) == 4
    assert sum(c["status"] == "initial_fail" for c in payload["cases"]) == 1
    assert sum(c["status"] == "initial_parse_failure" for c in payload["cases"]) == 1
    assert len({c["case_id"] for c in payload["cases"]}) == 6
    assert payload["missing_work"][0]["reason"] == "not_scheduled_over_cap"
    assert all(c["step"] != 2 for c in payload["cases"])
    html = (tmp_path / "pack/review.html").read_text()
    assert "initial samples" in html and "rep None" not in html
    assert verify_report(tmp_path / "pack")["kind"] == "collection_review_pack"


def test_unfinished_edits_remain_missing_not_behavioral_failures(tmp_path):
    _, source = primary(tmp_path, missing=(0,))
    make_pack(source, tmp_path / "pack")
    payload = json.loads((tmp_path / "pack/cases.json").read_bytes())
    assert {c["stage"] for c in payload["cases"]} == {"initial"}
    assert "writer_answer_missing" in {r["reason"] for r in payload["missing_work"]}
    assert "not_scheduled_unresolved" in {r["reason"] for r in payload["missing_work"]}


def test_previews_require_explicit_stores_and_never_modify_or_execute_source(tmp_path, monkeypatch):
    cfg, source = primary(tmp_path)
    before = hashes(cfg.runs_dir)
    make_pack(source, tmp_path / "without")
    without = json.loads((tmp_path / "without/cases.json").read_bytes())
    assert "available" not in {c["after_preview"]["state"] for c in without["cases"]}
    make_pack(source, tmp_path / "with", stores={"base": cfg.runs_dir})
    with_source = json.loads((tmp_path / "with/cases.json").read_bytes())
    assert "available" in {c["after_preview"]["state"] for c in with_source["cases"]}
    assert before == hashes(cfg.runs_dir)
    assert "writer sample indices" in (tmp_path / "with/review.html").read_text()
    assert verify_report(tmp_path / "with")["analysis_recomputed"]


def test_multiple_reviewers_disagree_without_changing_scores_or_setting_labels(tmp_path):
    _, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    original = (source / "comparison.json").read_bytes()
    case = next(
        c
        for c in json.loads((tmp_path / "pack/cases.json").read_bytes())["cases"]
        if c["stage"] == "edit"
    )
    first = annotation(tmp_path / "one.csv", case, category="edit_bug")
    second = annotation(tmp_path / "two.csv", case, reviewer="two", category="task_ambiguity")
    compile_pack(tmp_path / "pack", [first, second], tmp_path / "compiled")
    result = json.loads((tmp_path / "compiled/analysis.json").read_bytes())
    assert result["case_counts"] == {"disagreement": 1, "unreviewed": 5}
    assert result["training_labels"] is None
    assert "SYNTHETIC FIXTURE" in (tmp_path / "compiled/report.html").read_text()
    assert (source / "comparison.json").read_bytes() == original
    assert verify_report(tmp_path / "compiled")["analysis_recomputed"]


@pytest.mark.parametrize(
    "problem",
    ["unknown_case", "duplicate_reviewer", "verified_without_evidence", "initial_edit_bug"],
)
def test_invalid_annotation_claims_are_rejected_before_publication(tmp_path, problem):
    _, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    cases = json.loads((tmp_path / "pack/cases.json").read_bytes())["cases"]
    case = next(
        c for c in cases if c["stage"] == ("initial" if problem == "initial_edit_bug" else "edit")
    )
    if problem == "unknown_case":
        case["case_id"] = "f" * 64
    first = annotation(
        tmp_path / "one.csv",
        case,
        confidence="verified" if problem == "verified_without_evidence" else "hypothesis",
        category="edit_bug" if problem == "initial_edit_bug" else "uncertain",
    )
    paths = [first, first] if problem == "duplicate_reviewer" else [first]
    with pytest.raises(EvaluationError):
        compile_pack(tmp_path / "pack", paths, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_rehashed_case_score_change_cannot_survive_source_recomputation(tmp_path):
    _, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    path = tmp_path / "pack/cases.json"
    payload = json.loads(path.read_bytes())
    payload["cases"][0]["status"] = "success"
    path.write_bytes(encoded(payload))
    rehash(tmp_path / "pack", "cases.json")
    with pytest.raises(EvaluationError, match="disagree"):
        verify_report(tmp_path / "pack")


def test_evidence_references_are_text_not_files_to_open(tmp_path):
    _, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    case = json.loads((tmp_path / "pack/cases.json").read_bytes())["cases"][0]
    reference = str(tmp_path / "nonexistent-evidence.py")
    path = annotation(tmp_path / "review.csv", case, confidence="verified", evidence=reference)
    compile_pack(tmp_path / "pack", [path], tmp_path / "compiled")
    assert not Path(reference).exists()
    assert verify_report(tmp_path / "compiled")["verified"]


def test_pack_replay_is_identical_and_outputs_cannot_replace_source_stores(tmp_path):
    cfg, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    before = hashes(tmp_path / "pack")
    make_pack(source, tmp_path / "pack")
    assert before == hashes(tmp_path / "pack")
    with pytest.raises(EvaluationError, match="outside"):
        make_pack(source, cfg.runs_dir / "review", stores={"base": cfg.runs_dir})


def test_diff_is_bounded_display_and_never_fills_missing_or_truncated_code():
    before = {
        "state": "available",
        "files": [{"path": "main.py", "text": "x = 1\n", "truncated": False}],
    }
    after = {
        "state": "available",
        "files": [{"path": "main.py", "text": "x = 2\n", "truncated": False}],
    }
    assert "-x = 1" in preview_diff(before, after)
    assert "+x = 2" in preview_diff(before, after)
    after["files"][0]["truncated"] = True
    assert "unavailable" in preview_diff(before, after)
    assert "unavailable" in preview_diff({"state": "blob_missing", "files": []}, before)


def test_diff_rejects_excessive_display_line_counts():
    source = {
        "state": "available",
        "files": [{"path": "main.py", "text": "x\n" * 5000, "truncated": False}],
    }
    assert "line limit" in preview_diff(source, source)


def test_freeform_annotation_text_stays_inert_in_html_and_csv(tmp_path):
    _, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    case = json.loads((tmp_path / "pack/cases.json").read_bytes())["cases"][0]
    path = annotation(
        tmp_path / "review.csv",
        case,
        reviewer="=2+2",
        notes="<script>alert('x')</script> | freeform text\nsecond line",
    )
    compile_pack(tmp_path / "pack", [path], tmp_path / "compiled")
    text = (tmp_path / "compiled/report.html").read_text()
    assert "<script>" not in text and "&lt;script&gt;" in text
    assert "'=2+2" in (tmp_path / "compiled/annotations.csv").read_text()
    assert verify_report(tmp_path / "compiled")["verified"]


def test_compiled_review_needs_neither_original_pack_nor_original_annotation_files(
    tmp_path, monkeypatch
):
    _, source = primary(tmp_path)
    make_pack(source, tmp_path / "pack")
    case = json.loads((tmp_path / "pack/cases.json").read_bytes())["cases"][0]
    path = annotation(tmp_path / "review.csv", case)
    compile_pack(tmp_path / "pack", [path], tmp_path / "compiled")
    read_bytes = Path.read_bytes

    def local_only(candidate):
        if candidate == path or candidate.is_relative_to(tmp_path / "pack"):
            pytest.fail("Compiled review verification must use its archived inputs")
        return read_bytes(candidate)

    monkeypatch.setattr(Path, "read_bytes", local_only)
    assert verify_report(tmp_path / "compiled")["verified"]


def test_all_successful_source_does_not_manufacture_failure_cases(tmp_path):
    from harness.workbench.export import export_collection
    from tests.evaluation.helpers import IMAGE, saved

    cfg, _ = saved(tmp_path)
    data = export_collection(cfg, IMAGE, method="base", purpose="fixture")
    write_report(compare_collections([data], bootstrap_samples=20), tmp_path / "source")
    make_pack(tmp_path / "source", tmp_path / "pack")
    payload = json.loads((tmp_path / "pack/cases.json").read_bytes())
    assert payload["cases"] == []
    compile_pack(
        tmp_path / "pack", [tmp_path / "pack/annotations.template.csv"], tmp_path / "compiled"
    )
    assert json.loads((tmp_path / "compiled/analysis.json").read_bytes())["case_counts"] == {}
    assert verify_report(tmp_path / "compiled")["verified"]
