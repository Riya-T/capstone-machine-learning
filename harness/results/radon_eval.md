# Static-ranking writer (Radon) on the eval tasks

The static-ranking baseline: Qwen2.5-Coder-7B with a QLoRA adapter trained
by DPO on 160 pairs ranked by Radon's Maintainability Index instead of by
editing outcomes. The pairs come from the same 28 train tasks as our DPO
writer's, as many per task as ours (`scripts/static_ranking.py`, then
`scripts/match_pairs.py`; README, "Static-ranking baseline"), and training
uses dpo3's settings: learning rate 2e-5, beta 0.1, 2 epochs, seed 42. Same
16 eval tasks (as of 9ff8854), prompt (`prompts/writer_v1.md`), editor,
budget and selection as the base writer
(`harness/results/base_writer_eval.md`): passing programs, at most 8 per
task in sample order, 2 sequences × 3 repetitions each, 3 changes per
sequence. These tasks were not used for training or for choosing anything.

- Config: `configs/rtx5070_eval_radon.yaml`.
- Training: 40 steps in 25 minutes, peak 8.4 GB. Mean loss 0.67 in the
  first epoch and 0.55 in the second (dpo3: 0.68 and 0.61), reward accuracy
  73% and 99% (dpo3: 64% and 96%), reward margin 0.06 and 0.31 (dpo3: 0.03
  and 0.17). The Radon preferences are easier to fit than the editing ones.
- Export: built like `writer-dpo3-ctx8k` (README, "Serving the trained
  writer") as `writer-radon-ctx8k`. The 143 tensors LoRA does not touch are
  identical to the official file's, and all 196 trained ones differ.
- Run: 20261110T134603Z-31b2e3 at 35306cd, 2026-11-10 05:46 to 2026-11-11
  03:54 PST. No infrastructure errors; 254 of the 256 writer samples parsed.
- Cost: 3,590 editor calls, 6.6M prompt tokens, 3.8M reply tokens, for 1,177
  editing steps on 94 programs (base writer: 4,124, 7.5M and 4.2M for 1,434
  steps on 110). 101 of the steps reuse trials of identical programs other
  writers wrote (5 programs are the base writer's, 2 are dpo3's).

## Results

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| aging_inventory | 8 | 48 | 0.65 of 3 | 42% | 0% |
| auction_house | 3 | 18 | 1.61 of 3 | 61% | 44% |
| document_versions | 8 | 48 | 1.69 of 3 | 79% | 17% |
| elevator_dispatch | 8 | 48 | 0.75 of 3 | 44% | 2% |
| light_grid | 4 | 24 | 2.25 of 3 | 88% | 62% |
| locker_room | 5 | 30 | 1.77 of 3 | 73% | 50% |
| meeting_rooms | 6 | 36 | 1.00 of 3 | 69% | 11% |
| race_telemetry | 3 | 18 | 0.78 of 3 | 61% | 6% |
| rover_fleet | 5 | 30 | 0.57 of 3 | 27% | 10% |
| scoreboard | 8 | 48 | 2.17 of 3 | 94% | 46% |
| seat_reservation | 4 | 24 | 1.67 of 3 | 83% | 29% |
| social_feed | 5 | 30 | 1.83 of 3 | 83% | 33% |
| spending_alerts | 8 | 48 | 0.90 of 3 | 67% | 0% |
| subscription_billing | 8 | 48 | 0.27 of 3 | 27% | 0% |
| task_board | 3 | 18 | 2.06 of 3 | 89% | 39% |
| time_clock | 8 | 48 | 1.65 of 3 | 85% | 17% |
| **Average over 16 tasks** | 94 | 564 | 1.35 | 67% | 23% |

Step endings: success 722, budget_exhausted 293, fail_new 149,
fail_existing 7, fail_both 6.

## Compared with the base writer

Per task, base writer → Radon writer:

| Task | Initial pass | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| aging_inventory | 9/16 → 14/16 | 0.55 → 0.65 | 38% → 42% | 0% → 0% |
| auction_house | 6/16 → 3/16 | 2.31 → 1.61 | 83% → 61% | 64% → 44% |
| document_versions | 16/16 → 16/16 | 1.73 → 1.69 | 85% → 79% | 12% → 17% |
| elevator_dispatch | 9/16 → 8/16 | 0.79 → 0.75 | 44% → 44% | 2% → 2% |
| light_grid | 14/16 → 4/16 | 1.98 → 2.25 | 79% → 88% | 50% → 62% |
| locker_room | 8/16 → 5/16 | 2.25 → 1.77 | 85% → 73% | 67% → 50% |
| meeting_rooms | 9/16 → 6/16 | 1.31 → 1.00 | 71% → 69% | 23% → 11% |
| race_telemetry | 5/16 → 3/16 | 1.20 → 0.78 | 67% → 61% | 13% → 6% |
| rover_fleet | 6/16 → 5/16 | 0.78 → 0.57 | 33% → 27% | 19% → 10% |
| scoreboard | 16/16 → 16/16 | 2.08 → 2.17 | 94% → 94% | 38% → 46% |
| seat_reservation | 3/16 → 4/16 | 1.00 → 1.67 | 39% → 83% | 28% → 29% |
| social_feed | 6/16 → 5/16 | 1.78 → 1.83 | 78% → 83% | 36% → 33% |
| spending_alerts | 8/16 → 9/16 | 0.83 → 0.90 | 58% → 67% | 0% → 0% |
| subscription_billing | 13/16 → 13/16 | 0.46 → 0.27 | 42% → 27% | 2% → 0% |
| task_board | 5/16 → 3/16 | 2.07 → 2.06 | 87% → 89% | 37% → 39% |
| time_clock | 15/16 → 14/16 | 1.69 → 1.65 | 81% → 85% | 29% → 17% |

Paired task bootstrap (20,000 resamples of the 16 tasks, each task's pair
kept together, seed 20261105), Radon writer minus base writer:

| Metric | Base | Radon | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.35 | −0.08 | −0.23 to +0.08 |
| First change works | 67% | 67% | +0 pts | −6 to +8 pts |
| Whole sequence works | 26% | 23% | −3 pts | −8 to +1 pts |
| Writer samples passing the initial checks | 58% | 50% | −8 pts | −18 to +1 pts |

On the main measure the Radon writer is no better than the base writer,
and if anything a little worse: −0.08, with an interval from −0.23 to
+0.08. Per task, 6 tasks go up and 10 go down; the largest drops are
auction_house (2.31 → 1.61) and locker_room (2.25 → 1.77), and the largest
gain is seat_reservation (1.00 → 1.67 on 4 programs). Fewer of its samples
pass the initial checks (128 of 256 against 148); light_grid alone drops
from 14 to 4 of 16. So 8 tasks are scored on only 3 to 5 programs.

The Radon score its pairs train for moves only a little. The mean Radon
Maintainability Index of the eval-task samples (LOC-weighted per program,
averaged per task, then over the 16 tasks) is 43.5 against 42.6 for the
base writer, on a 0–100 scale (no interval computed). The maintainability
prompt gets about the same (43.6), and dpo3 stays at 42.8.
The Radon writer's programs are slightly less varied (243 distinct
programs of 256, against 252) and its replies slightly longer (595 tokens
on average against 564).

