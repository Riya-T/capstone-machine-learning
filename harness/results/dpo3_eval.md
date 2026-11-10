# DPO writer (dpo3) on the eval tasks

The DPO writer chosen on the dev tasks (`harness/results/dpo3_dev.md`):
Qwen2.5-Coder-7B with a QLoRA adapter trained on 160 filtered preference
pairs from 28 train tasks, learning rate 2e-5, beta 0.1, 2 epochs. Same 16
eval tasks (as of 9ff8854), prompt (`prompts/writer_v1.md`), editor, budget
and selection as the base writer (`harness/results/base_writer_eval.md`):
passing programs, at most 8 per task in sample order, 2 sequences × 3
repetitions each, 3 changes per sequence. Settings were chosen on the dev
tasks only; these tasks were not used for training or for choosing.

- Config: `configs/rtx5070_eval_dpo3.yaml`.
- Runs: 20261109T122319Z-05d0fe at 5b81863, stopped during social_feed when
  Windows Update restarted WSL, and 20261110T051632Z-30453c at b0620d3
  (which only adds a results page), which resumed it. Finished 2026-11-10.
  No infrastructure errors; all 256 writer samples parsed.
- Cost: 3,847 editor calls, 6.9M prompt tokens, 3.8M reply tokens (base
  writer: 4,124, 7.5M and 4.2M). 15 dpo3 programs are identical to programs
  the base writer wrote (light_grid 6, locker_room 4, aging_inventory 2,
  document_versions 2, scoreboard 1) and reuse its trials (172 of the
  1,473 editing steps).

## Results

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| aging_inventory | 8 | 48 | 0.60 of 3 | 40% | 0% |
| auction_house | 8 | 48 | 2.33 of 3 | 85% | 67% |
| document_versions | 8 | 48 | 1.75 of 3 | 88% | 12% |
| elevator_dispatch | 8 | 48 | 0.67 of 3 | 46% | 2% |
| light_grid | 8 | 48 | 2.35 of 3 | 92% | 62% |
| locker_room | 8 | 48 | 2.38 of 3 | 92% | 71% |
| meeting_rooms | 8 | 48 | 0.92 of 3 | 67% | 6% |
| race_telemetry | 5 | 30 | 2.23 of 3 | 93% | 47% |
| rover_fleet | 8 | 48 | 0.75 of 3 | 40% | 8% |
| scoreboard | 8 | 48 | 2.04 of 3 | 90% | 42% |
| seat_reservation | 2 | 12 | 1.00 of 3 | 58% | 17% |
| social_feed | 6 | 36 | 1.69 of 3 | 78% | 33% |
| spending_alerts | 8 | 48 | 0.62 of 3 | 52% | 0% |
| subscription_billing | 8 | 48 | 0.35 of 3 | 35% | 0% |
| task_board | 4 | 24 | 2.04 of 3 | 96% | 25% |
| time_clock | 8 | 48 | 1.42 of 3 | 83% | 15% |
| **Average over 16 tasks** | 113 | 678 | 1.45 | 71% | 25% |

Step endings: success 966, budget_exhausted 337, fail_new 153,
fail_existing 9, fail_both 8.

## Compared with the base writer

Per task, base writer → dpo3:

| Task | Initial pass | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| aging_inventory | 9/16 → 14/16 | 0.55 → 0.60 | 38% → 40% | 0% → 0% |
| auction_house | 6/16 → 8/16 | 2.31 → 2.33 | 83% → 85% | 64% → 67% |
| document_versions | 16/16 → 16/16 | 1.73 → 1.75 | 85% → 88% | 12% → 12% |
| elevator_dispatch | 9/16 → 12/16 | 0.79 → 0.67 | 44% → 46% | 2% → 2% |
| light_grid | 14/16 → 14/16 | 1.98 → 2.35 | 79% → 92% | 50% → 62% |
| locker_room | 8/16 → 11/16 | 2.25 → 2.38 | 85% → 92% | 67% → 71% |
| meeting_rooms | 9/16 → 11/16 | 1.31 → 0.92 | 71% → 67% | 23% → 6% |
| race_telemetry | 5/16 → 5/16 | 1.20 → 2.23 | 67% → 93% | 13% → 47% |
| rover_fleet | 6/16 → 8/16 | 0.78 → 0.75 | 33% → 40% | 19% → 8% |
| scoreboard | 16/16 → 16/16 | 2.08 → 2.04 | 94% → 90% | 38% → 42% |
| seat_reservation | 3/16 → 2/16 | 1.00 → 1.00 | 39% → 58% | 28% → 17% |
| social_feed | 6/16 → 6/16 | 1.78 → 1.69 | 78% → 78% | 36% → 33% |
| spending_alerts | 8/16 → 10/16 | 0.83 → 0.62 | 58% → 52% | 0% → 0% |
| subscription_billing | 13/16 → 13/16 | 0.46 → 0.35 | 42% → 35% | 2% → 0% |
| task_board | 5/16 → 4/16 | 2.07 → 2.04 | 87% → 96% | 37% → 25% |
| time_clock | 15/16 → 14/16 | 1.69 → 1.42 | 81% → 83% | 29% → 15% |

Paired task bootstrap (20,000 resamples of the 16 tasks, each task's pair
kept together, seed 20261105), dpo3 minus base writer:

| Metric | Base | dpo3 | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.45 | +0.02 | −0.11 to +0.19 |
| First change works | 67% | 71% | +4 pts | +0 to +9 pts |
| Whole sequence works | 26% | 25% | −1 pt | −6 to +5 pts |
| Writer samples passing the initial checks | 58% | 64% | +6 pts | +2 to +12 pts |

On the main measure dpo3 is no better than the base writer: +0.02, with an
interval from −0.11 to +0.19. The per-task changes go both ways (6 tasks
up, 9 down, 1 the same), and the small gain rests on race_telemetry
(1.20 → 2.23 on 5 programs). Without that task, the mean difference is
about −0.05. The first change works a little more often (+4 pts, interval
starting at 0), and the whole sequence works as often as before.

The one clear difference is not what the pairs trained for: dpo3's samples
pass the initial checks more often (164 of 256 against 148; +6 pts,
+2 to +12). Its programs are as varied as the base writer's (252 distinct
programs of 256 for both), and its replies are slightly shorter (548
tokens on average against 564).

All three writers measured so far, on the same 16 eval tasks:

| Metric | Base | Maintainability prompt | dpo3 |
|---|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.43 | 1.45 |
| First change works | 67% | 70% | 71% |
| Whole sequence works | 26% | 25% | 25% |
| Writer samples passing the initial checks | 58% | 60% | 64% |

Neither asking for maintainable code
(`harness/results/maintainability_prompt_eval.md`) nor DPO on 160
editing-outcome pairs makes the writer's programs measurably easier for
the editor to change.

## Reproduce

From `harness/`, inside WSL, after building `writer-dpo3-ctx8k` as in
`harness/results/dpo3_dev.md`:

```bash
uv run python -m harness collect --config configs/rtx5070_eval_dpo3.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_eval_dpo3.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_eval.yaml \
    --other configs/rtx5070_eval_dpo3.yaml --bootstrap 20000
```
