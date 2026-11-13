# Comment ablation on the eval tasks

The proposal's "comments removed" variation: does any writer's result
depend on comments that hint to the editor? Each of the five writers' eval
runs is repeated with the editor seeing every program without its comments
and docstrings (`editor.view_transform: strip_comments`,
`collection/view.py`). Stripping happens before the first step of each
change sequence, and the editor then edits the stripped program for the
whole sequence, so comments it writes itself stay. Every stripped file is
checked to parse to the same syntax tree as the original without its
docstrings, so the program does the same thing. Everything else is the
same as in the five normal runs: the same writer samples and initial
checks (reused, not rerun), the same 16 eval tasks (as of 9ff8854), editor,
budget and selection (passing programs, at most 8 per task in sample order,
2 sequences × 3 repetitions each, 3 changes per sequence).

- Configs: `configs/rtx5070_eval_nocomments.yaml` and one per writer
  (`_maintain`, `_dpo3`, `_radon`, `_sft`), each its normal config plus the
  view setting.
- Runs at 5facee6, one after the other, 2026-11-12 03:47 to 2026-11-13
  07:16 PST (27.5 hours):

  | Writer | Run | Hours | New editor calls |
  |---|---|---:|---:|
  | Base | 20261112T114730Z-507332 | 4.8 | 144 |
  | Maintainability prompt | 20261112T163745Z-fa6d0a | 9.3 | 1,167 |
  | dpo3 | 20261113T015448Z-0a7b05 | 4.5 | 193 |
  | Radon | 20261113T062347Z-6d074e | 4.6 | 324 |
  | Correctness-only | 20261113T110210Z-86aefd | 4.2 | 152 |

  One trial of the correctness-only run hit a sandbox error (Docker could
  not start a container). Rerunning its config retried just that trial,
  which then completed (20261113T152211Z-f158b8, under a minute).
- Cost: 1,980 new editor calls, 3.6M prompt tokens and 2.0M reply tokens
  for 6,293 editing steps, about a tenth of the five normal runs' 20,078
  calls.

## Why most trials did not need the editor

A program with nothing to strip gives the editor exactly the prompt it got
in the normal run. The editor's seed depends only on the task, program,
sequence and repetition, not on the editor config, so these trials are
answered from the stored replies; only their tests run again. They must
then match the normal run exactly, and they do: all 2,904 trials of
unchanged programs are identical to the normal run's, step by step (status
and output program). So the ablation can differ from the normal run only on
the programs that had comments, and there it is paired trial by trial, with
the same seeds.

## How much there was to strip

| Writer | Edited programs with comments or docstrings | Share of the programs' bytes removed |
|---|---:|---:|
| Base | 4 of 110 | 0.11% |
| Maintainability prompt | 32 of 108 | 3.67% |
| dpo3 | 5 of 113 | 0.13% |
| Radon | 8 of 94 | 0.29% |
| Correctness-only | 3 of 111 | 0.07% |
| *Train programs (for the pairs)* | *14 of 256* | *0.33%* |

