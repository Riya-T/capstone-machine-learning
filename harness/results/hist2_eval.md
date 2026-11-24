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
- Task files: coin_vaults, grain_silos, rehearsal_setlists and
  server_racks as before c066f99, which later added Usage sections to their
  reference and bug files, for every writer on this page. Stored results
  are keyed by a hash of every task file, so reading these back needs
  `git checkout c066f99^ -- harness/tasks/<task>` for those four.

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

## Third training seed

`hist2_rpo_d_s44` is D trained a third time, with seed 44, on the same
pairs and settings (`configs/rtx5070_hist2_eval_hist2_rpo_d_s44.yaml`, run
20261120T051632Z-c1e2ad, 162 editing steps, no infrastructure errors), with
the 4 eval tasks' files from before c066f99 like the other writers. Its
training ends like the others' (reward accuracy 1.0, chosen NLL 0.08). On
the dev tasks, 11 of its 19 passing programs use the copy design. Its
comparisons were fixed before the run (`docs/progress_report.md`, "Third
training seed of D").

| Task | Initial pass (base → seed 44) | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bike_docks | 8/16 → 4/16 | 0.00 → 0.25 | 0% → 25% | 0% → 0% |
| canal_locks | 13/16 → 11/16 | 0.12 → 0.19 | 12% → 19% | 0% → 0% |
| coin_vaults | 11/16 → 5/16 | 0.12 → 0.40 | 12% → 40% | 0% → 0% |
| grain_silos | 10/16 → 6/16 | 0.50 → 1.25 | 50% → 58% | 0% → 33% |
| museum_galleries | 7/16 → 11/16 | 0.29 → 0.31 | 29% → 31% | 0% → 0% |
| recipe_binder | 1/16 → 0/16 | 0.00 → – | – | – |
| rehearsal_setlists | 5/16 → 5/16 | 0.50 → 1.10 | 50% → 70% | 0% → 0% |
| server_racks | 10/16 → 12/16 | 0.50 → 1.56 | 50% → 75% | 0% → 31% |
| spare_parts | 14/16 → 0/16 | 0.50 → – | – | – |
| tour_itineraries | 14/16 → 12/16 | 0.25 → 0.81 | 25% → 50% | 0% → 12% |

Seed 44 has no passing sample on recipe_binder and spare_parts, so the
planned comparisons use the other 8 tasks:

| Metric | Seed 44 − base | Seed 44 − control | Seed 44 − prompted | Seed 44 − seed 42 | Seed 44 − seed 43 |
|---|---|---|---|---|---|
| Changes done before first failure | +0.45 (+0.23 to +0.69) | +0.41 (+0.19 to +0.66) | −0.19 (−0.41 to −0.01) | +0.25 (+0.06 to +0.46) | +0.07 (−0.10 to +0.26) |
| First change works | +17 pts (+11 to +24) | +16 pts (+10 to +21) | −12 pts (−23 to +1) | +8 pts (+0 to +15) | +3 pts (−5 to +9) |
| Whole sequence works | +10 pts (+2 to +20) | +10 pts (+2 to +20) | −3 pts (−9 to +3) | +7 pts (+0 to +15) | +0 pts (−6 to +9) |
| Writer samples passing the initial checks | −9 pts (−22 to +5) | +2 pts (−5 to +9) | +37 pts (+23 to +51) | +8 pts (+1 to +16) | −4 pts (−9 to +2) |

- **Per sample (all 10 tasks, a task without an edited program counting
  0):** seed 44 scores 0.31. Against the base writer +0.14 (−0.05 to
  +0.34), the control +0.15 (−0.00 to +0.33) and the prompted writer +0.17
  (−0.02 to +0.40). Its two tasks without a passing sample cost it here:
  the base writer passes 14 of 16 on spare_parts.
- **Pass rate on all 10 tasks:** 66 of 160 samples (41%), against 58% for
  the base writer, 38% for seed 42 and 48% for seed 43.
- **Within design classes:** its in-place programs score +0.55 (+0.18 to
  +0.96, 7 tasks) above the base writer's in-place programs. Its copy
  programs score below the prompted writer's (−0.26, −0.50 to −0.03), and
  its in-place programs as high as the prompted writer's copy programs
  (−0.12, −0.43 to +0.18).
- **Designs:** 31 of its 66 passing eval programs are copy designs; they
  score 0.69 against 0.81 for its in-place programs.

Of the four comparisons fixed before the run:

1. **Against the base writer and the control: confirmed.** The editor
   gets further on the trained writer's programs with all three seeds.
2. **Against the prompted writer, planned measure: the prompt does better**
   (−0.19, −0.41 to −0.01), as with seed 42; seed 43 was level.
3. **Against the prompted writer, per sample: not confirmed.** +0.17, with
   an interval that includes 0 (−0.02 to +0.40).
4. **In-place programs against the base writer's: confirmed** (+0.55, +0.18
   to +0.96).

