# Correctness-only writer (SFT) on the eval tasks

The correctness-only baseline: Qwen2.5-Coder-7B with a QLoRA adapter
fine-tuned on the writer's own programs that pass the initial checks, with
no preference between them. The programs are the first 8 passing ones of
each of the 28 train tasks our DPO pairs come from, the programs the editor
worked on: 201 programs, which include all 157 programs in our pairs
(`scripts/sft_programs.py`; README, "Correctness-only baseline"). Training
(`harness.train_sft`) uses dpo3's setup with the plain supervised loss:
learning rate 2e-5, 2 epochs, 8 examples per step, seed 42. Same 16 eval
tasks (as of 9ff8854), prompt (`prompts/writer_v1.md`), editor, budget and
selection as the base writer (`harness/results/base_writer_eval.md`):
passing programs, at most 8 per task in sample order, 2 sequences × 3
repetitions each, 3 changes per sequence. These tasks were not used for
training or for choosing anything.

- Config: `configs/rtx5070_eval_sft.yaml`.
- Training: 51 steps in 16 minutes, peak 7.5 GB. Mean loss per program
  token 0.038 in the first epoch and 0.024 in the second (0.051 at the
  first step, 0.019 at the last); it starts low because the programs are
  the writer's own samples.
- Export: built like `writer-dpo3-ctx8k` (README, "Serving the trained
  writer") as `writer-sft-ctx8k`. The 143 tensors LoRA does not touch are
  identical to the official file's, and all 196 trained ones differ.
- Run: 20261111T122905Z-5cae35 at 0ff2a58, 2026-11-11 04:29 to 2026-11-12
  03:34 PST. No infrastructure errors; 255 of the 256 writer samples parsed.
- Cost: 4,091 editor calls, 7.3M prompt tokens, 4.1M reply tokens, for
  1,501 editing steps on 111 programs (base writer: 4,124, 7.5M and 4.2M
  for 1,434 steps on 110). 214 of the steps reuse trials of identical
  programs other writers wrote (10 programs are the base writer's, 5 are
  dpo3's, 3 are the Radon writer's).

## Results

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| aging_inventory | 8 | 48 | 0.40 of 3 | 29% | 0% |
| auction_house | 8 | 48 | 2.46 of 3 | 96% | 67% |
| document_versions | 8 | 48 | 1.98 of 3 | 96% | 10% |
| elevator_dispatch | 8 | 48 | 0.90 of 3 | 54% | 4% |
| light_grid | 8 | 48 | 2.54 of 3 | 96% | 65% |
| locker_room | 7 | 42 | 2.36 of 3 | 88% | 71% |
| meeting_rooms | 8 | 48 | 0.98 of 3 | 73% | 6% |
| race_telemetry | 5 | 30 | 2.17 of 3 | 90% | 53% |
| rover_fleet | 4 | 24 | 0.79 of 3 | 42% | 12% |
| scoreboard | 8 | 48 | 2.08 of 3 | 90% | 42% |
| seat_reservation | 3 | 18 | 0.72 of 3 | 50% | 6% |
| social_feed | 8 | 48 | 1.79 of 3 | 83% | 31% |
| spending_alerts | 6 | 36 | 0.69 of 3 | 56% | 0% |
| subscription_billing | 8 | 48 | 0.29 of 3 | 29% | 0% |
| task_board | 6 | 36 | 1.81 of 3 | 89% | 25% |
| time_clock | 8 | 48 | 1.62 of 3 | 90% | 12% |
| **Average over 16 tasks** | 111 | 666 | 1.47 | 72% | 25% |

Step endings: success 1008, budget_exhausted 325, fail_new 149,
fail_existing 12, fail_both 7.

## Compared with the base writer

Per task, base writer → correctness-only writer:

| Task | Initial pass | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| aging_inventory | 9/16 → 14/16 | 0.55 → 0.40 | 38% → 29% | 0% → 0% |
| auction_house | 6/16 → 9/16 | 2.31 → 2.46 | 83% → 96% | 64% → 67% |
| document_versions | 16/16 → 15/16 | 1.73 → 1.98 | 85% → 96% | 12% → 10% |
| elevator_dispatch | 9/16 → 12/16 | 0.79 → 0.90 | 44% → 54% | 2% → 4% |
| light_grid | 14/16 → 15/16 | 1.98 → 2.54 | 79% → 96% | 50% → 65% |
| locker_room | 8/16 → 9/16 | 2.25 → 2.36 | 85% → 88% | 67% → 71% |
| meeting_rooms | 9/16 → 16/16 | 1.31 → 0.98 | 71% → 73% | 23% → 6% |
| race_telemetry | 5/16 → 5/16 | 1.20 → 2.17 | 67% → 90% | 13% → 53% |
| rover_fleet | 6/16 → 4/16 | 0.78 → 0.79 | 33% → 42% | 19% → 12% |
| scoreboard | 16/16 → 15/16 | 2.08 → 2.08 | 94% → 90% | 38% → 42% |
| seat_reservation | 3/16 → 3/16 | 1.00 → 0.72 | 39% → 50% | 28% → 6% |
| social_feed | 6/16 → 8/16 | 1.78 → 1.79 | 78% → 83% | 36% → 31% |
| spending_alerts | 8/16 → 7/16 | 0.83 → 0.69 | 58% → 56% | 0% → 0% |
| subscription_billing | 13/16 → 15/16 | 0.46 → 0.29 | 42% → 29% | 2% → 0% |
| task_board | 5/16 → 6/16 | 2.07 → 1.81 | 87% → 89% | 37% → 25% |
| time_clock | 15/16 → 15/16 | 1.69 → 1.62 | 81% → 90% | 29% → 12% |

Paired task bootstrap (20,000 resamples of the 16 tasks, each task's pair
kept together, seed 20261105), correctness-only writer minus base writer:

| Metric | Base | Correctness-only | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.47 | +0.05 | −0.09 to +0.22 |
| First change works | 67% | 72% | +5 pts | +1 to +10 pts |
| Whole sequence works | 26% | 25% | −1 pt | −7 to +6 pts |
| Writer samples passing the initial checks | 58% | 66% | +8 pts | +1 to +15 pts |

On the main measure the correctness-only writer is no better than the base
writer: +0.05, with an interval from −0.09 to +0.22. Per task, 8 tasks go
up, 7 down and 1 stays the same. As with dpo3, race_telemetry carries the
average (1.20 → 2.17 on 5 programs; dpo3 2.23); without it, the mean
difference is about −0.01. Its samples pass the initial checks more often
(168 of 256 against 148; +8 pts, +1 to +15) and the first change works a
little more often (+5 pts, +1 to +10). Its programs are less varied (234
distinct programs of 256, against 252), and its replies are as long as the
base writer's (565 tokens on average against 564).

## Compared with our writer (dpo3)

Correctness-only writer minus dpo3 (same bootstrap):

| Metric | dpo3 | Correctness-only | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.45 | 1.47 | +0.03 | −0.05 to +0.10 |
| First change works | 71% | 72% | +1 pt | −2 to +4 pts |
| Whole sequence works | 25% | 25% | −0 pts | −2 to +2 pts |
| Writer samples passing the initial checks | 64% | 66% | +2 pts | −5 to +8 pts |

The correctness-only writer saw the same programs as dpo3 but not which of
them were easier to change, and the two cannot be told apart on any
measure. Their intervals are the narrowest of any comparison so far
(−0.05 to +0.10 on the main measure): the two writers behave alike task by
task. So dpo3's higher pass rate (+6 pts against the base writer) and its
slightly more frequent first change most likely come from training on the
writer's own passing programs, not from the editing preferences (one seed
each). The Radon writer, whose pairs also compare passing programs, passes
less often (50%); there the formula's preferences seem to work against the
pass rate.

