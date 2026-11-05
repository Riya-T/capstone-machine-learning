"""Evaluation plan integration through the actual collector with mocked execution.

Usage:
    uv run pytest tests/evaluation/test_plan.py
    # These are software fixtures, not benchmark/model evidence.
"""

import importlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from harness.__main__ import main
from harness.config import ConfigError, canonical
from harness.evaluation import plan as module
from harness.evaluation.plan import execute, prepare, preview
from harness.evaluation.records import EvaluationError
from harness.models.backends import MockBackend
from harness.sandbox.evaluator import CategoryResult, InitialEvaluation, StepEvaluation

from .helpers import IMAGE, ROOT, config


def write_plan(tmp_path, edit=None):
    methods = []
    for name in ("original", "candidate"):
        cfg = config(tmp_path, name)
        cfg = replace(
            cfg,
            runs_dir=tmp_path / "old-results" / name,
            writer=replace(cfg.writer, backend=replace(cfg.writer.backend, model=name)),
        )
        path = tmp_path / (name + ".yaml")
        path.write_text(yaml.safe_dump(canonical(cfg, tmp_path)), encoding="utf8")
        methods.append(dict(id=name, config=path.name))
    raw = dict(
        schema_version=1,
        name="fixture-comparison",
        purpose="fixture",
        output_dir="new-results",
        reference="original",
        generation_seeds=[11],
        methods=methods,
        bootstrap_samples=50,
    )
    if edit:
        edit(raw)
    path = tmp_path / "evaluation.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf8")
    return path


class FakeRunner:
    def __init__(self, cfg):
        self.cfg = cfg

    def ensure_image(self):
        return IMAGE

    def existing_image_id(self):
        return IMAGE

    def sweep(self):
        return 0


def category(ok=True):
    return CategoryResult("fixture", "passed" if ok else "failed", int(ok), 1, (), "ok")


class FakeEvaluator:
    """No task source executes: synthetic private results exercise the real controller."""

    def __init__(self, runner, workers=1):
        self.bad = runner.cfg.writer.backend.model == "candidate"

    def check_initial(self, program, task):
        return InitialEvaluation(category(), category())

    def check_step(self, program, step):
        return StepEvaluation(category(), category(not self.bad or step.number == 1))


def mock_runtime(monkeypatch):
    collector = importlib.import_module("harness.collection.collect")
    monkeypatch.setattr(module, "make_runner", lambda cfg, **kw: FakeRunner(cfg))
    monkeypatch.setattr(collector, "make_runner", lambda cfg, **kw: FakeRunner(cfg))
    monkeypatch.setattr(collector, "Evaluator", FakeEvaluator)


def forbidden(*a, **kw):
    raise AssertionError("No model, collector, or container operation permitted")


