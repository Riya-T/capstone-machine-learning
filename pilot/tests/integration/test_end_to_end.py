"""End-to-end test of collection with the mock writer and editor on
record_store, in the real Docker sandbox.

The mock writer offers two programs, "modular" and "tangled" (both the v0
reference, told apart by a marker comment), and the seed is chosen so the
three writer samples give one of them twice: two distinct candidates and one
duplicate. The mock editor applies the right reference for each change to
the modular candidate (checking with RUN_CHECKS first), so it completes both
changes in every trial: score 2. For the tangled candidate, its second change
in each sequence breaks earlier behavior: score 1. Expected: exactly one
pair, modular over tangled, with the duplicate excluded.

Then: a complete rerun makes no model calls and leaves the store identical;
a trial whose second step is deleted resumes and replays it from the cache
with no model calls; `report` rebuilds the same files without building any
backend; `validate-tasks` passes.

Usage:
    uv run pytest tests/integration/test_end_to_end.py -rs
"""

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from pipeline import collect as collect_module
from pipeline.__main__ import main
from pipeline.backends import derive_seed
from pipeline.collect import collect
from pipeline.config import load_config
from pipeline.parser import render_program
from pipeline.registry import load_tasks

PILOT = Path(__file__).resolve().parents[2]
pytestmark = [pytest.mark.docker, pytest.mark.slow]

TASK = load_tasks(load_config(PILOT / "configs" / "pilot_mock.yaml").tasks)["record_store"]
S1, S2 = TASK.sequence("s1").steps, TASK.sequence("s2").steps


def variant(name: str, program) -> str:
    """The program with a marker line the mock rules can recognize."""
    marked = {p: f"# mock-variant: {name}\n".encode() + data for p, data in program.items()}
    return render_program(marked)


def all_of(*patterns: str) -> str:
    return "(?s)^" + "".join(f"(?=.*{p})" for p in patterns)


TXN, CONFLICT, UNIQUE = "Add transactions", "Add optimistic", "email to be unique"
HAS_UNIQUE = "_check_unique_email"
EDITOR_RULES = [
    # After RUN_CHECKS, the next prompt starts its feedback with the results.
    (r"Result of your last action\s*\n\s*Public checks:", "DONE"),
    (all_of("variant: modular", TXN), variant("modular", S1[1].reference) + "RUN_CHECKS"),
    (
        all_of("variant: modular", CONFLICT, HAS_UNIQUE),
        variant("modular", S2[1].reference) + "RUN_CHECKS",
    ),
    (all_of("variant: modular", CONFLICT), variant("modular", S1[0].reference) + "RUN_CHECKS"),
    (all_of("variant: modular", UNIQUE), variant("modular", S2[0].reference) + "RUN_CHECKS"),
    # Tangled: the second change of each sequence breaks earlier behavior.
    (
        all_of("variant: tangled", TXN),
        variant("tangled", S1[1].planted_bugs[0].program) + "DONE",
    ),
    # (the conflict-only reference: it drops the unique-email rule)
    (
        all_of("variant: tangled", CONFLICT, HAS_UNIQUE),
        variant("tangled", S1[0].reference) + "DONE",
    ),
    (all_of("variant: tangled", CONFLICT), variant("tangled", S1[0].reference) + "DONE"),
    (all_of("variant: tangled", UNIQUE), variant("tangled", S2[0].reference) + "DONE"),
]  # fmt: skip


def writer_seed() -> tuple[int, str]:
    """A base seed whose three writer samples pick both mock answers, one of
    them twice (the mock answers responses[seed % 2])."""
    for seed in range(1000):
        picks = [derive_seed(seed, TASK.id, "writer", i) % 2 for i in range(3)]
        if len(set(picks)) == 2:
            twice = max(set(picks), key=picks.count)
            return seed, ("modular", "tangled")[twice]
    raise AssertionError("no seed gives two distinct samples")


def write_rules(path: Path, rules) -> Path:
    data = {"rules": [{"match": m, "responses": [{"text": t}]} for m, t in rules]}
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("e2e")
    seed, duplicated = writer_seed()
    writer = {"rules": [{"match": "Produce exactly these files: records\\.py", "responses": [
        {"text": variant("modular", TASK.reference)},
        {"text": variant("tangled", TASK.reference)},
    ]}]}  # fmt: skip
    (tmp / "writer.yaml").write_text(yaml.safe_dump(writer, sort_keys=False))
    write_rules(tmp / "editor.yaml", EDITOR_RULES)

    cfg = yaml.safe_load((PILOT / "configs" / "base.yaml").read_text())
    cfg.update(name="e2e", seed=seed, allow_dirty=True, runs_dir=str(tmp / "runs"))
    cfg["tasks"].update(dir=str(PILOT / "tasks"), include=["record_store"])
    cfg["writer"].update(samples_per_task=3, prompt_template=str(PILOT / "prompts/writer_v1.md"))
    cfg["writer"]["backend"]["fixtures"] = str(tmp / "writer.yaml")
    cfg["editor"]["prompt_template"] = str(PILOT / "prompts/editor_v1.md")
    cfg["editor"]["backend"]["fixtures"] = str(tmp / "editor.yaml")
    cfg["sandbox"]["build_context"] = str(PILOT / "sandbox")
    cfg["execution"] = {"sandbox_workers": 8}
    path = tmp / "e2e.yaml"
    path.write_text(yaml.safe_dump(cfg, sort_keys=False))

    first = collect(load_config(path))
    return path, first, duplicated


def dump(db_path: Path) -> dict:
    """Every table except runs (each run adds its own record), sorted."""
    db = sqlite3.connect(db_path)
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    out = {t: sorted(map(tuple, db.execute(f"SELECT * FROM {t}"))) for t in tables if t != "runs"}
    db.close()
    return out


