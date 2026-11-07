# Base writer on the eval tasks

The original writer (Qwen2.5-Coder-7B, no training, prompt
`prompts/writer_v1.md`) on the 16 eval tasks, with the frozen editor
(Qwen2.5-Coder-14B) and budget. This is the "before" side of every
comparison: each other method gets the same run on the same tasks.

- Config: `configs/rtx5070_eval.yaml` (RTX 5070, both models 4-bit in
  Ollama with an 8192-token context).
- Programs: the writer's passing programs, at most 8 per task in sample
  order (`max_programs`). seat_reservation has only 3, race_telemetry and
  task_board 5. (`harness/docs/evaluation.md` describes a different
  protocol, one unselected first attempt per task and seed; these numbers
  are not from it.)
- Trials: each program, each of the task's 2 change sequences, 3
  repetitions; each sequence has 3 changes.
- Task files: as of 9ff8854. 13 tasks were fixed after the first run (see
  "Fixes after the first run" below) and scored again; document_versions,
  light_grid and time_clock are unchanged.
- Runs: 20261104T234904Z-4d6e4b (the 3 unchanged tasks), then
  20261105T232035Z-4d80c0, 20261106T014425Z-7166e3 and
  20261106T181812Z-4d448f (the 13 fixed tasks; one run, paused twice and
  resumed), finished 2026-11-06. No infrastructure errors.
- Cost: 4,124 editor calls, 7.5M prompt tokens, 4.2M reply tokens, 19.6
  hours of editing.

## Results

"Changes done before first failure" is the main number: how far the editor
got through the 3 changes before one failed (a change fails if any hidden
test of the new feature or of earlier behavior fails, or the editor runs out
of budget). Every task counts the same in the average.

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| aging_inventory | 7 | 42 | 0.55 of 3 | 38% | 0% |
| auction_house | 6 | 36 | 2.31 of 3 | 83% | 64% |
| document_versions | 8 | 48 | 1.73 of 3 | 85% | 12% |
| elevator_dispatch | 8 | 48 | 0.79 of 3 | 44% | 2% |
| light_grid | 8 | 48 | 1.98 of 3 | 79% | 50% |
| locker_room | 8 | 48 | 2.25 of 3 | 85% | 67% |
| meeting_rooms | 8 | 48 | 1.31 of 3 | 71% | 23% |
| race_telemetry | 5 | 30 | 1.20 of 3 | 67% | 13% |
| rover_fleet | 6 | 36 | 0.78 of 3 | 33% | 19% |
| scoreboard | 8 | 48 | 2.08 of 3 | 94% | 38% |
| seat_reservation | 3 | 18 | 1.00 of 3 | 39% | 28% |
| social_feed | 6 | 36 | 1.78 of 3 | 78% | 36% |
| spending_alerts | 8 | 48 | 0.83 of 3 | 58% | 0% |
| subscription_billing | 8 | 48 | 0.46 of 3 | 42% | 2% |
| task_board | 5 | 30 | 2.07 of 3 | 87% | 37% |
| time_clock | 8 | 48 | 1.69 of 3 | 81% | 29% |
| **Average over 16 tasks** | 110 | 660 | 1.43 | 67% | 26% |

Step endings: success 944, budget_exhausted 331, fail_new 142,
fail_existing 12, fail_both 5. Breaking earlier behavior is rare. Most
failures are now the editor running out of turns, often while a public
check it can see still fails.

Task bootstrap (20,000 resamples of the 16 tasks with replacement, seed
20261105, from the exact per-task values), percentile 95% intervals:

| Metric | Estimate | 95% interval |
|---|---:|---:|
| Changes done before first failure (of 3) | 1.43 | 1.12–1.72 |
| First change works | 67% | 56%–76% |
| Whole sequence works | 26% | 16%–37% |

Each eval task is its own family, so these measure variation across tasks,
not across programs or repetitions. A method comparison should resample the
same tasks for both methods and report the interval of the paired per-task
difference.

## Fixes after the first run

The first run (2026-11-05, runs 20261104T234904Z-4d6e4b and
20261105T142912Z-48e0e2) gave 1.17 changes, 58% and 20% on the earlier task
files. Rerunning the checks on every failed step showed tests that were the
task's fault in 13 tasks: rules the request states but no public check
covered, which almost every failed edit missed; requests that said a rule
unclearly; and one test bug. `harness/tasks/FAMILIES.md` ("Eval change
tests after the base run (2026-11-05)") lists each fix. The writer-visible
files were not changed, so the same programs were scored again. The changes
that are only hard were kept; for example document_versions `c_restore`
still never succeeds, because no program keeps who wrote each revision.

Biggest changes per task (changes done before first failure): rover_fleet
0.19 → 0.78, spending_alerts 0.35 → 0.83, auction_house 1.22 → 2.31 and
task_board 1.10 → 2.07.

## Reproduce

From `harness/`, inside WSL:

```bash
uv run python -m harness collect --config configs/rtx5070_eval.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_eval.yaml --bootstrap 20000
```

Results already in the store are reused, so the first command only runs
what is missing.
