# DPO+NLL writer (hist2_rpo_d) on the history-suite eval tasks

The writer is Qwen2.5-Coder-7B with a QLoRA adapter. It was trained by
DPO+NLL (`train_dpo.py --nll-weight 1`, lr 3e-5, 3 epochs, beta 0.1, LoRA
r16) on the 83 pairs of the hint2 train collection: 16 train tasks of the
history suite, 16 samples each, three quarters of them shown a worked
example of a copy-of-state design (`configs/rtx5070_hist_train_hints2.yaml`).
The pairs use the plain prompt, so the writer has to adopt the design
without being shown it. Setting D was chosen from five settings on the four
dev tasks (writer samples only), by a rule fixed before it was trained
(`harness/tasks/HISTORY_SUITE.md`):

| Setting | lr, epochs | Passing dev programs | Copy design among them |
|---|---|---:|---:|
| base | – | 30 | 0 |
| plain DPO (`hist2_dpo`) | 2e-5, 2 | 21 | 0 |
| A (`hist2_rpo`) | 2e-5, 2 | 27 | 0 |
| **D (`hist2_rpo_d`)** | **3e-5, 3** | **20** | **10** |
| C (`hist2_rpo_c`) | 5e-5, 2 | 18 | 11 |
| B (`hist2_rpo_b`) | 5e-5, 3 | 7 | 4 |

The eval used the 10 eval tasks of the history suite, with the same prompt
(`prompts/writer_v1.md`) and editor for both writers. The editor was the
frozen Qwen2.5-Coder-14B with 5 turns, 1 trial per sequence. Each task has
2 sequences of 3 changes: s1 starts with undo, s2 with another change. Up
to 8 passing programs per task were edited, in sample order. These settings
were fixed before any eval trial.

- Configs: `configs/rtx5070_hist2_eval_hist2_rpo_d.yaml`,
  `configs/rtx5070_hist2_eval.yaml` (base).
- Runs: 20261118T220928Z-4bf8af (D, 156 editing steps) and
  20261119T013930Z-90962e (base, 179 steps), at e9e16cd's code. No
  infrastructure errors.

## Results

| Task | Initial pass (base → D) | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bike_docks | 8/16 → 1/16 | 0.00 → 0.00 | 0% → 0% | 0% → 0% |
| canal_locks | 13/16 → 6/16 | 0.12 → 0.17 | 12% → 17% | 0% → 0% |
| coin_vaults | 11/16 → 6/16 | 0.12 → 0.25 | 12% → 25% | 0% → 0% |
| grain_silos | 10/16 → 6/16 | 0.50 → 0.50 | 50% → 50% | 0% → 0% |
| museum_galleries | 7/16 → 10/16 | 0.29 → 0.44 | 29% → 44% | 0% → 0% |
| rehearsal_setlists | 5/16 → 4/16 | 0.50 → 0.88 | 50% → 62% | 0% → 0% |
| server_racks | 10/16 → 12/16 | 0.50 → 0.88 | 50% → 56% | 0% → 12% |
| spare_parts | 14/16 → 4/16 | 0.50 → 1.12 | 50% → 62% | 0% → 25% |
| tour_itineraries | 14/16 → 11/16 | 0.25 → 0.75 | 25% → 50% | 0% → 12% |

recipe_binder has no edited program for at least one writer, so the
comparison has 9 tasks. The paired task bootstrap (20000 resamples, seed
20261105) gives:

| Metric | Base | D | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 0.31 | 0.55 | +0.24 | +0.10 to +0.39 |
| First change works | 31% | 41% | +10 pts | +5 to +15 pts |
| Whole sequence works | 0% | 6% | +6 pts | +0 to +11 pts |
| Writer samples passing the initial checks | 64% | 42% | −22 pts | −38 to −5 pts |

So the editor gets further on D's programs than on the base writer's, but
fewer of D's samples pass the initial checks.

## What the gain is, and what it isn't