Across the three seeds:

| Comparison | Seed 42 | Seed 43 | Seed 44 |
|---|---|---|---|
| − base, changes before first failure | +0.24 (+0.10 to +0.39), 9 tasks | +0.53 (+0.26 to +0.83), 10 tasks | +0.45 (+0.23 to +0.69), 8 tasks |
| − control, same measure | +0.22 (+0.07 to +0.40) | +0.41 (+0.18 to +0.66) | +0.41 (+0.19 to +0.66) |
| − prompted, same measure | −0.33 (−0.62 to −0.00) | −0.03 (−0.38 to +0.35) | −0.19 (−0.41 to −0.01) |
| − prompted, per sample | +0.09 (−0.02 to +0.22) | +0.23 (+0.05 to +0.43) | +0.17 (−0.02 to +0.40) |
| In-place − base in-place | +0.47 (+0.24 to +0.70) | +0.60 (+0.22 to +0.99) | +0.55 (+0.18 to +0.96) |
| Samples passing, all 10 tasks | 38% | 48% | 41% |

The per-sample and in-place rows were computed after the results for seeds
42 and 43, and fixed before the run for seed 44.

Averaged over the three seeds per task (`scripts/hist2_seed_pool.py`,
computed after all three results), D − prompted is −0.30 (−0.52 to −0.09)
on programs that pass (the 8 tasks where every seed has an edited program)
and +0.16 (+0.01 to +0.34) per sample (all 10 tasks).

## Prompted control

D's training samples were drawn with a worked example of the copy design
in the prompt. So the base writer given the same example at eval time might
do as well without any training. If it does, training adds nothing beyond
the prompt. The prompted control (`configs/rtx5070_hist2_eval_hinted.yaml`,
run 20261119T215045Z-2661e6, no infrastructure errors) is the base writer
with that example, byte for byte, on every eval sample. Everything else is
as above, and it was set up before its trials.

Four eval tasks changed between the runs above and this one. Commit
c066f99 added Usage sections to the docstrings of the reference and bug
files of coin_vaults, grain_silos, rehearsal_setlists and server_racks, as
`tests/test_headers.py` requires. The models never see those files, but a
task's hash covers every file, so the prompted writer was run on those 4
tasks with the files from before c066f99, like the other writers (run
20261120T015906Z-571021, no infrastructure errors). The comparisons use all
10 tasks; seed 42 and the control have no edited program on recipe_binder,
so theirs use 9.

| Task | Initial pass (base → prompted) | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bike_docks | 8/16 → 3/16 | 0.00 → 0.67 | 0% → 33% | 0% → 17% |
| canal_locks | 13/16 → 1/16 | 0.12 → 1.00 | 12% → 50% | 0% → 0% |
| coin_vaults | 11/16 → 1/16 | 0.12 → 0.50 | 12% → 50% | 0% → 0% |
| grain_silos | 10/16 → 3/16 | 0.50 → 1.50 | 50% → 83% | 0% → 33% |
| museum_galleries | 7/16 → 6/16 | 0.29 → 0.50 | 29% → 50% | 0% → 0% |
| recipe_binder | 1/16 → 1/16 | 0.00 → 0.50 | 0% → 50% | 0% → 0% |
| rehearsal_setlists | 5/16 → 1/16 | 0.50 → 1.00 | 50% → 100% | 0% → 0% |
| server_racks | 10/16 → 2/16 | 0.50 → 1.50 | 50% → 50% | 0% → 50% |
| spare_parts | 14/16 → 11/16 | 0.50 → 0.50 | 50% → 38% | 0% → 6% |
| tour_itineraries | 14/16 → 2/16 | 0.25 → 0.75 | 25% → 50% | 0% → 0% |

