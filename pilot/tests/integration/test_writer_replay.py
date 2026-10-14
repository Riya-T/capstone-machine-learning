"""Integration: registry -> writer prompt -> CachedBackend(MockBackend) ->
parser -> store, using the committed pilot_mock config and record_store task.

These tests drive the real modules together the way collection will: one
CachedBackend per writer sample, seeds from derive_seed, answers parsed and
stored. They check that a second pass replays everything with no model
calls, both from an in-memory cache and from the SQLite store after closing
and reopening it.
"""

import time
from pathlib import Path

import pytest

from pipeline.backends import (
    CachedBackend,
    InMemoryCallCache,
    MockBackend,
    derive_seed,
    make_backend,
)
from pipeline.config import load_config
from pipeline.parser import parse_program
from pipeline.registry import build_writer_prompt, load_tasks, load_template, prompt_version
from pipeline.store import Candidate, CandidateKey, Store, writer_cfg_hash

PILOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def setup():
    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    prompt = build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    return cfg, task, prompt


def sample(cfg, task, prompt, cache, sample_idx):
    """One writer sample: returns (backend, answer, parse result)."""
    seed = derive_seed(cfg.seed, task.id, "writer", sample_idx)
    backend = CachedBackend(make_backend(cfg.writer.backend, seed), cache)
    answer = backend.generate(prompt)
    result = parse_program(answer, task.entry_files, backend.last_usage.finish_reason)
    return backend, answer, result


def test_writer_samples_replay_from_the_cache(setup):
    cfg, task, prompt = setup
    cache = InMemoryCallCache()
    first = [sample(cfg, task, prompt, cache, i) for i in range(cfg.writer.samples_per_task)]

    for backend, _, result in first:
        assert backend.model_calls == 1
        assert result.ok and result.files == task.reference  # the fixture answers with v0
        # The writer saw only the WriterView: no change, private test or
        # later public check reached the model.
        (sent,) = backend.inner.prompts
        assert sent == prompt
        for change in task.changes.values():
            assert change.id not in sent
            assert change.request not in sent

    replay = [sample(cfg, task, prompt, cache, i) for i in range(cfg.writer.samples_per_task)]
    assert [answer for _, answer, _ in replay] == [answer for _, answer, _ in first]
    assert all(b.model_calls == 0 and b.last_was_cached for b, _, _ in replay)
    assert all(b.inner.prompts == [] for b, _, _ in replay)  # the mock was never asked


def collect_candidates(store: Store, cfg, task, prompt, run_id: str) -> int:
    """A minimal writer collection pass; returns how many model calls it made."""
    pv, wh = prompt_version(prompt), writer_cfg_hash(cfg)
    calls = 0
    for i in range(cfg.writer.samples_per_task):
        start = time.monotonic()
        backend, _, result = sample(cfg, task, prompt, store, i)
        calls += backend.model_calls
        usage = backend.last_usage
        store.record_candidate(
            Candidate(
                key=CandidateKey(task.id, pv, wh, i),
                candidate_id=store.put_blob(result.files) if result.ok else None,
                parse_error=None if result.ok else str(result.failure),
                tokens_in=usage.prompt_tokens,
                tokens_out=usage.completion_tokens,
                wall_s=time.monotonic() - start,
                run_id=run_id,
            )
        )
    return calls


def test_close_and_reopen_replays_from_sqlite(setup, tmp_path):
    cfg, task, prompt = setup
    with Store(tmp_path / "runs") as store:
        first_run = store.start_run(cfg)
        assert (
            collect_candidates(store, cfg, task, prompt, first_run) == cfg.writer.samples_per_task
        )
        before = store.candidates(task.id, prompt_version(prompt), writer_cfg_hash(cfg))

    with Store(tmp_path / "runs") as store:
        second_run = store.start_run(cfg)
        # Re-recording the same candidates with new timings and a new run id
        # is a no-op, not a conflict.
        assert collect_candidates(store, cfg, task, prompt, second_run) == 0
        after = store.candidates(task.id, prompt_version(prompt), writer_cfg_hash(cfg))
        assert after == before
        assert {c.run_id for c in after} == {first_run}
        for c in after:
            assert store.get_blob(c.candidate_id) == task.reference


def test_identical_samples_share_one_candidate_id(setup, tmp_path):
    # The mock fixture gives every sample the same program: one blob, and
    # identical candidate ids, which is what dedup will key on.
    cfg, task, prompt = setup
    with Store(tmp_path / "runs") as store:
        collect_candidates(store, cfg, task, prompt, store.start_run(cfg))
        ids = {
            c.candidate_id
            for c in store.candidates(task.id, prompt_version(prompt), writer_cfg_hash(cfg))
        }
        assert len(ids) == 1
        assert len(list(store.blob_dir.glob("*.json"))) == 1


def test_mock_prompts_are_recorded_for_leak_checks(setup):
    cfg, task, prompt = setup
    mock = MockBackend(cfg.writer.backend, seed=0)
    mock.generate(prompt)
    assert mock.prompts == [prompt]
