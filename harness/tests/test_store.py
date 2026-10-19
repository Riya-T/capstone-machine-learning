"""Tests for harness.store: result keys, run logging (against a temporary git
repository), program files, write-once rows, resuming, reopening the
database, and the saved model-call cache.

Usage:
    uv run pytest tests/test_store.py
"""

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from harness.config import BackendConfig, load_config
from harness.models.backends import CachedBackend, MockBackend, Usage, derive_seed
from harness.store import (
    Candidate,
    CandidateKey,
    Checkpoint,
    InitialCheck,
    ResumePoint,
    Store,
    StoreError,
    TrialKey,
    editor_cfg_hash,
    git_state,
    resume_point,
    sandbox_cfg_hash,
    writer_cfg_hash,
)

from .helpers import minimal, write

# --- fixtures ---------------------------------------------------------------


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path) -> Path:
    """A git repository holding a committed config; returns the config path.
    runs/ is ignored, as in the real repository."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    path = write(root / "configs", minimal())
    (root / ".gitignore").write_text("configs/runs/\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return path


@pytest.fixture
def store(tmp_path):
    with Store(tmp_path / "runs") as s:
        yield s


@pytest.fixture
def run_id(store, repo):
    return store.start_run(load_config(repo), repo_dir=repo.parent)


def edit_config(path: Path, change) -> None:
    data = yaml.safe_load(path.read_text())
    change(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


# --- key composition --------------------------------------------------------


IMAGE = "sha256:" + "1" * 64


def keys(path: Path) -> tuple[str, str, str]:
    cfg = load_config(path)
    return writer_cfg_hash(cfg), editor_cfg_hash(cfg, IMAGE), sandbox_cfg_hash(cfg, IMAGE)


def test_writer_key_changes_when_only_the_template_contents_change(repo):
    writer, editor, sandbox = keys(repo)
    template = repo.parent / "writer.md"
    template.write_text(template.read_text() + "\nThink step by step.")
    assert keys(repo) == (keys(repo)[0], editor, sandbox)
    assert keys(repo)[0] != writer


def test_editor_key_changes_when_only_the_sandbox_changes(repo):
    writer, editor, sandbox = keys(repo)
    edit_config(repo, lambda d: d["sandbox"].update(image="img@sha256:abc"))
    new_writer, new_editor, new_sandbox = keys(repo)
    assert new_writer == writer
    assert new_editor != editor
    assert new_sandbox != sandbox


def test_rebuilt_image_under_the_same_tag_changes_editor_and_sandbox_keys(repo):
    cfg = load_config(repo)
    rebuilt = "sha256:" + "2" * 64
    assert editor_cfg_hash(cfg, rebuilt) != editor_cfg_hash(cfg, IMAGE)
    assert sandbox_cfg_hash(cfg, rebuilt) != sandbox_cfg_hash(cfg, IMAGE)


def test_editor_key_changes_with_the_editor_section_only(repo):
    writer, editor, sandbox = keys(repo)
    edit_config(repo, lambda d: d["editor"].update(max_check_output_chars=500))
    assert keys(repo) == (writer, keys(repo)[1], sandbox)
    assert keys(repo)[1] != editor


def test_editor_key_changes_when_only_the_editor_template_contents_change(repo):
    writer, editor, sandbox = keys(repo)
    (repo.parent / "editor.md").write_text("$request $files $feedback $allowed_files $turns_left!")
    assert keys(repo) == (writer, keys(repo)[1], sandbox)
    assert keys(repo)[1] != editor


def test_writer_key_changes_with_mock_fixture_contents(repo):
    writer, _, _ = keys(repo)
    (repo.parent / "mock.yaml").write_text("rules:\n  - match: x\n    responses: [{text: y}]\n")
    assert keys(repo)[0] != writer


def test_editor_protocol_version_is_part_of_the_editor_key(repo, monkeypatch):
    # Editor code changes that alter behavior bump the version, so old trials
    # are not reused.
    import harness.store as store_module

    writer, editor, sandbox = keys(repo)
    monkeypatch.setattr(store_module, "EDITOR_PROTOCOL_VERSION", 999)
    assert keys(repo) == (writer, keys(repo)[1], sandbox)
    assert keys(repo)[1] != editor


def test_sample_and_rep_counts_are_not_part_of_the_keys(repo):
    # Sample i and rep k don't depend on the totals, so growing either keeps
    # what was already collected.
    before = keys(repo)
    edit_config(repo, lambda d: d["writer"].update(samples_per_task=32))
    edit_config(repo, lambda d: d["editor"].update(reps=5))
    assert keys(repo) == before


def test_unrelated_sections_do_not_change_either_key(repo):
    before = keys(repo)
    edit_config(repo, lambda d: d["scorer"].update(pairing_mode="all_pairs"))
    edit_config(repo, lambda d: d.update(execution={"sandbox_workers": 8}))
    edit_config(repo, lambda d: d.update(name="renamed", seed=99))
    assert keys(repo) == before


def test_keys_do_not_depend_on_checkout_location(repo, tmp_path):
    shutil.copytree(repo.parent.parent, tmp_path / "elsewhere")
    assert keys(tmp_path / "elsewhere" / "configs" / repo.name) == keys(repo)


# --- runs -------------------------------------------------------------------


def test_run_records_commit_and_full_config(store, repo):
    cfg = load_config(repo)
    run_id = store.start_run(cfg, repo_dir=repo.parent)
    run = store.get_run(run_id)
    assert run["git_commit"] == git(repo.parent.parent, "rev-parse", "HEAD")
    assert run["git_dirty"] is False
    assert run["config"] == cfg.to_dict()
    assert run["config_hash"] == cfg.config_hash
    on_disk = json.loads((store.runs_dir / run_id / "run.json").read_text())
    assert on_disk["git_commit"] == run["git_commit"]
    assert on_disk["config"] == cfg.to_dict()


def test_dirty_tree_is_refused_unless_allowed(store, repo):
    (repo.parent / "notes.txt").write_text("untracked files count as changes")
    with pytest.raises(StoreError, match="uncommitted changes"):
        store.start_run(load_config(repo), repo_dir=repo.parent)
    edit_config(repo, lambda d: d.update(allow_dirty=True))
    run_id = store.start_run(load_config(repo), repo_dir=repo.parent)
    assert store.get_run(run_id)["git_dirty"] is True


def test_outside_a_git_repository_is_an_error(tmp_path):
    with pytest.raises(StoreError, match="cannot read git state"):
        git_state(tmp_path)


def test_run_ids_are_unique(store, repo):
    cfg = load_config(repo)
    assert store.start_run(cfg, repo_dir=repo.parent) != store.start_run(cfg, repo_dir=repo.parent)


# --- blobs ------------------------------------------------------------------

programs = st.dictionaries(
    st.text(alphabet="abcdefghij/._", min_size=1, max_size=12), st.binary(max_size=200), max_size=4
)


@settings(max_examples=50, deadline=None)
@given(programs)
def test_blobs_preserve_exact_bytes(tmp_path_factory, files):
    with Store(tmp_path_factory.mktemp("runs")) as s:
        assert s.get_blob(s.put_blob(files)) == files


def test_blob_hash_ignores_insertion_order(store):
    a = store.put_blob({"a.py": b"1", "b.py": b"2"})
    assert store.put_blob({"b.py": b"2", "a.py": b"1"}) == a
    assert store.put_blob({"a.py": b"1", "b.py": b"3"}) != a


def test_corrupt_blob_is_detected(store):
    digest = store.put_blob({"m.py": b"x = 1\n"})
    (store.blob_dir / f"{digest}.json").write_text('{"m.py": "eCA9IDIK"}')  # x = 2
    with pytest.raises(StoreError, match="corrupt"):
        store.get_blob(digest)


def test_missing_blob_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_blob("0" * 64)


# --- candidates and initial checks ------------------------------------------


def candidate(run_id, idx=0, cid="c1", **overrides) -> Candidate:
    values = dict(
        key=CandidateKey("t", "pv", "wh", idx),
        candidate_id=cid,
        parse_error=None,
        tokens_in=10,
        tokens_out=20,
        wall_s=1.5,
        run_id=run_id,
    )
    values.update(overrides)
    return Candidate(**values)


def test_candidates_round_trip_in_sample_order(store, run_id):
    for idx in (2, 0, 1):
        store.record_candidate(candidate(run_id, idx, cid=f"c{idx}"))
    found = store.candidates("t", "pv", "wh")
    assert [c.key.sample_idx for c in found] == [0, 1, 2]
    assert found[0] == candidate(run_id, 0, cid="c0")
    assert store.get_candidate(CandidateKey("t", "pv", "other", 0)) is None


def test_unparseable_candidate_is_recorded_without_an_id(store, run_id):
    store.record_candidate(candidate(run_id, cid=None, parse_error="no code block"))
    assert store.get_candidate(CandidateKey("t", "pv", "wh", 0)).parse_error == "no code block"


def test_recording_the_same_result_twice_is_a_no_op(store, run_id):
    store.record_candidate(candidate(run_id))
    store.record_candidate(candidate(run_id))
    assert len(store.candidates("t", "pv", "wh")) == 1


def test_a_different_result_under_the_same_key_is_refused(store, run_id):
    store.record_candidate(candidate(run_id))
    with pytest.raises(StoreError, match=r"differs in \['candidate_id', 'parse_error'\]"):
        store.record_candidate(candidate(run_id, cid="c9", parse_error="x", wall_s=2.0))


def test_measurements_are_not_compared_and_keep_their_first_values(store, run_id, repo):
    # A replayed rerun takes ~0 s and belongs to a new run; that is not a
    # different result.
    store.record_candidate(candidate(run_id))
    rerun = store.start_run(load_config(repo), repo_dir=repo.parent)
    store.record_candidate(candidate(rerun, wall_s=0.01, tokens_in=1, tokens_out=2))
    assert store.get_candidate(CandidateKey("t", "pv", "wh", 0)) == candidate(run_id)

    store.record_checkpoint(step(run_id, 1, "fail_new", "b1", wall_s=9.0, n_calls=3))
    store.set_failure_cause(TRIAL, 1, "editor_mistake")
    store.record_checkpoint(step(rerun, 1, "fail_new", "b1", wall_s=0.1, n_calls=0))
    (stored,) = store.trial_steps(TRIAL)
    assert (stored.wall_s, stored.n_calls, stored.run_id) == (9.0, 3, run_id)
    assert stored.failure_cause == "editor_mistake"


def test_outcome_columns_of_checkpoints_are_compared(store, run_id):
    store.record_checkpoint(step(run_id, 1, "success", "b1", new_pass=3, new_total=3))
    with pytest.raises(StoreError, match=r"differs in \['new_pass'\]"):
        store.record_checkpoint(step(run_id, 1, "success", "b1", new_pass=2, new_total=3))


def test_initial_checks_are_keyed_by_task_version_and_sandbox(store, run_id):
    check = InitialCheck("t", "tv1", "c1", "sb1", True, {"initial": [3, 3]}, run_id)
    store.record_initial_check(check)
    assert store.get_initial_check("t", "tv1", "c1", "sb1") == check
    assert store.get_initial_check("t", "tv2", "c1", "sb1") is None  # tests were fixed
    assert store.get_initial_check("t", "tv1", "c1", "sb2") is None  # new sandbox image


# --- checkpoints ------------------------------------------------------------

TRIAL = TrialKey("t", "tv", "c1", "s1", 0, "eh")


def step(run_id, number, status, blob=None, trial=TRIAL, **extra) -> Checkpoint:
    return Checkpoint(trial, number, f"change{number}", status, blob, run_id=run_id, **extra)


def test_trial_steps_round_trip_in_order(store, run_id):
    second = step(run_id, 2, "fail_existing", "b2", new_pass=3, new_total=3, existing_pass=4,
                  existing_total=5, tokens_in=100, tokens_out=50, n_calls=2, wall_s=3.5,
                  diff_lines=12)  # fmt: skip
    store.record_checkpoint(second)
    store.record_checkpoint(step(run_id, 1, "success", "b1"))
    assert store.trial_steps(TRIAL) == [step(run_id, 1, "success", "b1"), second]
    other = TrialKey("t", "tv", "c1", "s1", 1, "eh")
    assert store.trial_steps(other) == []


def test_checkpoints_are_write_once(store, run_id):
    store.record_checkpoint(step(run_id, 1, "success", "b1"))
    store.record_checkpoint(step(run_id, 1, "success", "b1"))
    with pytest.raises(StoreError, match="differs in"):
        store.record_checkpoint(step(run_id, 1, "fail_new", "b1"))


def test_infra_error_step_can_be_replaced_by_a_retry(store, run_id):
    store.record_checkpoint(step(run_id, 1, "infra_error"))
    store.record_checkpoint(step(run_id, 1, "success", "b1"))
    assert [c.status for c in store.trial_steps(TRIAL)] == ["success"]


def test_failure_cause_can_be_labelled_later(store, run_id):
    store.record_checkpoint(step(run_id, 1, "fail_new", "b1"))
    store.set_failure_cause(TRIAL, 1, "editor_mistake")
    assert store.trial_steps(TRIAL)[0].failure_cause == "editor_mistake"
    with pytest.raises(KeyError):
        store.set_failure_cause(TRIAL, 2, "editor_mistake")


def test_checkpoint_needs_a_recorded_run(store):
    with pytest.raises(sqlite3.IntegrityError):
        store.record_checkpoint(step("no-such-run", 1, "success", "b1"))


def test_all_checkpoints_lists_every_trial(store, run_id):
    other = TrialKey("t", "tv", "c2", "s1", 0, "eh")
    store.record_checkpoint(step(run_id, 1, "success", "b1"))
    store.record_checkpoint(step(run_id, 1, "fail_new", "b9", trial=other))
    assert [(c.trial.candidate_id, c.step) for c in store.all_checkpoints()] == [
        ("c1", 1),
        ("c2", 1),
    ]


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([], ResumePoint(1, None)),
        (["success"], ResumePoint(2, "b1")),
        (["success", "success"], ResumePoint(None, None)),
        (["fail_new"], ResumePoint(None, None)),
        (["budget_exhausted"], ResumePoint(None, None)),
        (["success", "fail_both"], ResumePoint(None, None)),
        (["infra_error"], ResumePoint(1, None)),
        (["success", "infra_error"], ResumePoint(2, "b1")),
    ],
)
def test_resume_point(statuses, expected):
    steps = [step("r", i, s, f"b{i}") for i, s in enumerate(statuses, start=1)]
    assert resume_point(steps, length=2) == expected


def test_resume_point_with_a_missing_middle_step():
    # Only possible after a crash between the delete and insert of an
    # infra_error retry; step 2 runs again on step 1's output.
    steps = [step("r", 1, "success", "b1"), step("r", 3, "success", "b3")]
    assert resume_point(steps, length=3) == ResumePoint(2, "b1")


# --- persistence ------------------------------------------------------------


def test_everything_survives_reopening(tmp_path, repo):
    with Store(tmp_path / "runs") as s:
        run_id = s.start_run(load_config(repo), repo_dir=repo.parent)
        s.record_candidate(candidate(run_id))
        s.record_checkpoint(step(run_id, 1, "success", "b1"))
        blob = s.put_blob({"m.py": b"pass\n"})
    with Store(tmp_path / "runs") as s:
        assert s.get_run(run_id)["git_commit"]
        assert s.candidates("t", "pv", "wh") == [candidate(run_id)]
        assert s.trial_steps(TRIAL) == [step(run_id, 1, "success", "b1")]
        assert s.get_blob(blob) == {"m.py": b"pass\n"}


def test_other_schema_version_is_refused(tmp_path):
    Store(tmp_path / "runs").close()
    db = sqlite3.connect(tmp_path / "runs" / "harness.sqlite")
    db.execute("PRAGMA user_version=99")
    db.close()
    with pytest.raises(StoreError, match="store schema 99"):
        Store(tmp_path / "runs")


# --- model call cache -------------------------------------------------------


class Sampler:
    """Answers differently on every call, like a sampled model, and counts
    calls that reach it."""

    def __init__(self, identity: str):
        self.identity = identity
        self.calls = 0
        self.last_usage = None

    def generate(self, prompt: str, call_index: int = 0) -> str:
        self.calls += 1
        self.last_usage = Usage(len(prompt), self.calls, "stop")
        return f"{self.identity}:{prompt}:{self.calls}"


def test_call_cache_persists_text_and_usage(tmp_path):
    with Store(tmp_path / "runs") as s:
        CachedBackend(Sampler("x"), s).generate("p")
    with Store(tmp_path / "runs") as s:
        inner = Sampler("x")
        replay = CachedBackend(inner, s)
        assert replay.generate("p") == "x:p:1"
        assert replay.last_usage == Usage(1, 1, "stop")
        assert inner.calls == 0


def test_two_trials_with_separate_cached_backends_replay_correctly(tmp_path):
    """Two trials run interleaved, each through its own CachedBackend on the
    shared store. After reopening, each trial replays exactly its own
    answers, in its own order, whatever order the trials are replayed in,
    with no model calls."""
    with Store(tmp_path / "runs") as s:
        a, b = CachedBackend(Sampler("A"), s), CachedBackend(Sampler("B"), s)
        first = {
            "a": [a.generate("p"), None, a.generate("p"), None],
            "b": [None, b.generate("p"), None, b.generate("q")],
        }
        # Same prompt, same position, different trial: different answers.
        assert first["a"][0] == "A:p:1" and first["b"][1] == "B:p:1"

    with Store(tmp_path / "runs") as s:
        inner_a, inner_b = Sampler("A"), Sampler("B")
        a, b = CachedBackend(inner_a, s), CachedBackend(inner_b, s)
        # Replay b entirely before a: the order across trials doesn't matter.
        assert [b.generate("p"), b.generate("q")] == ["B:p:1", "B:q:2"]
        assert [a.generate("p"), a.generate("p")] == ["A:p:1", "A:p:2"]
        assert inner_a.calls == inner_b.calls == 0
        assert a.model_calls == b.model_calls == 0


def test_trials_with_derived_seeds_replay_their_own_mock_answers(tmp_path):
    """The realistic case: both trials use the same mock editor config and
    differ only in their derived seed, which picks different responses."""
    fixtures = tmp_path / "f.yaml"
    fixtures.write_text("rules:\n  - match: ''\n    responses: [{text: r0}, {text: r1}]\n")
    cfg = BackendConfig(kind="mock", model="m", temperature=0.7, max_tokens=8, fixtures=fixtures)
    seeds = [derive_seed(1, "t", "c1", "s1", rep) for rep in (0, 1, 2, 3)]
    assert len({s % 2 for s in seeds}) == 2  # both responses get used

    with Store(tmp_path / "runs") as s:
        first = [CachedBackend(MockBackend(cfg, seed), s).generate("edit") for seed in seeds]
    with Store(tmp_path / "runs") as s:
        backends = [CachedBackend(MockBackend(cfg, seed), s) for seed in seeds]
        assert [b.generate("edit") for b in reversed(backends)] == first[::-1]
        assert all(b.last_was_cached for b in backends)
        assert first == [f"r{seed % 2}" for seed in seeds]