All five writers, on the same 16 eval tasks:

| Metric | Base | Maintainability prompt | dpo3 | Radon | Correctness-only |
|---|---:|---:|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.43 | 1.45 | 1.35 | 1.47 |
| First change works | 67% | 70% | 71% | 67% | 72% |
| Whole sequence works | 26% | 25% | 25% | 23% | 25% |
| Writer samples passing the initial checks | 58% | 60% | 64% | 50% | 66% |
| Distinct programs among 256 samples | 252 | – | 252 | 243 | 234 |
| Radon Maintainability Index of the samples | 42.6 | 43.6 | 42.8 | 43.5 | 42.6 |

None of the five makes the programs measurably easier for the editor to
change, and DPO on 160 editing-outcome pairs does no better than plain
fine-tuning on the same programs.

## Reproduce

From `harness/`, inside WSL, after building `writer-sft-ctx8k` from the
adapter trained as in the README ("Correctness-only baseline"):

```bash
uv run python -m harness collect --config configs/rtx5070_eval_sft.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_eval_sft.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_eval.yaml \
    --other configs/rtx5070_eval_sft.yaml --bootstrap 20000
uv run python scripts/eval_compare.py --base configs/rtx5070_eval_dpo3.yaml \
    --other configs/rtx5070_eval_sft.yaml --bootstrap 20000
```

The Radon Maintainability Index row is computed as in
`harness/results/radon_eval.md`.
