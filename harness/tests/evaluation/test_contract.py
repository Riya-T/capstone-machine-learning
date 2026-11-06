"""A planned roster detects omitted or changed work without inventing outcomes.

Usage:
    uv run pytest tests/evaluation/test_contract.py
"""

import copy
import json

import pytest

from harness.__main__ import main
from harness.evaluation.analysis import compare
from harness.evaluation.contract import attach_contract, check_contract, freeze_contract
from harness.evaluation.export import export_dataset
from harness.evaluation.integrity import verify_report
from harness.evaluation.plan import _job, execute, prepare
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report
from harness.evaluation.seeds import summarize_seeds

from .helpers import IMAGE
from .test_integrity import update_checksum
from .test_plan import forbidden, mock_runtime, write_plan


def planned(tmp_path):
    prepared = prepare(write_plan(tmp_path))
    contract = freeze_contract(prepared)
    datasets = [
        export_dataset(_job(prepared, i, 11), IMAGE, method=m.id, purpose="fixture")
        for i, m in enumerate(prepared.plan.methods)
    ]
    return prepared, contract, datasets


def test_freeze_is_read_only_and_unresolved_is_not_omitted(tmp_path, monkeypatch):
    prepared, contract, datasets = planned(tmp_path)
    monkeypatch.setattr("harness.evaluation.plan.collect", forbidden)
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    path = tmp_path / "frozen.json"
    assert (
        main(
            [
                "evaluation-contract",
                "freeze",
                "--plan",
                str(prepared.source_path),
                "--out",
                str(path),
            ]
        )
        == 0
    )
    assert json.loads(path.read_bytes()) == contract
    assert not prepared.root.exists()
    assert check_contract(contract, datasets)["matches"]
    result = compare(datasets, reference="original", bootstrap_samples=50)
    attach_contract(result, contract)
    assert result["methods"]["original"]["metrics"]["initial_correctness"]["estimate"] is None
    assert summarize_seeds(result)["roster_verified"]


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "extra",
        "duplicate",
        "task",
        "writer",
        "legacy",
        "editor",
        "budget",
        "training_seed",
        "group",
    ],
)
def test_negative_controls_detect_roster_and_identity_changes(tmp_path, mode):
    _, contract, datasets = planned(tmp_path)
    if mode == "missing":
        datasets.pop()
    elif mode in ("extra", "duplicate"):
        extra = copy.deepcopy(datasets[0])
        if mode == "extra":
            extra["generation_seed"] = 99
        datasets.append(extra)
    elif mode == "task":
        datasets[0]["tasks"][0]["version"] = "f" * 64
    elif mode == "writer":
        datasets[0]["writer_model"] = "different-checkpoint"
    elif mode == "legacy":
        del datasets[0]["editor_identity"]
    elif mode == "editor":
        datasets[0]["editor_identity"] = "f" * 64
    elif mode == "budget":
        datasets[0]["contract"]["writer_max_tokens"] += 1
    elif mode == "training_seed":
        datasets[0]["training_seed"] = 999
    else:
        datasets[0]["method_group"] = "other"
    receipt = check_contract(contract, datasets)
    assert not receipt["matches"] and receipt["issues"]


def test_tampered_contract_and_rehashed_false_receipt_are_rejected(tmp_path):
    _, contract, datasets = planned(tmp_path)
    changed = copy.deepcopy(contract)
    changed["generation_seeds"].append(99)
    with pytest.raises(EvaluationError, match="changed"):
        check_contract(changed, datasets)
    result = compare(datasets, reference="original", bootstrap_samples=50)
    attach_contract(result, contract)
    directory = tmp_path / "report"
    write_report(result, directory)
    assert verify_report(directory)["analysis_recomputed"]
    result["coverage_receipt"]["expected_datasets"] = 100
    (directory / "comparison.json").write_text(json.dumps(result), encoding="utf8")
    update_checksum(directory, "comparison.json")
    with pytest.raises(EvaluationError, match="coverage receipt"):
        verify_report(directory)


def test_execution_freezes_contract_before_first_collection_and_resumes(tmp_path, monkeypatch):
    from harness.evaluation import plan as module

    prepared = prepare(write_plan(tmp_path))
    mock_runtime(monkeypatch)
    original_collect = module.collect
    calls = []

    def checked_collect(cfg):
        assert (prepared.root / "analysis.contract.json").is_file()
        calls.append(cfg.seed)
        return original_collect(cfg)

    monkeypatch.setattr(module, "collect", checked_collect)
    result = execute(prepared)
    assert result["complete"] and calls == [11, 11]
    path = prepared.root / "analysis.contract.json"
    frozen = path.read_bytes()
    monkeypatch.setattr(module, "collect", forbidden)
    monkeypatch.setattr(module, "make_runner", forbidden)
    execute(prepared)
    assert path.read_bytes() == frozen
    assert verify_report(result["report_directory"])["analysis_recomputed"]


def test_cli_coverage_rejection_writes_no_report(tmp_path, capsys):
    _, contract, datasets = planned(tmp_path)
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps(contract), encoding="utf8")
    source = tmp_path / "single.json"
    source.write_text(json.dumps(datasets[0]), encoding="utf8")
    assert (
        main(["evaluation-contract", "check", "--contract", str(frozen), "--input", str(source)])
        == 3
    )
    assert not json.loads(capsys.readouterr().out)["matches"]
    # compare requires two methods, so use a valid matched set with a missing planned seed.
    contract["generation_seeds"].append(22)
    from harness.evaluation.contract import _digest

    contract["contract_id"] = _digest({k: v for k, v in contract.items() if k != "contract_id"})
    frozen.write_text(json.dumps(contract), encoding="utf8")
    second = tmp_path / "second.json"
    second.write_text(json.dumps(datasets[1]), encoding="utf8")
    output = tmp_path / "rejected-report"
    assert (
        main(
            [
                "evaluation-report",
                "--contract",
                str(frozen),
                "--input",
                str(source),
                str(second),
                "--out",
                str(output),
            ]
        )
        == 2
    )
    assert not output.exists()


def test_legacy_summary_does_not_claim_roster_verification():
    from .test_analysis import example

    summary = summarize_seeds(compare([example(), example("candidate")], bootstrap_samples=20))
    assert not summary["roster_verified"]
    assert "omitted" in summary["roster_note"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("methods", [None]),
        ("generation_seeds", [[]]),
        ("tasks", {"a": None}),
        ("comparison_contract", {}),
        ("bootstrap", {"samples": "bad"}),
        ("purpose", []),
        ("plan_fingerprint", False),
    ],
)
def test_rehashed_malformed_contracts_fail_cleanly(tmp_path, field, value):
    from harness.evaluation.contract import _digest

    _, contract, datasets = planned(tmp_path)
    contract[field] = value
    contract["contract_id"] = _digest({k: v for k, v in contract.items() if k != "contract_id"})
    with pytest.raises(EvaluationError):
        check_contract(contract, datasets)


def test_changed_analysis_settings_cannot_use_frozen_contract(tmp_path):
    _, contract, datasets = planned(tmp_path)
    result = compare(datasets, reference="original", bootstrap_samples=20)
    with pytest.raises(EvaluationError, match="settings differ"):
        attach_contract(result, contract)
