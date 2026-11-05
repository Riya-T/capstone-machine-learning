# Base writer on the eval tasks

The original writer (Qwen2.5-Coder-7B, no training, prompt
`prompts/writer_v1.md`) on the 16 eval tasks, with the frozen editor
(Qwen2.5-Coder-14B) and budget. This is the "before" side of every
comparison: each other method gets the same run on the same tasks.

- Config: `configs/rtx5070_eval.yaml` (RTX 5070, both models 4-bit in
  Ollama with an 8192-token context).
- Programs: the writer's passing programs, at most 8 per task in sample
  order (`max_programs`). seat_reservation has only 3, race_telemetry and
  task_board 5.
- Trials: each program, each of the task's 2 change sequences, 3
  repetitions; each sequence has 3 changes.
- Runs: 20261104T234904Z-4d6e4b and 20261105T142912Z-48e0e2 (the same run,
  paused and resumed), plus a few trials from 20261104T222233Z-25884b and
  20261104T232530Z-4b23ad; finished 2026-11-05. No infrastructure errors.
- Cost: 3,062 editor calls, 5.4M prompt tokens, 3.1M reply tokens, 19.3
  hours of editing.
- meeting_rooms was scored after the Usage headers were added to its hidden
  files (6edc355), so its results match the current task files.

## Results

"Changes done before first failure" is the main number: how far the editor
got through the 3 changes before one failed (a change fails if any hidden
test of the new feature or of earlier behavior fails, or the editor runs out
of budget). Every task counts the same in the average.

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| aging_inventory | 7 | 42 | 0.55 of 3 | 38% | 0% |
| auction_house | 6 | 36 | 1.22 of 3 | 58% | 31% |
| document_versions | 8 | 48 | 1.73 of 3 | 85% | 12% |
| elevator_dispatch | 8 | 48 | 0.48 of 3 | 25% | 2% |
| light_grid | 8 | 48 | 1.98 of 3 | 79% | 50% |
| locker_room | 8 | 48 | 2.21 of 3 | 85% | 62% |
| meeting_rooms | 8 | 48 | 1.08 of 3 | 62% | 17% |
| race_telemetry | 5 | 30 | 0.90 of 3 | 53% | 7% |
| rover_fleet | 6 | 36 | 0.19 of 3 | 19% | 0% |
| scoreboard | 8 | 48 | 2.02 of 3 | 94% | 31% |
| seat_reservation | 3 | 18 | 1.00 of 3 | 39% | 28% |
| social_feed | 6 | 36 | 1.81 of 3 | 78% | 39% |
| spending_alerts | 8 | 48 | 0.35 of 3 | 35% | 0% |
| subscription_billing | 8 | 48 | 0.40 of 3 | 40% | 0% |
| task_board | 5 | 30 | 1.10 of 3 | 50% | 10% |
| time_clock | 8 | 48 | 1.69 of 3 | 81% | 29% |
| **Average over 16 tasks** | 110 | 660 | 1.17 | 58% | 20% |

Step endings: success 790, fail_new 297, budget_exhausted 212,
fail_existing 10, fail_both 8. Breaking earlier behavior is rare; most
failures are the new feature itself or running out of turns.

## Being checked

A few changes almost never succeed, for example spending_alerts
`c_month_compare` (0 of 24), rover_fleet `c_versioned_commands` (0 of 18),
document_versions `c_restore` (out of budget 19 of 19) and the first change
of subscription_billing `s1` (0 of 24). Each is being checked for hidden
tests that test something the change request doesn't say. A change that is
fixed is scored again, and this page updated; a change that is only hard is
kept.

## Reproduce

From `harness/`, inside WSL:

```bash
uv run python -m harness collect --config configs/rtx5070_eval.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_eval.yaml
```

Results already in the store are reused, so the first command only runs
what is missing.
