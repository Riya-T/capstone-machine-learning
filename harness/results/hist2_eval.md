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
