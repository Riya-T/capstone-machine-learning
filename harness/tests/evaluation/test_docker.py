"""Optional real sandbox smoke for evaluation orchestration and saved-only replay.

Usage:
    uv run pytest tests/evaluation/test_docker.py --slow -rs
    # Uses reference/mock fixture code only; not experimental model evidence.
"""

import json
from pathlib import Path

import pytest
import yaml

from harness.config import load_config
from harness.evaluation.plan import execute, prepare
from harness.models.parser import render_program
from harness.registry import load_tasks

from .helpers import ROOT
from .test_plan import write_plan

pytestmark = [pytest.mark.docker, pytest.mark.slow]


def test_real_sandbox_mock_evaluation_and_completed_resume(tmp_path, monkeypatch):
    path = write_plan(tmp_path)
    cfg = load_config(ROOT / "configs/mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    fixtures = tmp_path / "writer-reference.yaml"
    fixtures.write_text(
        yaml.safe_dump(
            {
                "rules": [
                    {
                        "match": "",
                        "responses": [{"text": render_program(dict(task.reference))}],
                    }
                ]
            }
        ),
        encoding="utf8",
    )
    for name in ("original", "candidate"):
        config_path = tmp_path / (name + ".yaml")
        raw = yaml.safe_load(config_path.read_text())
        raw["writer"]["backend"]["fixtures"] = str(fixtures)
        config_path.write_text(yaml.safe_dump(raw), encoding="utf8")
    prepared = prepare(path)
    result = execute(prepared)
    assert result["complete"]
    report = json.loads(Path(result["reports"]["comparison.json"]).read_text())
    for method in report["methods"].values():
        assert method["metrics"]["initial_correctness"]["estimate"] == 1
        assert method["metrics"]["change_completion"]["estimate"] == 0

    def forbidden(*a, **kw):
        raise AssertionError("Completed resume must not create a runner or model")

    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    monkeypatch.setattr("harness.evaluation.plan.collect", forbidden)
    assert execute(prepared) == result
    assert execute(prepared, export_only=True)["complete"]
