# DPO writer (dpo3) on the dev tasks

The second DPO setting: the same training as dpo2
(`harness/results/dpo2_dev.md`: 160 filtered pairs from 28 train tasks,
beta 0.1, 2 epochs, seed 42) at learning rate 2e-5 instead of 5e-5, after
dpo2 came out over-optimized. Built and served the same way (README,
"Serving the trained writer"). Same 8 dev tasks, prompt, editor, budget and
selection as the base writer (`harness/results/base_writer_dev.md`).

- Config: `configs/rtx5070_dev_dpo3.yaml`.
- Training: 40 optimizer steps of 8 pairs, 25 minutes, 8.3 GB peak. Mean
  loss 0.68 over the first pass and 0.61 over the second (0.55 at the last
  step; dpo2: 0.35 over the second pass). In the second pass the adapter
  preferred the chosen program in 96% of the training pairs, but by a much
  smaller margin than dpo2 (mean reward margin 0.17 against 1.07).
- Export: the 143 tensors the adapter does not touch are identical to the
  official GGUF's; all 196 trained tensors differ.
- Run: 20261109T070911Z-de241d at 5b81863, finished 2026-11-09. No
  infrastructure errors; all 128 writer samples parsed.
- Cost: 847 editor calls, 1.1M prompt tokens, 0.7M reply tokens (base
  writer: 1,159, 1.6M and 0.9M). Five dpo3 programs are identical to
  programs the base writer wrote (bank_ledger 2, lru_cache 2,
  parking_garage 1) and reuse its trials (81 of the 519 editing steps).

## Results

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| bank_ledger | 8 | 48 | 1.65 of 2 | 85% | 79% |
| course_enrollment | 8 | 48 | 1.92 of 2 | 100% | 92% |
| football_season | 3 | 18 | 1.22 of 2 | 67% | 56% |
| library_catalog | 7 | 42 | 1.57 of 2 | 90% | 67% |
| lru_cache | 5 | 30 | 0.73 of 2 | 47% | 27% |
| parking_garage | 3 | 18 | 0.83 of 2 | 44% | 39% |
| shopping_cart | 8 | 48 | 1.50 of 2 | 100% | 50% |
| team_roster | 6 | 36 | 0.89 of 2 | 61% | 28% |
| **Average over 8 tasks** | 48 | 288 | 1.29 | 74% | 55% |

Step endings: success 400, fail_new 63, budget_exhausted 49, fail_both 4,
fail_existing 3.

## Compared with the base writer

Per task, base writer → dpo3:

| Task | Initial pass | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bank_ledger | 16/16 → 16/16 | 1.90 → 1.65 | 96% → 85% | 94% → 79% |
| course_enrollment | 12/16 → 13/16 | 1.92 → 1.92 | 98% → 100% | 94% → 92% |
| football_season | 6/16 → 3/16 | 1.31 → 1.22 | 67% → 67% | 64% → 56% |
| library_catalog | 6/16 → 7/16 | 1.39 → 1.57 | 78% → 90% | 61% → 67% |
| lru_cache | 15/16 → 13/16 | 0.50 → 0.73 | 36% → 47% | 14% → 27% |
| parking_garage | 4/16 → 3/16 | 0.62 → 0.83 | 33% → 44% | 29% → 39% |
| shopping_cart | 5/16 → 8/16 | 1.50 → 1.50 | 100% → 100% | 50% → 50% |
| team_roster | 7/16 → 6/16 | 0.86 → 0.89 | 67% → 61% | 19% → 28% |

Paired task bootstrap (20,000 resamples of the 8 tasks, each task's pair
kept together, seed 20261105), dpo3 minus base writer:

| Metric | Base | dpo3 | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.25 | 1.29 | +0.04 | −0.07 to +0.14 |
| First change works | 72% | 74% | +3 pts | −3 to +8 pts |
| Whole sequence works | 53% | 55% | +1 pt | −5 to +7 pts |
| Writer samples passing the initial checks | 55% | 54% | −2 pts | −9 to +6 pts |

dpo3 is slightly ahead of the base writer on the main measure, but the
interval includes 0, so 8 dev tasks cannot tell it apart from no change.
The gains are on three of the tasks with the most room (lru_cache 0.50 →
0.73, parking_garage 0.62 → 0.83, library_catalog 1.39 → 1.57). The
largest loss is on bank_ledger (1.90 → 1.65), which was near the ceiling.
football_season and parking_garage rest on only 3 programs each, so their
numbers move a lot with one program.

Unlike dpo2, dpo3 keeps the base writer's variety:

| | Base | dpo2 | dpo3 |
|---|---:|---:|---:|
| Changes done before first failure | 1.25 | 1.21 | 1.29 |
| Distinct programs among the 128 samples | 113 | 101 | 114 |
| Samples passing the initial checks | 71 | 75 | 69 |
| Distinct passing programs | 61 | 52 | 57 |
| Mean reply length (tokens) | 534 | 495 | 467 |

course_enrollment has 10 different passing programs (dpo2: 4), and
library_catalog passes 7 of 16 samples (dpo2: 1). Replies are shorter than
the base writer's, mostly on football_season (1,019 → 583 tokens on
average).

dpo3 does more changes before the first failure than the base writer on
the dev tasks, which was the condition for scoring a DPO writer on the eval
tasks (`configs/rtx5070_eval_dpo3.yaml`, started 2026-11-09). Those 16
tasks give the actual comparison.

## Reproduce

From `harness/`, inside WSL, after building `writer-dpo3-ctx8k` as in the
README (adapter trained with `--learning-rate 2e-5 --max-length 3200`):

```bash
uv run python -m harness collect --config configs/rtx5070_dev_dpo3.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_dev_dpo3.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_pc.yaml \
    --other configs/rtx5070_dev_dpo3.yaml --bootstrap 20000
```