def test_dry_run_has_no_backend_container_or_filesystem_effects(tmp_path, monkeypatch, capsys):
    path = write_plan(tmp_path)
    monkeypatch.setattr(module, "make_runner", forbidden)
    monkeypatch.setattr(module, "collect", forbidden)
    assert main(["evaluate", "--plan", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "dry-run" and result["max_writer_generations"] == 2
    assert result["max_edit_checkpoints"] == 24
    assert not (tmp_path / "new-results").exists()
    assert not (tmp_path / "old-results").exists()


def test_actual_collector_integration_isolated_outputs_and_offline_resume(tmp_path, monkeypatch):
    path = write_plan(tmp_path)
    original_store = tmp_path / "old-results"
    original_store.mkdir()
    sentinel = original_store / "do-not-touch"
    sentinel.write_bytes(b"prior evidence")
    mock_runtime(monkeypatch)
    calls = []
    original = MockBackend.generate

    def counted(self, *a, **kw):
        calls.append(self.identity)
        return original(self, *a, **kw)

    monkeypatch.setattr(MockBackend, "generate", counted)
    prepared = prepare(path)
    result = execute(prepared)
    assert result["complete"] and len(calls) == 26  # two writers + 24 editing turns
    report_path = Path(result["reports"]["comparison.json"])
    report = json.loads(report_path.read_text())
    assert report["purpose"] == "fixture"
    assert report["methods"]["original"]["metrics"]["change_completion"]["estimate"] == 1
    assert report["methods"]["candidate"]["metrics"]["change_completion"]["estimate"] == 0.5
    assert sentinel.read_bytes() == b"prior evidence"
    assert list(original_store.iterdir()) == [sentinel]
    before = report_path.read_bytes()
    monkeypatch.setattr(MockBackend, "generate", forbidden)
    monkeypatch.setattr(module, "make_runner", forbidden)
    monkeypatch.setattr(module, "collect", forbidden)
    assert execute(prepared) == result
    offline = execute(prepared, export_only=True)
    assert offline["complete"] and not offline["inference_requested"]
    assert report_path.read_bytes() == before


def test_interrupted_jobs_stay_missing_and_resume_only_unfinished_work(tmp_path, monkeypatch):
    prepared = prepare(write_plan(tmp_path))
    mock_runtime(monkeypatch)
    real = module.collect
    calls = []

    def interrupted(cfg):
        calls.append(cfg.name)
        if len(calls) == 2:
            raise RuntimeError("fixture interruption")
        return real(cfg)

    monkeypatch.setattr(module, "collect", interrupted)
    with pytest.raises(RuntimeError, match="fixture interruption"):
        execute(prepared)
    partial = execute(prepared, export_only=True)
    assert not partial["complete"]
    data = json.loads(Path(partial["reports"]["comparison.json"]).read_text())
    assert data["methods"]["candidate"]["metrics"]["change_completion"]["estimate"] is None
    old_report = Path(partial["reports"]["comparison.json"]).read_bytes()
    resumed = []

    def resumed_collect(cfg):
        resumed.append(cfg.name)
        return real(cfg)

    monkeypatch.setattr(module, "collect", resumed_collect)
    assert execute(prepared)["complete"]
    assert resumed == ["evaluation-candidate-11"]
    assert Path(partial["reports"]["comparison.json"]).read_bytes() == old_report


def test_lock_prevents_concurrent_controllers(tmp_path, monkeypatch):
    prepared = prepare(write_plan(tmp_path))
    monkeypatch.setattr(module, "make_runner", forbidden)
    with module._controller(prepared.root), pytest.raises(EvaluationError, match="Another"):
        execute(prepared)


def test_export_only_cannot_create_a_run(tmp_path):
    prepared = prepare(write_plan(tmp_path))
    with pytest.raises(EvaluationError, match="No frozen"):
        execute(prepared, export_only=True)
    assert not prepared.root.exists()


@pytest.mark.parametrize(
    "edit",
    [
        lambda p: p.update(generation_seeds=[1, 1]),
        lambda p: p.update(generation_seeds=[True]),
        lambda p: p.update(name="../escape"),
        lambda p: p["methods"].append(p["methods"][0]),
        lambda p: p.update(reference="absent"),
        lambda p: p.update(max_method_runs=1),
        lambda p: p.update(max_edit_checkpoints=1),
        lambda p: p.update(unknown_field="typo"),
        lambda p: p.update(purpose="heldout"),
    ],
)
def test_invalid_plans_fail_before_any_work(tmp_path, edit):
    with pytest.raises(ConfigError):
        prepare(write_plan(tmp_path, edit))


def test_different_editor_budget_cannot_enter_same_comparison(tmp_path):
    path = write_plan(tmp_path)
    config_path = tmp_path / "candidate.yaml"
    data = yaml.safe_load(config_path.read_text())
    data["editor"]["budget"]["max_turns"] += 1
    config_path.write_text(yaml.safe_dump(data))
    with pytest.raises(EvaluationError, match="matched"):
        prepare(path)


def test_generation_seeds_have_separate_stores_and_input_changes_have_new_namespaces(tmp_path):
    path = write_plan(tmp_path)
    a = prepare(path)
    raw = yaml.safe_load(path.read_text())
    raw["generation_seeds"] = [11, 12]
    path.write_text(yaml.safe_dump(raw))
    b = prepare(path)
    assert a.root != b.root
    assert module._job(b, 0, 11).runs_dir != module._job(b, 0, 12).runs_dir
    assert preview(b)["max_writer_generations"] == 4


def test_existing_output_evidence_is_never_adopted_or_overwritten(tmp_path, monkeypatch):
    prepared = prepare(write_plan(tmp_path))
    prepared.root.mkdir(parents=True)
    evidence = prepared.root / "unrelated.json"
    evidence.write_text("preserve")
    monkeypatch.setattr(module, "make_runner", forbidden)
    with pytest.raises(EvaluationError, match="unowned"):
        execute(prepared)
    assert evidence.read_text() == "preserve"


def test_real_example_previews_without_a_trained_model_or_container(monkeypatch):
    monkeypatch.setattr(module, "make_runner", forbidden)
    prepared = prepare(ROOT / "configs/evaluation.example.yaml")
    result = preview(prepared)
    assert len(result["task_ids"]) == 16
    assert result["max_writer_generations"] == 32
    assert result["max_edit_checkpoints"] == 576
    with pytest.raises(EvaluationError, match="trained writer"):
        execute(prepared)


def test_external_model_endpoints_are_rejected_before_inference(tmp_path):
    cfg = config(tmp_path)
    cfg = replace(
        cfg,
        writer=replace(
            cfg.writer,
            backend=replace(
                cfg.writer.backend,
                kind="openai_compat",
                fixtures=None,
                base_url="https://api.example.com/v1",
                model="remote",
            ),
        ),
    )
    with pytest.raises(EvaluationError, match="loopback"):
        module._local_only(cfg)
