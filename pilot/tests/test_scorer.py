"""Unit tests for pipeline.scorer against hand-calculated cases: trial scores
(including budget_exhausted and unresolved trials), the strict and
weak_dominance rules, all_pairs and best_vs_worst pairing with deterministic
tie-breaking, per-task caps, ablations (fewer changes, fewer reps), exclusion
counts by reason, the report, and loading records from the store.

Usage:
    uv run pytest tests/test_scorer.py
"""

import json
import random
from fractions import Fraction
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pipeline.config import ConfigError, ScorerConfig, load_config
from pipeline.parser import parse_program
from pipeline.registry import load_tasks
from pipeline.scorer import (
    RULES,
    CandidateRecord,
    Scorer,
    TaskRecord,
    load_task_record,
    strict,
    trial_score,
    weak_dominance,
    write_outputs,
)
from pipeline.store import Candidate, CandidateKey, Checkpoint, InitialCheck, Store, TrialKey

PILOT = Path(__file__).resolve().parents[1]
F = Fraction


# --- trial scores -----------------------------------------------------------


@pytest.mark.parametrize(
    ("steps", "length", "score"),
    [
        ({1: "success", 2: "success"}, 2, 2),
        ({1: "success", 2: "fail_new"}, 2, 1),
        ({1: "fail_existing"}, 2, 0),
        ({1: "fail_both"}, 2, 0),
        ({1: "success", 2: "budget_exhausted"}, 2, 1),  # out of budget is a failure
        ({1: "success", 2: "success"}, 1, 1),  # max_changes=1 truncates
        ({1: "infra_error"}, 2, "infra_error"),
        ({1: "success", 2: "infra_error"}, 2, "infra_error"),
        ({1: "success"}, 2, "incomplete"),
        ({}, 2, "incomplete"),
        ({1: "fail_new", 2: "infra_error"}, 2, 0),  # nothing after the first failure counts
    ],
)
def test_trial_score(steps, length, score):
    assert trial_score(steps, length) == score


def test_unknown_status_is_an_error():
    with pytest.raises(ValueError, match="unknown step status"):
        trial_score({1: "passed"}, 2)


# --- rules ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "strict_verdict", "weak_verdict"),
    [
        ((F(2), F(2)), (F(1), F(1)), "a", "a"),  # higher in every sequence
        ((F(2), F(1)), (F(1), F(1)), "tie", "a"),  # higher, equal: rules differ
        ((F(1), F(1)), (F(1), F(2)), "tie", "b"),
        ((F(2), F(0)), (F(1), F(1)), "inconsistent", "inconsistent"),  # sign flip
        ((F(1), F(1)), (F(1), F(1)), "tie", "tie"),
        ((F(5, 3), F(2)), (F(5, 3), F(2)), "tie", "tie"),  # exact fractions: equal
    ],
)
def test_rules(a, b, strict_verdict, weak_verdict):
    assert strict(a, b) == strict_verdict
    assert weak_dominance(a, b) == weak_verdict


means = st.lists(st.fractions(0, 3, max_denominator=3), min_size=2, max_size=2)
MIRROR = {"a": "b", "b": "a", "tie": "tie", "inconsistent": "inconsistent"}


@given(means, means)
def test_rules_are_antisymmetric(a, b):
    for rule in RULES.values():
        assert rule(b, a) == MIRROR[rule(a, b)]


@given(means, means)
def test_strict_labels_are_a_subset_of_weak_dominance(a, b):
    if strict(a, b) in ("a", "b"):
        assert weak_dominance(a, b) == strict(a, b)


# --- a hand-calculated task -------------------------------------------------
#
# Two sequences, two changes, three reps. Per-sequence rep scores:
#   A: s1 [2, 2, 2]  s2 [2, 1, 2]   means (2, 5/3)  aggregate 11/6
#   B: s1 [1, 1, 1]  s2 [1, 1, 1]   means (1, 1)    aggregate 1
#   C: s1 [2, 2, 2]  s2 [0, 0, 0]   means (2, 0)    aggregate 1
# A vs B: higher in both              -> strict A, weak A
# A vs C: equal in s1, higher in s2   -> strict tie, weak A
# B vs C: lower in s1, higher in s2   -> inconsistent under both
# Plus samples that must be excluded: a duplicate of A, an initially failing
# program, an unparseable answer, a candidate with an infra_error trial, and
# one whose trials are not finished.


def statuses(score: int, length: int = 2) -> dict[int, str]:
    steps = {i: "success" for i in range(1, score + 1)}
    if score < length:
        steps[score + 1] = "fail_new"
    return steps