| Metric | Prompted − base | Seed 42 − prompted | Seed 43 − prompted | Control − prompted |
|---|---|---|---|---|
| Changes done before first failure | +0.56 (+0.37 to +0.75) | −0.33 (−0.62 to −0.00) | −0.03 (−0.38 to +0.35) | −0.55 (−0.76 to −0.36) |
| First change works | +28 pts (+15 to +38) | −15 pts (−28 to −1) | −4 pts (−21 to +15) | −26 pts (−35 to −16) |
| Whole sequence works | +11 pts (+2 to +22) | −6 pts (−18 to +5) | −1 pt (−10 to +8) | −12 pts (−24 to −2) |
| Writer samples passing the initial checks | −39 pts (−54 to −23) | +21 pts (−1 to +40) | +29 pts (+9 to +44) | +32 pts (+19 to +45) |

The base writer completes 0.28 changes before the first failure, the
prompted writer 0.84 (0.88 on the 9 tasks), seed 42 0.55, seed 43 0.81 and
the control 0.33.

- **On the planned measure, the prompt does at least as well as training.**
  Seed 43 matches the prompted writer, and seed 42 falls below it (the
  interval's upper end is at 0). On the first 6 tasks the two seeds
  straddled it (−0.19 and +0.15); the 4 tasks added later favor the prompt.
  The prompted writer has 1 to 3 edited programs on each of them, which
  score 0.50 to 1.50.
- **It does so through the copy design alone, at a cost.** Every one of the
  prompted writer's 31 passing programs is classed as a copy design,
  against 48% of each D seed's. Only 19% of its samples pass the initial
  checks, against 58% for the base writer.
- **Per sample (computed after the results):** the base writer scores 0.17
  changes per sample, the prompted writer 0.14, the control 0.16, seed 42
  0.23 and seed 43 0.37. The prompt's failing samples cancel its gain
  (prompted − base −0.03, 95% −0.08 to +0.02). Seed 43 − prompted is +0.23
  (+0.05 to +0.43), seed 42 − prompted +0.09 (−0.02 to +0.22), control −
  prompted +0.02 (−0.03 to +0.08).
- **D's programs are a different kind (computed after the results).**
  Within tasks and within a design class (`scripts/hist2_design_within.py`,
  paired task bootstrap):
  - D's in-place programs score above the base writer's in-place programs:
    +0.47 (+0.24 to +0.70, 6 tasks) for seed 42 and +0.60 (+0.22 to +0.99,
    9 tasks) for seed 43. The control's do not (−0.01, −0.07 to +0.06).
  - D's in-place programs score as well as the prompted writer's copy
    programs: +0.04 (−0.28 to +0.42) and +0.09 (−0.35 to +0.56).
  - D's copy programs score lower than the prompted writer's: −0.49 (−0.74
    to −0.24) for seed 42 and −0.15 (−0.48 to +0.20) for seed 43.

  On the first 6 tasks, D's in-place programs keep their data in private
  attributes (89% and 79% of the attributes set in `__init__`, against 0%
  for the base writer and 35% for the control). Their getters return a copy
  more often (about 80%, against 46% for the base writer, but 71% for the
  control). These describe the programs; they are not a tested mechanism.

So training does not beat the prompt it was trained from on programs that
pass their tests: seed 43 matches it and seed 42 falls short. The prompt
gets its gain by turning every program into a copy design, and three
quarters of its samples fail. Training gets there without the prompt at
test time. Its samples pass the initial checks more often (+21 and +29
points). Half its passing programs are in-place programs that the editor
changes as easily as the prompted copy programs and more easily than the
base writer's; the correctness-only control doesn't produce these. Per
writer sample, seed 43 does better than the prompted writer, and seed 42's
difference doesn't exclude 0.

## Second training round

`hist2_r2a` is D trained further on the editor's ranking of D's own
plain-prompt samples. The plan and its four comparisons were fixed before
the run (`docs/progress_report.md`, "Second training round").

- **Collection** (`configs/rtx5070_hist_train_round2.yaml`): D seed 42 wrote
  16 samples per train task with the plain prompt, otherwise as in the first
  round. 117 of 256 passed the initial checks and 97 were edited.
- **Pairs:** every unequal pair of mean editing scores
  (`configs/rtx5070_hist2_train_round2_aggregate.yaml`): 171 pairs.
- **Training:** DPO+NLL (NLL weight 1, seed 42), starting from D merged into
  the base weights, so the reference model is D.
- **Dev rule:**
  - At D's setting (lr 3e-5, 3 epochs; `hist2_r2`), 2 dev programs pass
    out of 64 samples. The rule asks for 20, and both programs'
    log-probabilities fall (chosen −0.6, rejected −7.6 nats from D).
  - At setting A (lr 2e-5, 2 epochs; `hist2_r2a`), 10 pass: chosen +3.7
    and rejected −0.4 nats. 6 of these 10 programs are copy designs.
  - Neither is eligible, so by the rule the one with more passing programs
    went to the eval.
- **Eval:** `configs/rtx5070_hist2_eval_hist2_r2a.yaml`, run
  20261123T163249Z-c458bc, 172 editing steps, no infrastructure errors. As
  for the other writers, the 4 eval tasks use their files from before
  c066f99.

| Task | Initial pass (base → second round) | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bike_docks | 8/16 → 3/16 | 0.00 → 1.00 | 0% → 67% | 0% → 17% |
| canal_locks | 13/16 → 7/16 | 0.12 → 0.14 | 12% → 14% | 0% → 0% |
| coin_vaults | 11/16 → 4/16 | 0.12 → 0.38 | 12% → 12% | 0% → 12% |
| grain_silos | 10/16 → 3/16 | 0.50 → 1.00 | 50% → 83% | 0% → 0% |
| museum_galleries | 7/16 → 11/16 | 0.29 → 0.69 | 29% → 31% | 0% → 12% |
| recipe_binder | 1/16 → 0/16 | 0.00 → – | – | – |
| rehearsal_setlists | 5/16 → 9/16 | 0.50 → 1.12 | 50% → 81% | 0% → 0% |
| server_racks | 10/16 → 10/16 | 0.50 → 1.38 | 50% → 81% | 0% → 25% |
| spare_parts | 14/16 → 0/16 | 0.50 → – | – | – |
| tour_itineraries | 14/16 → 9/16 | 0.25 → 1.06 | 25% → 56% | 0% → 19% |

It has no passing sample on recipe_binder and spare_parts, so the
comparisons on programs that pass use the other 8 tasks. On them it
completes 0.85 changes before the first failure. On the same tasks, the
other writers complete:

| Writer | Changes before first failure |
|---|---:|
| Base writer | 0.29 |
| Control | 0.32 |
| Prompted | 0.93 |
| D seed 42 | 0.48 |
| D seed 43 | 0.66 |
| D seed 44 | 0.73 |

| Metric | − base | − control | − prompted | − D seed 42 | − D seed 43 | − D seed 44 |
|---|---|---|---|---|---|---|
| Changes done before first failure | +0.56 (+0.34 to +0.77) | +0.52 (+0.32 to +0.71) | −0.08 (−0.37 to +0.17) | +0.36 (+0.18 to +0.58) | +0.18 (−0.00 to +0.39) | +0.11 (−0.08 to +0.34) |
| First change works | +25 pts (+12 to +41) | +23 pts (+10 to +36) | −5 pts (−22 to +13) | +15 pts (−1 to +34) | +10 pts (−4 to +25) | +7 pts (−6 to +21) |
| Whole sequence works | +11 pts (+5 to +17) | +11 pts (+5 to +17) | −2 pts (−15 to +9) | +8 pts (+3 to +12) | +1 pt (−6 to +8) | +1 pt (−10 to +10) |
| Writer samples passing the initial checks | −17 pts (−35 to +3) | −6 pts (−18 to +6) | +29 pts (+15 to +41) | +0 pts (−10 to +12) | −12 pts (−20 to −3) | −8 pts (−16 to +3) |

- **Per sample (all 10 tasks, a task without an edited program counting
  0):** it scores 0.31. Against the base writer that is +0.13 (−0.05 to
  +0.31), against the control +0.15 (−0.00 to +0.29), against the prompted
  writer +0.17 (−0.02 to +0.36) and against D seed 42 +0.08 (−0.03 to
  +0.19).
- **Pass rate on all 10 tasks:** 56 of 160 samples (35%), against 58% for
  the base writer, 19% for the prompted writer and 38%, 48% and 41% for D's
  seeds.
- **Designs:** 37 of its 56 passing eval programs are in-place (66%; D
  seed 42 52%). They score 1.11 on average and its copy programs 0.38.
  Within tasks (`scripts/hist2_design_within.py`; these three comparisons
  were not among the four fixed for this writer):
  - its in-place programs against the base writer's in-place programs:
    +0.71 (+0.31 to +1.10, 6 tasks; 0.99 against 0.28);
  - its in-place programs against the prompted writer's copy programs:
    +0.09 (−0.42 to +0.48);
  - its copy programs against the prompted writer's: −0.52 (−0.69 to
    −0.34).