def outputs(directory: Path) -> tuple[str, dict]:
    pairs = (directory / "preferences.jsonl").read_text()
    report = json.loads((directory / "preferences_report.json").read_text())
    return pairs, report


def test_first_run_scores_and_pairs(setup):
    path, first, duplicated = setup
    assert first.model_calls > 0 and first.samples_recorded == 3 and first.pairs == 1
    pairs_text, report = outputs(first.run_dir)

    assert report["samples"] == {
        "eligible": 2,
        "initially_failing": 0,
        "duplicate": 1,
        "infra_error": 0,
        "incomplete": 0,
    }
    assert report["tasks"]["record_store"]["score_histogram"] == {"s1": [0, 3, 3], "s2": [0, 3, 3]}
    # modular: 12 successful steps; tangled: 6 successes, then 6 broken steps.
    assert report["step_endings"] == {"fail_existing": 6, "success": 18}
    for combo in ("strict/all_pairs", "weak_dominance/all_pairs", "weak_dominance/best_vs_worst"):
        assert report["combinations"][combo]["pair_yield"] == 1

    (pair,) = [json.loads(line) for line in pairs_text.splitlines()]
    assert "# mock-variant: modular" in pair["chosen"]
    assert "# mock-variant: tangled" in pair["rejected"]
    assert pair["chosen_scores"] == [[2, 2, 2], [2, 2, 2]]
    assert pair["rejected_scores"] == [[1, 1, 1], [1, 1, 1]]
    assert pair["strict_subset"] is True
    # The duplicated variant's pair entry lists both of its writer answers.
    calls = {"modular": pair["chosen_call_keys"], "tangled": pair["rejected_call_keys"]}
    assert len(calls[duplicated]) == 2 and sum(len(k) for k in calls.values()) == 3

    run = json.loads((first.run_dir / "run.json").read_text())
    assert len(run["git_commit"]) == 40 and run["config"]["name"] == "e2e"


def test_rerun_makes_no_model_calls_and_changes_nothing(setup):
    path, first, _ = setup
    db = load_config(path).runs_dir / "pipeline.sqlite"
    before = dump(db)
    second = collect(load_config(path))
    assert second.model_calls == 0
    assert (second.samples_recorded, second.initial_checks_recorded, second.steps_recorded) == (
        0,
        0,
        0,
    )
    assert dump(db) == before
    assert outputs(second.run_dir) == outputs(first.run_dir)


def test_interrupted_trial_resumes_by_replaying_from_the_cache(setup):
    path, first, _ = setup
    db_path = load_config(path).runs_dir / "pipeline.sqlite"
    db = sqlite3.connect(db_path)
    # A modular trial's second step: its turns used RUN_CHECKS, so replaying
    # needs the normalized check output to rebuild identical prompts.
    (cid,) = db.execute(
        "SELECT candidate_id FROM checkpoints WHERE step = 2 AND status = 'success' LIMIT 1"
    ).fetchone()
    where = "candidate_id = ? AND sequence_id = 's1' AND rep = 1 AND step = 2"
    columns = "status, output_blob, new_pass, new_total, existing_pass, existing_total, n_calls"
    before = db.execute(f"SELECT {columns} FROM checkpoints WHERE {where}", (cid,)).fetchone()
    db.execute(f"DELETE FROM checkpoints WHERE {where}", (cid,))
    db.commit()
    db.close()

    resumed = collect(load_config(path))
    assert (resumed.steps_recorded, resumed.model_calls) == (1, 0)
    db = sqlite3.connect(db_path)
    after = db.execute(f"SELECT {columns} FROM checkpoints WHERE {where}", (cid,)).fetchone()
    db.close()
    assert after == before


def test_report_rebuilds_the_files_without_any_backend(setup, tmp_path, monkeypatch):
    path, first, _ = setup

    def no_backends(*args, **kwargs):
        raise AssertionError("report must not build a backend")

    monkeypatch.setattr(collect_module, "make_backend", no_backends)
    assert main(["report", "--config", str(path), "--out", str(tmp_path / "report")]) == 0
    assert outputs(tmp_path / "report") == outputs(first.run_dir)


def test_validate_tasks_command(setup):
    path, _, _ = setup
    assert main(["validate-tasks", "--config", str(path)]) == 0


def test_staged_run_stops_after_each_stage(setup, tmp_path):
    path, _, _ = setup
    staged = tmp_path / "staged.yaml"
    data = yaml.safe_load(path.read_text())
    data["runs_dir"] = str(tmp_path / "runs")
    staged.write_text(yaml.safe_dump(data, sort_keys=False))
    db = tmp_path / "runs" / "pipeline.sqlite"

    def count(table):
        conn = sqlite3.connect(db)
        (n,) = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        conn.close()
        return n

    writer = collect(load_config(staged), until="writer")
    assert (count("candidates"), count("initial_checks"), count("checkpoints")) == (3, 0, 0)
    _, report = outputs(writer.run_dir)
    assert report["candidates"]["record_store"]["flag"] == "initial checks pending"
    assert (writer.run_dir / "summary.txt").read_text().startswith("Candidates")

    initial = collect(load_config(staged), until="initial")
    assert initial.model_calls == 0  # the samples were already collected
    assert (count("initial_checks"), count("checkpoints")) == (2, 0)
    _, report = outputs(initial.run_dir)
    stats = report["candidates"]["record_store"]
    assert (stats["distinct"], stats["passed_initial"]) == (2, 2)
    assert stats["distinct_normalized"] == 1  # modular and tangled differ only in a comment
    assert stats["flag"] == "fewer than 3 distinct passing programs"