- **Per sample (computed after the results, not planned):** counting a
  sample that fails the initial checks as 0 changes, over all 10 tasks, the
  base writer scores 0.17 changes per sample and D scores 0.23. The
  difference is +0.05 (95% −0.04 to +0.15). If programs are tested before
  they are edited, as here, the planned measure above applies. Per sample,
  the lower pass rate cancels most of the gain.
- **Undo first:** on s1, no base program got its first change done (0 of
  69). For D, 7 of 51 did (mean 0.27 changes). On s2, the first change
  works for 75% of D's programs and 59% of the base writer's.
- **How the editor's steps end:** for the base writer, 23% succeed, 30%
  fail the new tests and 47% run out of turns. For D, 38% succeed, 32% fail
  the new tests and 28% run out of turns.
- **Not the copy design, as far as we can tell:** `design_classes.py`
  marks 29 of D's 60 passing eval programs as copy designs, against 0 of
  the base writer's 92. But on eval these scored lower than D's other
  programs (0.38 against 0.79), and all 7 of D's undo-first successes are
  in-place programs. The classifier counts any `deepcopy` in a mutating
  method, so it includes programs that copy one list. D's programs are
  easier to edit for reasons this classifier doesn't capture. They don't
  differ from the base writer's in length, number of methods or classes.
## Correctness-only control

The control (`hist2_sft`, `configs/rtx5070_hist2_eval_hist2_sft.yaml`, run
20261119T063506Z-842b2f, 168 steps, no infrastructure errors) is SFT on
the same train collection's passing programs. It uses the first 8 per task
in sample order, 83 in all, with both designs, the plain prompt and D's lr
and epochs. It uses no editing outcomes. So it has the same hinted programs
and the same amount of training as D, and lacks only the editor's
preferences. On the dev tasks, 1 of its 29 passing programs used the copy
design. Same 9 tasks, same bootstrap:

| Metric | Base | Control | Control − base (95%) | D | D − control (95%) |
|---|---:|---:|---:|---:|---:|
| Changes done before first failure | 0.31 | 0.33 | +0.02 (−0.03 to +0.06) | 0.55 | +0.22 (+0.07 to +0.40) |
| First change works | 31% | 30% | −1 pts (−6 to +4) | 41% | +10 pts (+2 to +19) |
| Whole sequence works | 0% | 0% | +0 pts (+0 to +0) | 6% | +6 pts (+0 to +11) |
| Writer samples passing the initial checks | 64% | 53% | −11 pts (−21 to −1) | 42% | −11 pts (−24 to +1) |

Counting failing samples as 0 changes (computed after the results, all 10
tasks): base 0.17, control 0.16, D 0.23. D − control is +0.07 (95% −0.01
to +0.15). The control's steps end in success for 25%, in failed new tests
for 30% and in running out of turns for 44%, much like the base writer's.

So training on the same programs without the editor's preferences doesn't
make them any easier to edit. D's gain comes from the editor's outcomes:
which program of a pair is preferred, which also decides the programs the
NLL term trains on. Half of
D's loss in pass rate is shared with the control (training on these
programs at all costs 11 points). The other half is specific to DPO+NLL,
and its interval reaches +1. The second seed below does not show this
extra loss.

## Second training seed

`hist2_rpo_d_s43` is D trained again with seed 43, which changes the LoRA
initialisation and the order of the pairs. The pairs, settings and code are
the same. It ran with the same eval settings, against the same base and
control runs (`configs/rtx5070_hist2_eval_hist2_rpo_d_s43.yaml`, run
20261119T114314Z-8ac0c3, 205 editing steps, no infrastructure errors). Its
training curve is like seed 42's: reward accuracy 0.88 to 1.0 from step 5
on, and the chosen NLL falls from 0.13 to 0.08. On the dev tasks, 11 of its
15 passing programs used the copy design (seed 42: 10 of 20).