- **The pairs did not favor a design.** In the round's train collection,
  D's copy programs scored +0.06 (−0.05 to +0.18) against their task's
  mean and its in-place programs −0.04 (−0.10 to +0.04). So the move to
  in-place programs is not the editor preferring that class; what the
  pairs reinforced is not something our classifier captures.

Of the four comparisons fixed before the run:

1. **Against the prompted writer, planned measure: not beaten** (−0.08,
   −0.37 to +0.17). That is closer than D seeds 42 and 44 (−0.33 and
   −0.19) and about level with seed 43 (−0.03).
2. **Against the prompted writer, per sample: not confirmed.** +0.17, with
   an interval that includes 0 (−0.02 to +0.36).
3. **Against D seed 42, its starting point: confirmed** (+0.36, +0.18 to
   +0.58). But seed 42 is D's weakest seed. Against seeds 43 and 44, the
   intervals reach 0 (+0.18 and +0.11). So one seed of the second round
   cannot separate a second-round gain from D's seed spread. Seeds 43 and
   44 of `hist2_r2a` answer that (next section).
4. **Against the base writer and the control: confirmed.** +0.56 and +0.52,
   the largest gains of any history-suite writer. The whole sequence works
   on 11% of its programs, against 0% for both.

So a second round on D's own samples, with no example in its new pairs,
gets furthest above the base writer and closest to the prompt on programs
that pass. It still does not beat the prompt, and fewer of its samples
pass the initial checks than any D seed's (35% against 38% to 48%).

