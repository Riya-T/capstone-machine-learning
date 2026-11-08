# Maintainability prompt on the eval tasks

The prompt-only baseline: the same writer (Qwen2.5-Coder-7B, no training)
with `prompts/writer_maintainable_v1.md`, which is `writer_v1.md` plus a
request for clean, maintainable code that will be changed later. Same 16 eval
tasks (as of 9ff8854), editor, budget and selection as the base writer
(`harness/results/base_writer_eval.md`): passing programs, at most 8 per task
in sample order, 2 sequences × 3 repetitions each.

- Config: `configs/rtx5070_eval_maintain.yaml`.
- Runs: writer samples 20261105T184639Z-e29d38 (2026-11-05), editor trials
  20261105T195056Z-3bfb66 (light_grid), 20261105T210023Z-977504
  (time_clock) and 20261107T075721Z-f1f83e (the rest), finished
  2026-11-07. No infrastructure errors. A program the base writer also
  wrote gets the same trials (results are keyed by the program), which
  happened for 219 of the 1,403 editing steps.
- Cost: 4,052 editor calls, 7.5M prompt tokens, 4.3M reply tokens (base
  writer: 4,124, 7.5M and 4.2M).

## Results

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| aging_inventory | 8 | 48 | 0.60 of 3 | 40% | 0% |
| auction_house | 6 | 36 | 2.00 of 3 | 75% | 58% |
| document_versions | 8 | 48 | 1.73 of 3 | 88% | 12% |
| elevator_dispatch | 8 | 48 | 0.83 of 3 | 48% | 2% |
| light_grid | 8 | 48 | 1.94 of 3 | 79% | 48% |
| locker_room | 8 | 48 | 2.40 of 3 | 90% | 71% |
| meeting_rooms | 6 | 36 | 1.08 of 3 | 69% | 14% |
| race_telemetry | 5 | 30 | 1.63 of 3 | 73% | 40% |
| rover_fleet | 5 | 30 | 0.83 of 3 | 40% | 17% |
| scoreboard | 8 | 48 | 1.88 of 3 | 83% | 33% |
| seat_reservation | 3 | 18 | 1.22 of 3 | 72% | 17% |
| social_feed | 6 | 36 | 2.03 of 3 | 86% | 42% |
| spending_alerts | 8 | 48 | 0.77 of 3 | 60% | 0% |
| subscription_billing | 8 | 48 | 0.33 of 3 | 33% | 0% |
| task_board | 5 | 30 | 2.17 of 3 | 97% | 40% |
| time_clock | 8 | 48 | 1.38 of 3 | 81% | 12% |
| **Average over 16 tasks** | 108 | 648 | 1.43 | 70% | 25% |

Step endings: success 914, budget_exhausted 324, fail_new 149, fail_both 10,
fail_existing 6.

## Compared with the base writer

Paired task bootstrap (20,000 resamples of the 16 tasks, each task's pair
kept together, seed 20261105), maintainability prompt minus base writer:

| Metric | Base | Maintainability prompt | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.43 | +0.00 | −0.10 to +0.10 |
| First change works | 67% | 70% | +3 pts | −1 to +8 pts |
| Whole sequence works | 26% | 25% | −1 pt | −5 to +4 pts |
| Writer samples passing the initial checks | 58% | 60% | +2 pts | −3 to +8 pts |

Asking for maintainable code changes nothing measurable: every interval
includes 0, and the main measure is the same to two decimals. Per task the
differences go both ways (race_telemetry 1.20 → 1.63, time_clock 1.69 →
1.38). The prompt did raise the number of correct programs on a few tasks
(aging_inventory 9 → 13 of 16 samples, spending_alerts 8 → 12) and lowered
it on others (meeting_rooms 9 → 6).

## Reproduce

From `harness/`, inside WSL:

```bash
uv run python -m harness collect --config configs/rtx5070_eval_maintain.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_eval_maintain.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_eval.yaml \
    --other configs/rtx5070_eval_maintain.yaml --bootstrap 20000
```
