# DPO writer (dpo2) on the dev tasks

The first DPO writer worth scoring: Qwen2.5-Coder-7B with a QLoRA adapter
trained by `harness.train_dpo` on the filtered train pairs (at most 8 per
task, chosen program wins in at least 2 of 3 repetitions, cosmetic pairs
dropped: 160 pairs from 28 train tasks), beta 0.1, learning rate 5e-5, 2
epochs, seed 42. The adapter is merged into the base weights and quantized to
Q4_K_M exactly like the base writer's GGUF (README, "Serving the trained
writer"). Same 8 dev tasks, prompt (`prompts/writer_v1.md`), editor, budget
and selection as the base writer (`harness/results/base_writer_dev.md`).

- Config: `configs/rtx5070_dev_dpo2.yaml`.
- Training: 40 optimizer steps of 8 pairs, 26 minutes, 8.3 GB peak. Mean
  loss 0.62 over the first pass and 0.35 over the second (0.69 at the
  start, 0.21 at the last step). In the second pass the adapter preferred
  the chosen program in 98% of the training pairs.
- Run: 20261109T001859Z-99203f, started at a706a94 with the export changes
  of cbd7d97 not yet committed, finished 2026-11-08. No infrastructure
  errors. One of the 128 writer samples hit the 4,096-token limit
  (football_season).
- Cost: 984 editor calls, 1.5M prompt tokens, 0.8M reply tokens (base
  writer: 1,159, 1.6M and 0.9M). Four dpo2 programs are identical to
  programs the base writer wrote (bank_ledger 1, lru_cache 1,
  shopping_cart 2). Results are keyed by the program, so those reuse the
  base writer's trials (34 of the 459 editing steps).

## Results

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| bank_ledger | 8 | 48 | 1.83 of 2 | 94% | 90% |
| course_enrollment | 4 | 24 | 1.92 of 2 | 100% | 92% |
| football_season | 7 | 42 | 1.02 of 2 | 57% | 45% |
| library_catalog | 1 | 6 | 1.33 of 2 | 67% | 67% |
| lru_cache | 6 | 36 | 0.58 of 2 | 39% | 19% |
| parking_garage | 8 | 48 | 0.60 of 2 | 33% | 27% |
| shopping_cart | 4 | 24 | 1.50 of 2 | 100% | 50% |
| team_roster | 8 | 48 | 0.92 of 2 | 67% | 25% |
| **Average over 8 tasks** | 46 | 276 | 1.21 | 70% | 52% |

Step endings: success 315, fail_new 83, budget_exhausted 57, fail_both 2,
fail_existing 2.

## Compared with the base writer

Per task, base writer → dpo2:

| Task | Initial pass | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bank_ledger | 16/16 → 16/16 | 1.90 → 1.83 | 96% → 94% | 94% → 90% |
| course_enrollment | 12/16 → 15/16 | 1.92 → 1.92 | 98% → 100% | 94% → 92% |
| football_season | 6/16 → 7/16 | 1.31 → 1.02 | 67% → 57% | 64% → 45% |
| library_catalog | 6/16 → 1/16 | 1.39 → 1.33 | 78% → 67% | 61% → 67% |
| lru_cache | 15/16 → 14/16 | 0.50 → 0.58 | 36% → 39% | 14% → 19% |
| parking_garage | 4/16 → 8/16 | 0.62 → 0.60 | 33% → 33% | 29% → 27% |
| shopping_cart | 5/16 → 6/16 | 1.50 → 1.50 | 100% → 100% | 50% → 50% |
| team_roster | 7/16 → 8/16 | 0.86 → 0.92 | 67% → 67% | 19% → 25% |

Paired task bootstrap (20,000 resamples of the 8 tasks, each task's pair
kept together, seed 20261105), dpo2 minus base writer:

| Metric | Base | dpo2 | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.25 | 1.21 | −0.03 | −0.11 to +0.03 |
| First change works | 72% | 70% | −2 pts | −6 to +1 pts |
| Whole sequence works | 53% | 52% | −1 pt | −7 to +3 pts |
| Writer samples passing the initial checks | 55% | 59% | +3 pts | −9 to +13 pts |

dpo2's programs are no easier to change. The main measure is slightly
lower, and its interval includes 0 but lies mostly below it. Per task
the differences go both ways: football_season fell (1.31 → 1.02), while
lru_cache (0.50 → 0.58) and team_roster (0.86 → 0.92) rose slightly.

The trained writer repeats itself more:

| | Base | dpo2 |
|---|---:|---:|
| Distinct programs among the 128 samples | 113 | 101 |
| Samples passing the initial checks | 71 | 75 |
| Distinct passing programs | 61 | 52 |
| Mean reply length (tokens) | 534 | 495 |

The clearest case is course_enrollment: 15 of 16 samples pass, but they
are only 4 different programs (base writer: 11 of its 12). library_catalog
went the other way: 1 of 16 samples pass (base writer: 6). Its failures
are the tests the base writer also fails most (loans listed in catalog
order, the history after adding copies, each borrower's own loans), just
more often. So that task contributes a single program here.

With a low training loss, near-perfect preference for the chosen program
and less varied output, dpo2 looks over-optimized on its 160 pairs.
Because dpo2 does not improve on the dev tasks, the eval tasks are not run
with it. The next setting is the same training at learning rate 2e-5
(`configs/rtx5070_dev_dpo3.yaml`).

## Reproduce

From `harness/`, inside WSL, after building `writer-dpo2-ctx8k` as in the
README:

```bash
uv run python -m harness collect --config configs/rtx5070_dev_dpo2.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_dev_dpo2.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_pc.yaml \
    --other configs/rtx5070_dev_dpo2.yaml --bootstrap 20000
```
