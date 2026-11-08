# Base writer on the dev tasks

The original writer (Qwen2.5-Coder-7B, no training, `prompts/writer_v1.md`)
on the 8 dev tasks, with the same frozen editor, budget and selection as the
eval runs (`harness/results/base_writer_eval.md`). Dev tasks are where
training settings are chosen (learning rate, passes over the data, DPO's
beta, the pair cap), so the eval tasks stay untouched until the final
comparison. Dev sequences have 2 changes.

- Config: `configs/rtx5070_pc.yaml`.
- Task files: as of 9ff8854 (`library_catalog` after its 2026-11-05
  redesign).
- Runs: 20261105T201359Z-f451b1 (library_catalog) and 20261108T045940Z-8a64a4
  (the other 7), finished 2026-11-08. No infrastructure errors.

| Task | Programs | Trials | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|---|
| bank_ledger | 8 | 48 | 1.90 of 2 | 96% | 94% |
| course_enrollment | 8 | 48 | 1.92 of 2 | 98% | 94% |
| football_season | 6 | 36 | 1.31 of 2 | 67% | 64% |
| library_catalog | 6 | 36 | 1.39 of 2 | 78% | 61% |
| lru_cache | 7 | 42 | 0.50 of 2 | 36% | 14% |
| parking_garage | 4 | 24 | 0.62 of 2 | 33% | 29% |
| shopping_cart | 5 | 30 | 1.50 of 2 | 100% | 50% |
| team_roster | 7 | 42 | 0.86 of 2 | 67% | 19% |
| **Average over 8 tasks** | 51 | 306 | 1.25 | 72% | 53% |

Step endings: success 397, fail_new 72, budget_exhausted 53, fail_both 5,
fail_existing 5.

bank_ledger and course_enrollment are near the ceiling, so a better writer
can show little there; lru_cache, parking_garage and team_roster leave the
most room.

## Reproduce

From `harness/`, inside WSL:

```bash
uv run python -m harness collect --config configs/rtx5070_pc.yaml
uv run python scripts/eval_summary.py --config configs/rtx5070_pc.yaml --bootstrap 20000
```