## Compared with our writer (dpo3)

Radon writer minus dpo3 (same bootstrap):

| Metric | dpo3 | Radon | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.45 | 1.35 | −0.10 | −0.35 to +0.11 |
| First change works | 71% | 67% | −4 pts | −11 to +3 pts |
| Whole sequence works | 25% | 23% | −3 pts | −10 to +3 pts |
| Writer samples passing the initial checks | 64% | 50% | −14 pts | −24 to −5 pts |

The two trainings saw the same tasks, the same number of pairs and the
same settings; only who picked the winner differs. On how far the editor
gets they cannot be told apart. The one clear difference is the initial
pass rate: dpo3's samples pass 14 points more often (164 of 256 against
128).

All four writers measured so far, on the same 16 eval tasks:

| Metric | Base | Maintainability prompt | dpo3 | Radon |
|---|---:|---:|---:|---:|
| Changes done before first failure | 1.43 | 1.43 | 1.45 | 1.35 |
| First change works | 67% | 70% | 71% | 67% |
| Whole sequence works | 26% | 25% | 25% | 23% |
| Writer samples passing the initial checks | 58% | 60% | 64% | 50% |
| Radon Maintainability Index of the samples | 42.6 | 43.6 | 42.8 | 43.5 |

Training on Radon's ranking moves the Radon score about as much as asking
for maintainable code does, and neither makes the programs easier for the
editor to change.

## Reproduce

From `harness/`, inside WSL, after building `writer-radon-ctx8k` from the
adapter trained as in the README ("Static-ranking baseline"):

```bash
uv run python -m harness collect --config configs/rtx5070_eval_radon.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_eval_radon.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_eval.yaml \
    --other configs/rtx5070_eval_radon.yaml --bootstrap 20000
uv run python scripts/eval_compare.py --base configs/rtx5070_eval_dpo3.yaml \
    --other configs/rtx5070_eval_radon.yaml --bootstrap 20000
```

The Radon Maintainability Index row uses `maintainability_score` from
`scripts/static_ranking.py` on every parsed sample (samples that are not
valid Python are skipped).