## Second-round seeds

`hist2_r2a_s43` and `hist2_r2a_s44` are the second-round writer trained
again with seeds 43 and 44: the same 171 pairs, the same start (D seed 42
merged into the base weights) and setting A. Their comparisons were fixed
before the run (`docs/progress_report.md`, "Second-round seeds").

- **Configs:** `configs/rtx5070_hist2_eval_hist2_r2a_s43.yaml` and
  `_s44.yaml`.
- **Runs:**
  - Seed 43: 20261123T223358Z-2b3c12, 164 editing steps.
  - Seed 44: 20261124T015414Z-3498f2, 180 editing steps.
  - Neither had infrastructure errors. As for the other writers, the 4 eval
    tasks use their files from before c066f99.
- **Training** ends like seed 42's:
  - Seed 43: reward accuracy 0.83, chosen +3.3 and rejected −0.2 nats
    from D.
  - Seed 44: reward accuracy 1.0, chosen +5.5 and rejected +0.6 nats.
- **Dev:** 9 and 12 passing programs (seed 42: 10). The setting was not
  chosen again.

Neither new seed has a passing sample on recipe_binder, so their
comparisons use 9 tasks.

| Task | Initial pass, base → seed 43 → seed 44 | Changes done before first failure | Whole sequence works |
|---|---|---|---|
| bike_docks | 8/16 → 2/16 → 4/16 | 0.00 → 0.25 → 0.50 | 0% → 0% → 0% |
| canal_locks | 13/16 → 9/16 → 8/16 | 0.12 → 0.19 → 0.19 | 0% → 0% → 0% |
| coin_vaults | 11/16 → 6/16 → 5/16 | 0.12 → 0.25 → 0.30 | 0% → 0% → 0% |
| grain_silos | 10/16 → 4/16 → 3/16 | 0.50 → 1.88 → 2.17 | 0% → 50% → 50% |
| museum_galleries | 7/16 → 12/16 → 11/16 | 0.29 → 0.75 → 0.62 | 0% → 0% → 12% |
| recipe_binder | 1/16 → 0/16 → 0/16 | 0.00 → – → – | – |
| rehearsal_setlists | 5/16 → 12/16 → 9/16 | 0.50 → 0.88 → 0.94 | 0% → 0% → 0% |
| server_racks | 10/16 → 12/16 → 12/16 | 0.50 → 0.62 → 1.69 | 0% → 6% → 31% |
| spare_parts | 14/16 → 1/16 → 3/16 | 0.50 → 2.00 → 1.50 | 0% → 50% → 33% |
| tour_itineraries | 14/16 → 7/16 → 6/16 | 0.25 → 1.07 → 0.67 | 0% → 21% → 8% |