def cand(cid, s1, s2, samples=(0,), passed=True, override=None, causes=None) -> CandidateRecord:
    trials = {}
    for seq, reps in (("s1", s1), ("s2", s2)):
        for rep, score in enumerate(reps):
            trials[(seq, rep)] = statuses(score)
    trials.update(override or {})
    keys = tuple(f"call-{cid}-{i}" for i in samples)
    return CandidateRecord(cid, tuple(samples), passed, trials, keys, causes or {})


def scenario(b_id="b", c_id="c") -> TaskRecord:
    return TaskRecord(
        task_id="t",
        prompt="WRITER PROMPT",
        sequence_ids=("s1", "s2"),
        sequence_length=2,
        parse_failures=("truncated/max_tokens",),
        candidates=(
            cand("a", [2, 2, 2], [2, 1, 2], samples=(0, 3)),  # sample 3 duplicates sample 0
            cand(b_id, [1, 1, 1], [1, 1, 1], samples=(1,)),
            cand(c_id, [2, 2, 2], [0, 0, 0], samples=(2,)),
            cand("e", [2, 2, 2], [2, 2, 2], samples=(4,), passed=False),
            cand(
                "f",
                [2, 2, 2],
                [2, 2, 2],
                samples=(5,),
                override={("s2", 1): {1: "infra_error"}},
                causes={("s2", 1): "backend_error"},
            ),
            # h's trial (s1, rep 1) never ran: incomplete under every ablation.
            cand("h", [2, 2, 2], [2, 2, 2], samples=(6,), override={("s1", 1): {}}),
        ),
    )


def programs(cid):
    return {"records.py": f"# program {cid}\n".encode()}


def build(task=None, **cfg):
    values = dict(rule="weak_dominance", pairing_mode="best_vs_worst")
    values.update(cfg)
    return Scorer(ScorerConfig(**values), editor_reps=3).build([task or scenario()], programs)


def test_samples_get_exactly_one_fate():
    report = build().report
    assert report["samples"] == {
        "eligible": 3,  # a, b, c
        "duplicate": 1,  # sample 3 (same program as sample 0)
        "initially_failing": 2,  # e, plus the unparseable sample
        "infra_error": 1,  # f
        "incomplete": 1,  # h
    }
    assert sum(report["samples"].values()) == 8  # every sample accounted for
    assert report["samples_detail"] == {
        "initially_failing": {"failed_initial_tests": 1, "truncated/max_tokens": 1},
        "infra_error": {"backend_error": 1},
    }
    assert report["tasks"]["t"]["excluded_detail"] == report["samples_detail"]


def test_step_endings_count_every_scored_step():
    # Eligible a, b, c over 18 trials: successes a 6+5, b 6, c 6 = 23; first
    # failures a 1, b 6, c 3 = 10.
    assert build().report["step_endings"] == {"fail_new": 10, "success": 23}


def test_budget_exhausted_steps_are_split_by_reason():
    # One prompt_too_large step on a, the rest succeed.
    a = cand("a", [2, 2, 2], [2, 2, 2])
    trials = {**a.trials, ("s1", 0): {1: "success", 2: "budget_exhausted"}}
    reasons = {("s1", 0): {1: "done", 2: "prompt_too_large"}}
    a = CandidateRecord("a", (0,), True, trials, ("k",), {}, reasons)
    b = cand("b", [1, 1, 1], [1, 1, 1], samples=(1,))
    task = TaskRecord("t", "p", ("s1", "s2"), 2, (), (a, b))
    endings = build(task).report["step_endings"]
    assert endings["budget_exhausted/prompt_too_large"] == 1
    assert build(task).report["tasks"]["t"]["step_endings"] == endings


def test_all_pairs_under_each_rule():
    combos = build().report["combinations"]
    assert combos["strict/all_pairs"] == {
        "pair_yield": 1,  # a > b
        "compared": 3,
        "tie": 1,  # a vs c
        "inconsistent": 1,  # b vs c
        "over_cap": 0,
        "tie_rate": 1 / 3,
        "inconsistent_rate": 1 / 3,
    }
    assert combos["weak_dominance/all_pairs"]["pair_yield"] == 2  # a > b, a > c
    assert combos["weak_dominance/all_pairs"]["tie"] == 0
    assert combos["weak_dominance/all_pairs"]["inconsistent"] == 1


