"""Human review preserves source evidence, missing cases, disagreements and abstention.

Usage:
    uv run pytest tests/evaluation/test_review.py
"""

import csv
import json

import pytest

from harness.evaluation.analysis import compare
from harness.evaluation.integrity import verify_report
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report
from harness.evaluation.review import ANNOTATION_FIELDS, compile_reviews, make_review_pack

from .helpers import saved
from .test_analysis import example


def pack(tmp_path):
    primary, target = tmp_path / "primary", tmp_path / "pack"
    write_report(compare([example()], bootstrap_samples=20), primary)
    make_review_pack(primary, target)
    cases = json.loads((target / "cases.json").read_text())["cases"]
    return target, cases


def annotations(path, rows):
    with path.open("w", newline="", encoding="utf8") as stream:
        writer = csv.DictWriter(stream, fieldnames=ANNOTATION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def entry(case, reviewer="alice", category="edit_bug", confidence="hypothesis", evidence=""):
    return dict(
        case_id=case["case_id"],
        reviewer=reviewer,
        category=category,
        confidence=confidence,
        evidence=evidence,
        notes="A review fixture, not a causal finding",
    )


def test_pack_binds_cases_to_report_and_does_not_trust_embedded_store_paths(tmp_path):
    target, cases = pack(tmp_path)
    assert len(cases) == 7
    assert len({c["case_id"] for c in cases}) == 7
    assert {c["after_preview"]["state"] for c in cases} <= {
        "store_not_provided",
        "no_saved_source_hash",
    }
    assert verify_report(target)["kind"] == "review_pack"
    before = (target / "cases.json").read_bytes()
    make_review_pack(tmp_path / "primary", target)
    assert (target / "cases.json").read_bytes() == before


def test_annotations_keep_unreviewed_cases_and_reviewer_disagreements(tmp_path):
    target, cases = pack(tmp_path)
    first = annotations(tmp_path / "alice.csv", [entry(cases[0])])
    second = annotations(
        tmp_path / "bob.csv", [entry(cases[0], reviewer="bob", category="initial_bug")]
    )
    compile_reviews(target, [first, second], tmp_path / "summary")
    result = json.loads((tmp_path / "summary/analysis.json").read_text())
    assert result["case_counts"] == {"disagreement": 1, "unreviewed": 6}
    assert result["training_labels"] is None
    assert len(result["cases"][0]["annotations"]) == 2
    assert len(result["cases"]) == 7


@pytest.mark.parametrize(
    "change",
    [
        dict(case_id="x"),
        dict(category="made_up"),
        dict(confidence="certain"),
        dict(reviewer=""),
        dict(confidence="verified"),
    ],
)
def test_unknown_or_unsubstantiated_review_claims_are_rejected(tmp_path, change):
    target, cases = pack(tmp_path)
    row = entry(cases[0])
    row.update(change)
    source = annotations(tmp_path / "review.csv", [row])
    with pytest.raises(EvaluationError):
        compile_reviews(target, [source], tmp_path / "summary")
    assert not (tmp_path / "summary").exists()


def test_duplicate_reviewer_case_rejected_and_verified_reference_never_executed(tmp_path):
    target, cases = pack(tmp_path)
    row = entry(cases[0], confidence="verified", evidence="nonexistent/reproduction.py")
    source = annotations(tmp_path / "review.csv", [row, row])
    with pytest.raises(EvaluationError, match="Duplicate"):
        compile_reviews(target, [source], tmp_path / "summary")
    annotations(source, [row])
    compile_reviews(target, [source], tmp_path / "summary")
    result = json.loads((tmp_path / "summary/analysis.json").read_text())
    assert "not opened or executed" in result["note"]
    assert result["cases"][0]["annotations"][0]["confidence"] == "verified"


def test_unchanged_template_compiles_to_all_unreviewed(tmp_path):
    target, cases = pack(tmp_path)
    compile_reviews(target, [target / "annotations.template.csv"], tmp_path / "summary")
    result = json.loads((tmp_path / "summary/analysis.json").read_text())
    assert result["case_counts"] == {"unreviewed": len(cases)}


def test_explicit_store_previews_saved_bytes_without_running_them(tmp_path):
    cfg, data = saved(tmp_path, statuses={("s1", 0): ["fail_new"]})
    primary, target = tmp_path / "primary", tmp_path / "pack"
    write_report(compare([data], bootstrap_samples=20), primary)
    make_review_pack(primary, target, stores={"original": cfg.runs_dir})
    case = json.loads((target / "cases.json").read_text())["cases"][0]
    assert case["before_preview"]["state"] == case["after_preview"]["state"] == "available"
    assert case["before_preview"] == case["after_preview"]
    assert case["input_source_hash"] == case["output_source_hash"]


def test_source_previews_are_html_escaped_and_corrupt_blobs_rejected(tmp_path, monkeypatch):
    target, _ = pack(tmp_path)
    monkeypatch.setattr(
        "harness.evaluation.review._preview",
        lambda *args: dict(
            state="available",
            files=[dict(path="<unsafe>", text="<script>alert(1)</script>", truncated=False)],
        ),
    )
    make_review_pack(tmp_path / "primary", tmp_path / "escaped")
    page = (tmp_path / "escaped/review.html").read_text(encoding="utf8")
    assert "&lt;script&gt;" in page and "<script>" not in page
    assert "&lt;unsafe&gt;" in page


def test_csv_formula_text_is_safe_while_json_preserves_original_text(tmp_path):
    target, cases = pack(tmp_path)
    row = entry(cases[0])
    row["notes"] = '=HYPERLINK("https://example.com")'
    source = annotations(tmp_path / "review.csv", [row])
    compile_reviews(target, [source], tmp_path / "summary")
    assert "'=HYPERLINK" in (tmp_path / "summary/annotations.csv").read_text()
    saved_row = json.loads((tmp_path / "summary/analysis.json").read_text())["cases"][0][
        "annotations"
    ][0]
    assert saved_row["notes"] == row["notes"]


def test_corrupt_explicit_source_blob_cannot_be_presented_as_verified_code(tmp_path):
    cfg, data = saved(tmp_path, statuses={("s1", 0): ["fail_new"]})
    primary = tmp_path / "primary"
    write_report(compare([data], bootstrap_samples=20), primary)
    digest = data["samples"][0]["candidate_id"]
    (cfg.runs_dir / "blobs" / (digest + ".json")).write_bytes(b"{}")
    with pytest.raises(EvaluationError, match="Corrupt"):
        make_review_pack(primary, tmp_path / "review", stores={"original": cfg.runs_dir})
    assert not (tmp_path / "review").exists()