| Task | Initial pass (base → seed 43) | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bike_docks | 8/16 → 5/16 | 0.00 → 0.30 | 0% → 20% | 0% → 0% |
| canal_locks | 13/16 → 9/16 | 0.12 → 0.25 | 12% → 25% | 0% → 0% |
| coin_vaults | 11/16 → 6/16 | 0.12 → 0.33 | 12% → 25% | 0% → 0% |
| grain_silos | 10/16 → 8/16 | 0.50 → 0.62 | 50% → 50% | 0% → 6% |
| museum_galleries | 7/16 → 13/16 | 0.29 → 0.25 | 29% → 25% | 0% → 0% |
| recipe_binder | 1/16 → 1/16 | 0.00 → 1.50 | 0% → 100% | 0% → 0% |
| rehearsal_setlists | 5/16 → 7/16 | 0.50 → 0.93 | 50% → 64% | 0% → 7% |
| server_racks | 10/16 → 12/16 | 0.50 → 1.44 | 50% → 69% | 0% → 38% |
| spare_parts | 14/16 → 5/16 | 0.50 → 1.30 | 50% → 70% | 0% → 20% |
| tour_itineraries | 14/16 → 11/16 | 0.25 → 1.19 | 25% → 69% | 0% → 25% |

Both writers have an edited program on all 10 tasks, so the planned
comparison has 10:

| Metric | Base | Seed 43 | Difference | 95% interval |
|---|---:|---:|---:|---:|
| Changes done before first failure | 0.28 | 0.81 | +0.53 | +0.26 to +0.83 |
| First change works | 28% | 52% | +24 pts | +10 to +44 pts |
| Whole sequence works | 0% | 10% | +10 pts | +3 to +18 pts |
| Writer samples passing the initial checks | 58% | 48% | −10 pts | −25 to +6 pts |

recipe_binder rests on one passing sample per writer, and the task
bootstrap weighs it like the other tasks. Leaving it out gives the 9 tasks
of seed 42's comparisons. The control and seed 42 have no edited program on
recipe_binder, so their comparisons have these 9 tasks anyway:

| Metric | Seed 43 − base | Seed 43 − control | Seed 43 − seed 42 |
|---|---|---|---|
| Changes done before first failure | +0.43 (+0.20 to +0.66) | +0.41 (+0.18 to +0.66) | +0.18 (+0.04 to +0.32) |
| First change works | +15 pts (+7 to +24) | +16 pts (+7 to +26) | +6 pts (−2 to +12) |
| Whole sequence works | +11 pts (+3 to +20) | +11 pts (+3 to +20) | +5 pts (+0 to +11) |
| Writer samples passing the initial checks | −11 pts (−28 to +7) | +0 pts (−13 to +12) | +11 pts (+5 to +17) |

- **Per sample (computed after the results, all 10 tasks):** base 0.17,
  control 0.16, seed 42 0.23, seed 43 0.37. Seed 43 − base is +0.19 (95%
  +0.05 to +0.36), and seed 43 − control is +0.21 (+0.08 to +0.37).
- **How the editor's steps end:** 46% succeed, 27% fail the new tests and
  27% run out of turns.
- **Undo first:** on s1, the first change works for 14 of seed 43's 64
  edited programs: 11 of 33 in-place programs and 3 of 31 copy programs.
  The base writer gets 0 of 69 and seed 42 gets 7 of 51.
- **Designs:** 37 of its 77 passing eval programs are classed as copy
  designs. As with seed 42, they score lower than its other programs (0.52
  against 0.97).

So:

- **The gain replicates.** With both training seeds, the editor gets
  further on the trained writer's programs than on the base writer's or the
  control's. Every interval of the main measure excludes 0.
- **Its size depends on the seed.** Seed 43's gain is nearly twice seed
  42's on the same 9 tasks, and the interval of their difference excludes
  0. The task bootstrap doesn't include training-seed variation, and two
  seeds measure it only roughly.
- **No extra pass-rate cost with seed 43.** Seed 42's extra loss in pass
  rate beyond the control's doesn't recur: seed 43 passes as often as the
  control, 11 points below the base writer (interval −28 to +7). With seed
  43, even the per-sample measure is clearly positive.
- **Still not the copy design,** as far as the classifier can tell.