Per seed (changes done before the first failure unless marked; seed 42 on
8 tasks, seeds 43 and 44 on 9):

| Comparison | Seed 42 | Seed 43 | Seed 44 |
|---|---|---|---|
| − base | +0.56 (+0.34 to +0.77) | +0.57 (+0.25 to +0.93) | +0.64 (+0.34 to +0.99) |
| − control | +0.52 (+0.32 to +0.71) | +0.55 (+0.21 to +0.94) | +0.62 (+0.30 to +0.99) |
| − prompted | −0.08 (−0.37 to +0.17) | −0.00 (−0.42 to +0.47) | +0.07 (−0.24 to +0.40) |
| − D seed 42 | +0.36 (+0.18 to +0.58) | +0.32 (+0.04 to +0.66) | +0.40 (+0.11 to +0.78) |
| − prompted, per sample (10 tasks) | +0.17 (−0.02 to +0.36) | +0.16 (+0.01 to +0.30) | +0.21 (+0.04 to +0.43) |
| − base, per sample | +0.13 (−0.05 to +0.31) | +0.12 (−0.02 to +0.26) | +0.17 (+0.02 to +0.38) |
| − control, per sample | +0.15 (−0.00 to +0.29) | +0.14 (+0.02 to +0.26) | +0.19 (+0.06 to +0.37) |
| In-place − base in-place | +0.71 (+0.31 to +1.10) | +0.54 (+0.17 to +0.96) | +0.71 (+0.39 to +1.07) |
| In-place − prompted copy | +0.09 (−0.42 to +0.48) | −0.03 (−0.50 to +0.49) | +0.12 (−0.22 to +0.46) |
| Changes before first failure | 0.85 | 0.88 | 0.95 |
| Per sample | 0.31 | 0.30 | 0.35 |
| Samples passing, all 10 tasks | 35% | 40% | 38% |
| Passing programs that are in-place | 66% | 52% | 56% |

Over seeds (`scripts/hist2_seed_pool.py`: each group's mean per task over
its three seeds, paired task bootstrap; programs that pass on the 8 tasks
where every writer has an edited program, per sample on all 10):