def test_best_vs_worst_breaks_aggregate_ties_by_lowest_candidate_id():
    # b and c tie for worst (aggregate 1). With b's id lower, a is compared
    # with b (a decisive win); with c's id lower, a is compared with c,
    # which strict calls a tie.
    combos = build(scenario(b_id="b", c_id="c")).report["combinations"]
    assert combos["strict/best_vs_worst"]["pair_yield"] == 1
    swapped = build(scenario(b_id="z", c_id="c")).report["combinations"]
    assert swapped["strict/best_vs_worst"]["pair_yield"] == 0
    assert swapped["strict/best_vs_worst"]["tie"] == 1
    assert swapped["weak_dominance/best_vs_worst"]["pair_yield"] == 1


def test_primary_pairs_carry_programs_scores_and_strict_flag():
    pairs = build(rule="weak_dominance", pairing_mode="all_pairs").pairs
    first = pairs[0]
    assert first["prompt"] == "WRITER PROMPT"
    # Both samples behind program a (sample 3 duplicated sample 0).
    assert first["chosen_call_keys"] == ["call-a-0", "call-a-3"]
    assert first["rejected_call_keys"] == ["call-b-1"]
    assert parse_program(first["chosen"], ["records.py"]).files == programs(first["chosen_id"])
    assert first["chosen_scores"] == [[2, 2, 2], [2, 1, 2]]


def test_pairs_are_ordered_by_margin_then_ids():
    # a-b margin: |2-1| + |5/3-1| = 5/3; a-c margin: 0 + 5/3 = 5/3. Equal
    # margins fall back to ids: (a, b) before (a, c).
    pairs = build(rule="weak_dominance", pairing_mode="all_pairs").pairs
    assert [(p["chosen_id"], p["rejected_id"], p["margin"]) for p in pairs] == [
        ("a", "b", "5/3"),
        ("a", "c", "5/3"),
    ]
    assert [p["strict_subset"] for p in pairs] == [True, False]


def test_per_task_cap_keeps_the_first_pairs_and_counts_the_rest():
    result = build(rule="weak_dominance", pairing_mode="all_pairs", per_task_cap=1)
    assert [(p["chosen_id"], p["rejected_id"]) for p in result.pairs] == [("a", "b")]
    assert result.report["combinations"]["weak_dominance/all_pairs"]["over_cap"] == 1


def test_one_change_ablation_truncates_scores():
    # With max_changes=1: a (1,1), b (1,1), c (1,0). a and b now tie; a
    # beats c only in s2; b beats c only in s2.
    combos = build(max_changes=1).report["combinations"]
    assert combos["strict/all_pairs"]["pair_yield"] == 0
    assert combos["weak_dominance/all_pairs"]["pair_yield"] == 2  # a > c, b > c
    assert combos["weak_dominance/all_pairs"]["tie"] == 1  # a vs b


def test_one_rep_ablation_uses_only_the_listed_reps():
    # Rep 1 only: a s2 = 1 (its weak rep), so a (2,1) vs b (1,1) is a tie
    # under strict.
    combos = build(reps=(1,)).report["combinations"]
    assert combos["strict/all_pairs"]["pair_yield"] == 0
    assert combos["weak_dominance/all_pairs"]["pair_yield"] == 2


def test_rep_agreement_and_histograms():
    report = build().report
    # Agreement per (candidate, sequence): a s2 has 2 of 3 reps equal.
    assert report["rep_agreement"] == pytest.approx((1 + 2 / 3 + 1 + 1 + 1 + 1) / 6)
    assert report["tasks"]["t"]["score_histogram"] == {
        "s1": [0, 3, 6],  # b's three 1s; a's and c's six 2s
        "s2": [3, 4, 2],  # c's 0s; b's 1s and a's 1; a's two 2s
    }


def test_results_do_not_depend_on_input_order():
    task = scenario()
    shuffled = list(task.candidates)
    random.Random(7).shuffle(shuffled)
    reordered = TaskRecord(**{**task.__dict__, "candidates": tuple(shuffled)})
    for mode in ("all_pairs", "best_vs_worst"):
        assert build(task, pairing_mode=mode).pairs == build(reordered, pairing_mode=mode).pairs
    assert build(task).report == build(reordered).report


def test_single_eligible_candidate_gives_no_pairs():
    task = TaskRecord("t", "p", ("s1", "s2"), 2, (), (cand("a", [2, 2, 2], [2, 2, 2]),))
    result = build(task)
    assert result.pairs == []
    assert result.report["combinations"]["weak_dominance/best_vs_worst"]["compared"] == 0
    assert result.report["combinations"]["weak_dominance/best_vs_worst"]["tie_rate"] is None