Neither writer prompt mentions comments. With the plain prompt
(`prompts/writer_v1.md`) the writer rarely writes any. Asked for "clean,
maintainable code" (`prompts/writer_maintainable_v1.md`), it comments a
third of its programs. dpo3 and the correctness-only writer comment no
more than the base writer. The Radon writer comments a little more, maybe
because Radon's index gives credit for comment lines (`mi_visit(...,
multi=True)` counts docstrings as comments).

## Results

Each writer, normal → comments removed (paired task bootstrap, 20,000
resamples of the 16 tasks, seed 20261105):

| Writer | Changes done before first failure | Difference | 95% interval | First change works | Whole sequence works |
|---|---:|---:|---:|---:|---:|
| Base | 1.43 → 1.41 | −0.01 | −0.03 to +0.00 | −0 pts (−1 to +0) | −1 pt (−1 to +0) |
| Maintainability prompt | 1.43 → 1.44 | +0.01 | −0.04 to +0.07 | +1 pt (−1 to +3) | −0 pts (−1 to +1) |
| dpo3 | 1.45 → 1.45 | +0.01 | −0.01 to +0.02 | −0 pts (−1 to +0) | +0 pts (−0 to +1) |
| Radon | 1.35 → 1.35 | −0.00 | −0.04 to +0.03 | −0 pts (−1 to +1) | −0 pts (−1 to +0) |
| Correctness-only | 1.47 → 1.48 | +0.00 | +0.00 to +0.01 | +0 pts (+0 to +0) | −0 pts (−0 to +0) |

The pass rate of the initial checks is the same by construction (same
samples). The intervals are narrow because most trials are the normal
ones. For four writers only 1 to 3 tasks change at all.

Only on the programs that had comments, normal → comments removed, trial
by trial (`scripts/ablation_compare.py`; every task weighted the same):

| Writer | Programs | Tasks, trials | Changes done before first failure | Difference | 95% interval |
|---|---:|---:|---:|---:|---:|
| Base | 4 | 3, 24 | 1.58 → 1.22 | −0.36 | – |
| Maintainability prompt | 32 | 12, 192 | 1.28 → 1.32 | +0.04 | −0.17 to +0.26 |
| dpo3 | 5 | 3, 30 | 1.41 → 1.48 | +0.07 | – |
| Radon | 8 | 3, 48 | 1.54 → 1.29 | −0.25 | – |
| Correctness-only | 3 | 1, 18 | 1.06 → 1.17 | +0.11 | – |
| **All five pooled** | 52 | 13, 312 | 1.37 → 1.33 | −0.04 | −0.26 to +0.19 |

Intervals over 1 to 3 tasks say nothing and are left out. 20 of the 52
programs are elevator_dispatch programs.

Per task, maintainability prompt, normal → comments removed (12 tasks have
commented programs, so 4 stay exactly the same):

| Task | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|
| aging_inventory | 0.60 → 0.62 | 40% → 42% | 0% → 0% |
| auction_house | 2.00 → 2.17 | 75% → 86% | 58% → 58% |
| document_versions | 1.73 → 1.73 | 88% → 88% | 12% → 12% |
| elevator_dispatch | 0.83 → 0.71 | 48% → 42% | 2% → 4% |
| light_grid | 1.94 → 1.94 | 79% → 79% | 48% → 48% |
| locker_room | 2.40 → 2.25 | 90% → 85% | 71% → 69% |
| meeting_rooms | 1.08 → 1.44 | 69% → 81% | 14% → 19% |
| race_telemetry | 1.63 → 1.67 | 73% → 73% | 40% → 40% |
| rover_fleet | 0.83 → 0.70 | 40% → 37% | 17% → 13% |
| scoreboard | 1.88 → 1.81 | 83% → 81% | 33% → 35% |
| seat_reservation | 1.22 → 1.22 | 72% → 72% | 17% → 17% |
| social_feed | 2.03 → 2.00 | 86% → 89% | 42% → 36% |
| spending_alerts | 0.77 → 0.85 | 60% → 65% | 0% → 0% |
| subscription_billing | 0.33 → 0.31 | 33% → 31% | 0% → 0% |
| task_board | 2.17 → 2.17 | 97% → 97% | 40% → 40% |
| time_clock | 1.38 → 1.42 | 81% → 81% | 12% → 10% |

## What it means

- **No writer's result depends on comments.** Removing them changes no
  writer's main measure by more than 0.02, and on the 52 programs that had
  any, the editor does about as well without them (−0.04, interval −0.26
  to +0.19). Tasks go both ways.
- **Our writer did not learn to write hint comments.** dpo3 and the
  correctness-only writer comment as rarely as the base writer (5 and 3
  programs against 4). So their small differences from the base writer do
  not come from comments either.
- **The maintainability prompt's comments neither help nor hurt the
  editor.** They are 3.7% of its programs' bytes, and stripping them
  leaves its results unchanged (+0.01, −0.04 to +0.07; on its 32
  commented programs +0.04, −0.17 to +0.26).
- **Comments cannot have driven our training pairs much.** Only 14 of the
  256 train programs have comments, and pairs whose two programs differ
  only in docstrings, strings, local names or annotations were already
  filtered out (`scripts/filter_pairs.py`).

Limits: comments are rare, so the ablation tests only a small part of the
programs (52 of 536). There is one seed per trained writer, and only large
effects on the commented programs could be seen.

## Reproduce

From `harness/`, inside WSL, with the five writers served as in their own
pages:

```bash
for w in "" _maintain _dpo3 _radon _sft; do
  uv run python -m harness collect --config configs/rtx5070_eval${w}_nocomments.yaml
  uv run python scripts/eval_compare.py --base configs/rtx5070_eval$w.yaml \
      --other configs/rtx5070_eval${w}_nocomments.yaml --bootstrap 20000
done
uv run python scripts/ablation_compare.py \
    configs/rtx5070_eval.yaml configs/rtx5070_eval_nocomments.yaml \
    configs/rtx5070_eval_maintain.yaml configs/rtx5070_eval_maintain_nocomments.yaml \
    configs/rtx5070_eval_dpo3.yaml configs/rtx5070_eval_dpo3_nocomments.yaml \
    configs/rtx5070_eval_radon.yaml configs/rtx5070_eval_radon_nocomments.yaml \
    configs/rtx5070_eval_sft.yaml configs/rtx5070_eval_sft_nocomments.yaml
```

The collect commands answer the trials of unchanged programs from the
normal runs' stored replies, so they need the normal runs in the same
store to stay cheap. The train-program row of
the strip table applies the same `strip_comments` to the 256 programs
edited by `configs/rtx5070_train.yaml`.