| Over seeds | Programs that pass | Per sample |
|---|---|---|
| Second round − D (fixed) | +0.20 (+0.01 to +0.43); 0.82 against 0.63 | +0.02 (−0.07 to +0.11); 0.32 against 0.30 |
| Second round − prompted (fixed) | −0.11 (−0.35 to +0.09); 0.82 against 0.93 | +0.18 (+0.02 to +0.35); 0.32 against 0.14 |
| Second round − base | +0.54 (+0.32 to +0.77) | +0.14 (−0.01 to +0.29) |
| Second round − control | +0.50 (+0.28 to +0.74) | +0.16 (+0.04 to +0.28) |
| D − prompted (post hoc) | −0.30 (−0.52 to −0.09) | +0.16 (+0.01 to +0.34) |
| D − base | +0.34 (+0.17 to +0.53) | +0.13 (−0.00 to +0.28) |
| D − control | +0.30 (+0.14 to +0.49) | +0.14 (+0.03 to +0.28) |

Only the two rows marked "fixed" were among the comparisons fixed before
the run. The others were computed with them; the D rows use only results
that were already known.

Of the comparisons fixed before the run:

1. **The second round adds to D on programs that pass, over seeds:** +0.20
   (+0.01 to +0.43), just clear of 0. Per sample it adds nothing (+0.02):
   its programs score higher, but fewer of its samples pass.
2. **Against the prompted writer, over seeds:**
   - On programs that pass, it is level (−0.11, −0.35 to +0.09).
   - Per sample, it is ahead: +0.18 (+0.02 to +0.35).
3. **Per seed:**
   - Seeds 43 and 44 are level with the prompt on programs that pass
     (−0.00 and +0.07).
   - Per sample, both are ahead of it, with intervals that exclude 0
     (+0.16 and +0.21).
   - Both beat D seed 42, the base writer and the control.
4. **Within designs:**
   - The in-place programs of both new seeds score above the base writer's
     in-place programs (+0.54 and +0.71).
   - They score as well as the prompted writer's copy programs.

Seed 42's larger share of in-place programs did not replicate. Seeds 43
and 44 have about half, like D.

So the second round's programs are level with the prompt's on programs
that pass, with three seeds instead of one level and two below. Per writer
sample, the second round beats the prompt in the test fixed beforehand,
because about twice as many of its samples pass (38% against 19%). These
comparisons use the 16-sample prompted control; the next section repeats
them with 32 samples.

## Larger prompted control