def test_unknown_rule_or_bad_reps_are_config_errors():
    with pytest.raises(ConfigError, match="unknown rule 'pooled'"):
        Scorer(ScorerConfig(rule="pooled", pairing_mode="all_pairs"), editor_reps=3)
    with pytest.raises(ConfigError, match="rep indices below 3"):
        Scorer(ScorerConfig(rule="strict", pairing_mode="all_pairs", reps=(3,)), editor_reps=3)


def test_write_outputs(tmp_path):
    result = build()
    write_outputs(result, tmp_path / "run")
    lines = (tmp_path / "run" / "preferences.jsonl").read_text().splitlines()
    assert [json.loads(line)["chosen_id"] for line in lines] == [
        p["chosen_id"] for p in result.pairs
    ]
    report = json.loads((tmp_path / "run" / "preferences_report.json").read_text())
    assert report["samples"]["eligible"] == 3


# --- loading from the store -------------------------------------------------


def test_load_task_record_from_the_store(tmp_path):
    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    prompt, pv = "PROMPT", None
    from pipeline.registry import prompt_version

    pv = prompt_version(prompt)
    with Store(tmp_path / "runs") as store:
        run = store.start_run(cfg)
        good = store.put_blob({"records.py": b"good\n"})
        bad = store.put_blob({"records.py": b"bad\n"})
        for idx, cid in enumerate([good, good, None, bad]):
            store.record_candidate(
                Candidate(
                    CandidateKey(task.id, pv, "wh", idx),
                    cid,
                    None if cid else "malformed/no_code: x",
                    1,
                    1,
                    0.1,
                    run,
                    call_key=f"k{idx}",
                )
            )
        store.record_initial_check(
            InitialCheck(task.id, task.task_version, good, "sb", True, {}, run)
        )
        store.record_initial_check(
            InitialCheck(task.id, task.task_version, bad, "sb", False, {}, run)
        )
        for seq in ("s1", "s2"):
            for rep in range(3):
                key = TrialKey(task.id, task.task_version, good, seq, rep, "eh")
                store.record_checkpoint(Checkpoint(key, 1, "c", "success", "x", run_id=run))
                store.record_checkpoint(Checkpoint(key, 2, "c", "fail_new", "y", run_id=run))

        record = load_task_record(
            store,
            task,
            prompt,
            writer_hash="wh",
            sandbox_hash="sb",
            editor_hash="eh",
            editor_reps=3,
        )

    assert record.parse_failures == ("malformed/no_code",)
    assert record.sequence_ids == ("s1", "s2") and record.sequence_length == 2
    by_id = {c.candidate_id: c for c in record.candidates}
    assert by_id[good].sample_indices == (0, 1)
    assert by_id[good].call_keys == ("k0", "k1")
    assert by_id[good].initially_passed is True
    assert by_id[good].trials[("s2", 2)] == {1: "success", 2: "fail_new"}
    assert by_id[bad].initially_passed is False and by_id[bad].trials == {}

    report = (
        Scorer(ScorerConfig(rule="strict", pairing_mode="all_pairs"), 3)
        .build([record], programs)
        .report
    )
    assert report["samples"] == {
        "eligible": 1,
        "initially_failing": 2,
        "duplicate": 1,
        "infra_error": 0,
        "incomplete": 0,
    }
    assert report["samples_detail"] == {
        "initially_failing": {"failed_initial_tests": 1, "malformed/no_code": 1}
    }
    assert report["tasks"]["record_store"]["score_histogram"] == {"s1": [0, 3, 0], "s2": [0, 3, 0]}


def test_infra_cause_is_loaded_from_the_store(tmp_path):
    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    from pipeline.registry import prompt_version

    with Store(tmp_path / "runs") as store:
        run = store.start_run(cfg)
        cid = store.put_blob({"records.py": b"x\n"})
        key = CandidateKey(task.id, prompt_version("P"), "wh", 0)
        store.record_candidate(Candidate(key, cid, None, 1, 1, 0.1, run))
        store.record_initial_check(
            InitialCheck(task.id, task.task_version, cid, "sb", True, {}, run)
        )
        trial = TrialKey(task.id, task.task_version, cid, "s1", 0, "eh")
        store.record_checkpoint(
            Checkpoint(trial, 1, "c", "infra_error", None, run_id=run, infra_cause="docker_create")
        )
        record = load_task_record(
            store, task, "P", writer_hash="wh", sandbox_hash="sb", editor_hash="eh", editor_reps=3
        )
    report = (
        Scorer(ScorerConfig(rule="strict", pairing_mode="all_pairs"), 3)
        .build([record], programs)
        .report
    )
    assert report["samples_detail"] == {"infra_error": {"docker_create": 1}}
