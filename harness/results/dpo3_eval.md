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
- Cost: 4,221 editor calls, 7.5M prompt tokens, 4.2M reply tokens over
  all 1,473 editing steps (base writer: 4,124, 7.5M and 4.2M over 1,434).
  15 dpo3 programs are identical to programs
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

## Second training seed

`dpo3_s2` is dpo3 trained again with `--seed 2`, on the same 160 pairs
with the same settings (`configs/rtx5070_eval_dpo3_s2.yaml`, run
20261121T013018Z-7db506, 638 editing steps, no infrastructure errors; the
collection was paused once and resumed from the store). Its training ends
with reward accuracy 0.88 and a reward margin of 0.21.

| Metric | Base | dpo3 (seed 42) | dpo3 (seed 2) | Seed 2 − base (95%) |
|---|---:|---:|---:|---|
| Changes done before first failure | 1.43 | 1.45 | 1.48 | +0.06 (−0.03 to +0.14) |
| First change works | 67% | 71% | 73% | +6 pts (+2 to +11) |
| Whole sequence works | 26% | 25% | 26% | −0 pts (−4 to +3) |
| Writer samples passing the initial checks | 58% | 64% | 62% | +4 pts (−0 to +10) |

The second seed repeats the first: no measurable gain on the planned
measure (seed 42: +0.02, −0.11 to +0.19), and a few points more on the
first change and on initial correctness. Those two are secondary metrics,
and the first change's gain is too small to move the planned measure.

## Third training seed

`dpo3_s3` is dpo3 trained again with `--seed 3`, on the same pairs with the
same settings (`configs/rtx5070_eval_dpo3_s3.yaml`; the collection was
paused three times for other runs and resumed from the store, last run
20261125T160728Z-0b5ac2, finished 2026-11-25, 649 editing steps, no
infrastructure errors). Its training ends with reward accuracy 1.00 and a
reward margin of 0.32.

Per task, base writer → dpo3 seed 3:

| Task | Initial pass | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| aging_inventory | 9/16 → 12/16 | 0.55 → 0.46 | 38% → 31% | 0% → 0% |
| auction_house | 6/16 → 9/16 | 2.31 → 2.04 | 83% → 79% | 64% → 54% |
| document_versions | 16/16 → 16/16 | 1.73 → 1.69 | 85% → 81% | 12% → 12% |
| elevator_dispatch | 9/16 → 11/16 | 0.79 → 1.00 | 44% → 56% | 2% → 4% |
| light_grid | 14/16 → 15/16 | 1.98 → 1.75 | 79% → 75% | 50% → 46% |
| locker_room | 8/16 → 8/16 | 2.25 → 2.40 | 85% → 86% | 67% → 74% |
| meeting_rooms | 9/16 → 5/16 | 1.31 → 1.20 | 71% → 70% | 23% → 20% |
| race_telemetry | 5/16 → 13/16 | 1.20 → 1.83 | 67% → 85% | 13% → 35% |
| rover_fleet | 6/16 → 6/16 | 0.78 → 0.75 | 33% → 42% | 19% → 11% |
| scoreboard | 16/16 → 16/16 | 2.08 → 1.81 | 94% → 90% | 38% → 29% |
| seat_reservation | 3/16 → 5/16 | 1.00 → 1.40 | 39% → 67% | 28% → 33% |
| social_feed | 6/16 → 4/16 | 1.78 → 1.88 | 78% → 83% | 36% → 38% |
| spending_alerts | 8/16 → 11/16 | 0.83 → 0.81 | 58% → 60% | 0% → 2% |
| subscription_billing | 13/16 → 11/16 | 0.46 → 0.33 | 42% → 33% | 2% → 0% |
| task_board | 5/16 → 4/16 | 2.07 → 1.79 | 87% → 88% | 37% → 21% |
| time_clock | 15/16 → 14/16 | 1.69 → 1.71 | 81% → 94% | 29% → 12% |

| Metric | Base | Seed 42 | Seed 2 | Seed 3 | Seed 3 − base (95%) |
|---|---:|---:|---:|---:|---|
| Changes done before first failure | 1.43 | 1.45 | 1.48 | 1.43 | +0.00 (−0.11 to +0.13) |
| First change works | 67% | 71% | 73% | 70% | +3 pts (−1 to +9) |
| Whole sequence works | 26% | 25% | 26% | 25% | −2 pts (−6 to +3) |
| Writer samples passing the initial checks | 58% | 64% | 62% | 62% | +5 pts (−3 to +14) |

The third seed repeats the other two: no gain on the planned measure. Six
tasks go up and ten down; race_telemetry again gains the most (+0.63), and
without it the mean difference is −0.04. Its first versions pass the
initial checks a few points more often (160 of 256 against 148), as with
the other seeds.

Mean over the three seeds per task, dpo3 minus base (paired task bootstrap
as above; computed after the results with `scripts/hist2_seed_pool.py
--config '../configs/rtx5070_eval{}.yaml' --group base=base
--group dpo3=_dpo3,_dpo3_s2,_dpo3_s3`):

| Metric | Base | dpo3, three seeds | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.45 | +0.03 | −0.06 to +0.14 |
| Per writer sample (a sample failing the initial checks counts 0) | 0.85 | 0.91 | +0.06 | −0.04 to +0.17 |

With three seeds, training on 160 editing-outcome pairs does not change how
far the editor gets on the original testbed.

## Reproduce

From `harness/`, inside WSL, after building `writer-dpo3-ctx8k` as in
`harness/results/dpo3_dev.md`:

```bash
uv run python -m harness collect --config configs/rtx5070_eval_dpo3.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_eval_dpo3.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_eval.yaml \
    --other configs/rtx5070_eval_dpo3.yaml --bootstrap 20000
```