The prompted control's score on programs that pass rested on 31 programs,
1 on four tasks and 2 or 3 on four more, while each trained writer has
three seeds. So it was rerun with 32 samples per task. A sample's seed
depends only on its index, so samples 0 to 15 and their trials are the
16-sample run's, and only samples 16 to 31 are new. The comparisons were
fixed before the run (`docs/progress_report.md`, "Larger prompted
control").

- **Config:** `configs/rtx5070_hist2_eval_hinted32.yaml`.
- **Runs:** 20261124T053648Z-c4564b (stopped by a machine restart at about
  22:30 on 11-23) and 20261124T183906Z-2d1feb (resumed from the store), no
  infrastructure errors. As before, the first 8 passing programs per task
  are edited, and the 4 eval tasks use their files from before c066f99.
- **The new samples pass about as often:** 34 of 160 (21%), against 31 of
  160 before. In all, 65 of 320 samples pass (20%), and all 65 passing
  programs are copy designs.

| Task | Initial pass (base → prompted, 32) | Changes done before first failure | First change works | Whole sequence works |
|---|---|---|---|---|
| bike_docks | 8/16 → 10/32 | 0.00 → 1.06 | 0% → 62% | 0% → 19% |
| canal_locks | 13/16 → 1/32 | 0.12 → 1.00 | 12% → 50% | 0% → 0% |
| coin_vaults | 11/16 → 1/32 | 0.12 → 0.50 | 12% → 50% | 0% → 0% |
| grain_silos | 10/16 → 5/32 | 0.50 → 1.30 | 50% → 70% | 0% → 30% |
| museum_galleries | 7/16 → 14/32 | 0.29 → 0.50 | 29% → 50% | 0% → 0% |
| recipe_binder | 1/16 → 3/32 | 0.00 → 0.50 | 0% → 50% | 0% → 0% |
| rehearsal_setlists | 5/16 → 3/32 | 0.50 → 0.83 | 50% → 67% | 0% → 0% |
| server_racks | 10/16 → 4/32 | 0.50 → 1.62 | 50% → 62% | 0% → 50% |
| spare_parts | 14/16 → 20/32 | 0.50 → 0.50 | 50% → 38% | 0% → 6% |
| tour_itineraries | 14/16 → 4/32 | 0.25 → 0.38 | 25% → 25% | 0% → 0% |

Changes before the first failure, 32 samples against 16:
- on all 10 tasks: 0.82 against 0.84;
- on the second round's 8 tasks: 0.90 against 0.93.

Per sample, 0.15 against 0.14. Against the base writer, the 32-sample
control gains +0.54 (+0.31 to +0.78) on programs that pass (16 samples:
+0.56). Per sample it is −0.03 (−0.10 to +0.07).

| Against the prompted control | Programs that pass, 32 samples | 16 samples | Per sample, 32 samples | 16 samples |
|---|---|---|---|---|
| D seed 42 (9 tasks) | −0.30 (−0.66 to +0.07) | −0.33 (−0.62 to −0.00) | +0.08 (−0.06 to +0.22) | +0.09 (−0.02 to +0.22) |
| D seed 43 (10 tasks) | −0.01 (−0.39 to +0.40) | −0.03 (−0.38 to +0.35) | +0.22 (+0.03 to +0.43) | +0.23 (+0.05 to +0.43) |
| D seed 44 (8 tasks) | −0.17 (−0.46 to +0.11) | −0.19 (−0.41 to −0.01) | +0.16 (−0.05 to +0.40) | +0.17 (−0.02 to +0.40) |
| Second round, seed 42 (8 tasks) | −0.05 (−0.35 to +0.24) | −0.08 (−0.37 to +0.17) | +0.16 (−0.03 to +0.35) | +0.17 (−0.02 to +0.36) |
| Second round, seed 43 (9 tasks) | +0.02 (−0.47 to +0.55) | −0.00 (−0.42 to +0.47) | +0.15 (−0.01 to +0.31) | +0.16 (+0.01 to +0.30) |
| Second round, seed 44 (9 tasks) | +0.10 (−0.27 to +0.47) | +0.07 (−0.24 to +0.40) | +0.20 (+0.02 to +0.43) | +0.21 (+0.04 to +0.43) |
| Control (9 tasks) | −0.53 (−0.78 to −0.28) | −0.55 (−0.76 to −0.36) | +0.01 (−0.08 to +0.09) | +0.02 (−0.03 to +0.08) |
| D, over seeds | −0.27 (−0.57 to +0.04) | −0.30 (−0.52 to −0.09) | +0.15 (−0.02 to +0.35) | +0.16 (+0.01 to +0.34) |
| Second round, over seeds | −0.08 (−0.39 to +0.22) | −0.11 (−0.35 to +0.09) | +0.17 (+0.00 to +0.34) | +0.18 (+0.02 to +0.35) |

The larger control moves every estimate by 0.03 or less. Its intervals
are a little wider, because the new programs vary more within tasks (bike_docks
now scores 1.06 on 8 programs instead of 0.67 on 3). So:

- **On programs that pass, nothing changes:**
  - Every second-round seed is level with the prompt.
  - D is below it on average, now with an interval that includes 0.
- **Per sample, the second round's lead is the same size:** +0.17 against
  +0.18. But its interval now starts at 0 (+0.00 to +0.34). It is a
  borderline result, not a clear one.

**Reading the store.** `samples_per_task` is not in the writer key, so
after this run the store holds 32 samples under the prompted writer's key.
Until 11-24, the readers took every stored sample. From then on, `rtx5070_hist2_eval_hinted.yaml`
would have read all 32. They now read only the config's `samples_per_task`
samples (`Store.candidates(limit=...)`), so that config again gives the
16-sample numbers above. The only other configs whose key holds more
samples than they ask for are `evaluation_original.yaml` and
`evaluation_maintainability.yaml` (1 sample each, a protocol that was
not run), so no reported result changes.
