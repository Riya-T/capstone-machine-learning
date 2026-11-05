"""Tests for Radon-ranked static baseline preferences.

Usage:
    uv run pytest tests/test_static_ranking.py
"""

import json
from dataclasses import replace
from pathlib import Path

from scripts.static_ranking import (
    RankedProgram,
    build_preferences,
    maintainability_score,
    make_preferences,
)

from harness.collection.collect import Keys
from harness.config import load_config
from harness.models.parser import render_program
from harness.registry import build_writer_prompt, load_tasks, load_template, prompt_version
from harness.store import Candidate, CandidateKey, InitialCheck, Store
from harness.train_dpo import load_preferences


def program(candidate_id: str, score: float, source: str) -> RankedProgram:
    return RankedProgram(candidate_id, {"main.py": source.encode()}, score, ())


def test_maintainability_score_prefers_simple_code():
    simple = {"main.py": b"def value(x):\n    return x + 1\n"}
    complex_source = (
        b"def value(x):\n"
        b"    if x > 0:\n"
        b"        if x > 1:\n"
        b"            if x > 2:\n"
        b"                return x + 1\n"
        b"            else:\n"
        b"                return x + 2\n"
        b"        else:\n"
        b"            return x + 3\n"
        b"    else:\n"
        b"        return x + 4\n"
    )

    assert maintainability_score(simple) > maintainability_score({"main.py": complex_source})


def test_make_preferences_chooses_higher_scores_and_applies_cap():
    programs = [
        program("low", 20.0, "x = 0\n"),
        program("high", 80.0, "x = 1\n"),
        program("middle", 50.0, "x = 2\n"),
    ]

    pairs, stats = make_preferences("example", "write code", programs, per_task_cap=2)

    assert [(pair["chosen_id"], pair["rejected_id"]) for pair in pairs] == [
        ("high", "low"),
        ("high", "middle"),
    ]
    assert pairs[0]["chosen"] == render_program(programs[1].files)
    assert [pair["rule"] for pair in pairs] == ["radon_mi", "radon_mi"]
    assert stats == {
        "programs": 3,
        "comparisons": 3,
        "ties": 0,
        "pairs": 2,
        "capped": 1,
    }


def test_make_preferences_drops_tied_scores():
    pairs, stats = make_preferences(
        "example",
        "write code",
        [program("first", 60.0, "a = 1\n"), program("second", 60.0, "a = 2\n")],
        per_task_cap=8,
    )

    assert pairs == []
    assert stats["ties"] == 1


def test_build_preferences_reads_only_initially_passing_store_programs(tmp_path):
    config_dir = Path(__file__).parents[1] / "configs"
    cfg = replace(load_config(config_dir / "mock.yaml"), runs_dir=tmp_path / "runs")
    task = load_tasks(cfg.tasks)["record_store"]
    prompt = build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    keys = Keys.of(cfg, "sha256:test-image")
    sources = [
        "def get_record(records, key):\n    return records.get(key)\n",
        (
            "def get_record(records, key):\n"
            "    if key in records:\n"
            "        if records[key] is not None:\n"
            "            return records[key]\n"
            "        else:\n"
            "            return None\n"
            "    else:\n"
            "        return None\n"
        ),
    ]

    with Store(cfg.runs_dir) as store:
        run_id = store.start_run(cfg)
        for sample_idx, source in enumerate(sources):
            candidate_id = store.put_blob({"records.py": source.encode()})
            store.record_candidate(
                Candidate(
                    CandidateKey(task.id, prompt_version(prompt), keys.writer, sample_idx),
                    candidate_id,
                    None,
                    1,
                    1,
                    0.1,
                    run_id,
                    call_key=f"call-{sample_idx}",
                )
            )
            store.record_initial_check(
                InitialCheck(
                    task.id, task.task_version, candidate_id, keys.sandbox, True, {}, run_id
                )
            )

    pairs, report = build_preferences(cfg, "sha256:test-image")

    assert len(pairs) == 1
    assert pairs[0]["prompt"] == prompt
    assert pairs[0]["chosen_scores"][0] > pairs[0]["rejected_scores"][0]
    assert pairs[0]["rule"] == "radon_mi"
    assert report["totals"]["pairs"] == 1
    dataset = tmp_path / "preferences.jsonl"
    dataset.write_text(json.dumps(pairs[0]) + "\n")
    assert load_preferences(dataset) == [
        {key: pairs[0][key] for key in ("prompt", "chosen", "rejected")}
    ]
