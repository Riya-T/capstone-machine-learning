# Progress report, 2026-11-10

What has been done on the RTX 5070 machine since 2026-10-21 (Karin): the
tasks, the training data, DPO training, serving the trained writer, and the
first held-out results. It builds on the harness (Noah), the evaluation
tool (Thoomy), and the confidence intervals, static-ranking generator and
first training code (Riya). Details and reproduce commands are in the pages
linked from each section; this report collects them in one place.

## In short

- **The full pipeline runs end to end on one 12 GB GPU:** 60 tasks, writer
  sampling, editing trials, preference pairs, DPO training, a trained writer
  served exactly like the original, and held-out evaluation.
- **Three of the five methods are done on the 16 eval tasks, and none makes
  the code measurably easier to change.** The editor gets through 1.43 of 3
  changes before its first failure with the original writer, 1.43 with the
  maintainability prompt and 1.45 with our DPO writer. Every interval
  includes 0.
- **The one clear effect of our training is not the one it aimed for.** The
  DPO writer's programs pass the initial tests more often: 64% against 58%,
  95% interval +2 to +12 points.
- **The other two baselines are running now.** The static-ranking (Radon)
  baseline is on the eval tasks, and the correctness-only baseline is queued
  behind it. Both should be done by Thursday morning (see "Running now").

## The five methods

| Method | Status | Changes done before first failure (of 3) | First change works | Whole sequence works | Samples passing initial tests |
|---|---|---:|---:|---:|---:|
| Original writer | done | 1.43 | 67% | 26% | 58% |
| Maintainability prompt | done | 1.43 | 70% | 25% | 60% |
| Ours (DPO on editing outcomes, dpo3) | done | 1.45 | 71% | 25% | 64% |
| Static ranking (DPO on Radon MI) | eval running | – | – | – | – |
| Correctness-only (fine-tuning on passing programs) | queued | – | – | – | – |

All rows use the same 16 eval tasks, the same frozen editor
(Qwen2.5-Coder-14B), budget and selection. The selection is the writer's
passing programs, at most 8 per task in sample order, each given 2 change
sequences × 3 repetitions. Differences from the original writer, from a
paired bootstrap over the 16 tasks:

| Method | Changes done before first failure | First change works | Whole sequence works | Samples passing initial tests |
|---|---|---|---|---|
| Maintainability prompt | +0.00 (−0.10 to +0.10) | +3 pts (−1 to +8) | −1 pt (−5 to +4) | +2 pts (−3 to +8) |
| Ours (dpo3) | +0.02 (−0.11 to +0.19) | +4 pts (+0 to +9) | −1 pt (−6 to +5) | +6 pts (+2 to +12) |

Pages: [original writer](../harness/results/base_writer_eval.md),
[maintainability prompt](../harness/results/maintainability_prompt_eval.md),
[ours](../harness/results/dpo3_eval.md).

## Running now

As of 2026-11-10 05:50 PST, on the RTX 5070 machine. Each step runs only if
the one before succeeded, and a run that stops resumes from the store.

1. **Static-ranking baseline, eval tasks** (`configs/rtx5070_eval_radon.yaml`,
   run 20261110T134603Z-31b2e3, started 05:46 PST). Its training is done:
   160 Radon-ranked pairs matched to ours, dpo3's settings, loss 0.54 at
   the last step (dpo3: 0.55). It passed the same export checks as ours. Expected to
   finish around Wednesday 2026-11-11 in the morning.
2. **Correctness-only baseline** (`configs/rtx5070_eval_sft.yaml`), queued
   to start when the Radon run finishes: about 15 minutes of training,
   20 minutes of export, then about a day on the eval tasks. Expected
   around Thursday 2026-11-12 in the morning. Its trainer is new and passes
   its tests, but has not run on the GPU yet (the GPU is busy). If it fails
   at startup, the run stops and gets fixed.

Results pages for both will be added to `harness/results/` as they finish.

## What was done

### Tasks (2026-10-21 to 2026-11-05)

- Added the 60 task families: 8 dev (2 new plus the 6 that existed), 36
  train and 16 eval. `harness/tasks/FAMILIES.md` documents each family and
  every change below.
- **Writer check:** a task is usable only if enough of the writer's samples
  pass its initial tests, and many first failed it. Two kinds of fix, applied
  the same way everywhere:
  - Input checks the writer skips anyway were made unspecified (True as a
    number, non-string names other than `""` and `None`, which error comes
    first). Their hidden tests went with them.
  - Behaviour the writer kept getting wrong was stated more plainly, with
    examples.
- **Redesigns:** some tasks were redesigned to fit what the writer does
  anyway: robot_fleet, hangman_games, ticket_desk, iou_tracker and
  pantry_inventory (three times each for the last two), 8 of the eval
  tasks, and library_catalog. All 60 tasks now pass the writer check.
- **Change tests:** these were brought in line with the same rules. Then
  the checks were rerun on the final program of every failed editing step.
  Where nearly every failure missed a rule that the change request states
  but no public check covered, a small public check was added (15 in eval
  tasks, 11 in train tasks, and some in dev tasks). Each new check passes
  every step that succeeded before. Changes that are only hard were left
  alone.

### Settings (2026-10-26 to 2026-11-01)

All are listed under "Changes from the proposal" in the README. The main
ones:

- **Hardware:** everything runs on an RTX 5070 (12 GB), not the RTX 5090.
  The writer (Qwen2.5-Coder-7B) and the editor (Qwen2.5-Coder-14B) are both
  4-bit in Ollama, with an 8192-token context.
- **Programs edited per task:** 16 writer samples per task, of which the
  first 8 distinct passing programs are edited. With 8 samples, too few
  programs passed to reach 100–300 pairs.
- **Pairing:** `all_pairs`, at most 8 pairs per task. A pair needs the
  chosen program to complete at least 2 more changes than the rejected one,
  summed over sequences and repetitions (`min_step_gap: 2`).
- **Scoring:** a program scores changes completed in a row, with no partial
  credit, and the editor gets 8 turns. Writer temperature is 0.4.
- **Dev calibration:** 53 pairs from 130 comparisons, a tie rate of 0.23,
  repetition agreement of 0.84 and 47 seconds per editing step.
- **Infrastructure:** program files are now flushed to disk before they are
  recorded, after two WSL crashes left empty files. The README explains how
  to run under WSL on Windows without those crashes.

### Training data (train collection)

- 36 train tasks × 16 samples = 576 writer programs. 256 were edited, 177
  failed the initial tests, 46 were duplicates and 97 were over the
  8-program cap.
- 2,679 editing steps gave 821 comparisons and 229 pairs from 31 tasks (tie
  rate 0.19, repetition agreement 0.84).
- Filtering (`scripts/filter_pairs.py`) gives the training file:
  - pairs whose chosen program wins in at least 2 of the 3 repetitions:
    182;
  - minus cosmetic pairs, whose two programs are the same code apart from
    strings, docstrings, local names and annotations: **160 pairs from 28
    tasks**.

### DPO training (2026-11-08)

- `harness/src/harness/train_dpo.py` now runs its own DPO loop. TRL's
  trainer ran out of memory at 12 GB, because it computes the whole
  vocabulary's scores at every position.
- Setup: QLoRA (4-bit NF4), LoRA rank 16 on every linear layer, beta 0.1,
  2 epochs, 8 pairs per step. A run takes about 25 minutes and peaks at
  8.3 GB.

### Serving the trained writer exactly like the original (2026-11-08)

Ollama cannot load LoRA adapters, and the original writer is the official
Q4_K_M file. So the adapter is merged into the weights
(`scripts/merge_lora.py`) and converted with llama.cpp:

- conversion goes through f16 (the official file was made from f16);
- quantization reuses the official file's per-tensor types
  (`scripts/gguf_quant_types.py`);
- metadata the official file does not have is dropped.

**Check:** the untrained model sent through this route reproduces the
official file byte for byte. A trained writer's 143 tensors that LoRA does
not touch are identical to the official ones, and all 196 trained ones
differ. So any difference in results comes from training, not from
conversion. README, "Serving the trained writer".

### Choosing the training settings on the dev tasks (2026-11-08 to 11-09)

Only the learning rate was varied; the eval tasks were not touched.

| | Original | dpo2 (lr 5e-5) | dpo3 (lr 2e-5) |
|---|---:|---:|---:|
| Changes done before first failure (of 2) | 1.25 | 1.21 | 1.29 |
| First change works | 72% | 70% | 74% |
| Whole sequence works | 53% | 52% | 55% |
| Distinct programs among 128 samples | 113 | 101 | 114 |

- **lr 5e-6:** barely trained. The loss stayed at 0.68 after 2 epochs.
- **dpo2, lr 5e-5:** over-optimized. Training loss fell to 0.21, and the
  writer repeated itself: course_enrollment's 15 passing samples were only
  4 different programs, and library_catalog passed 1 of 16.
- **dpo3, lr 2e-5:** kept the original's variety and was slightly ahead
  (+0.04, interval −0.07 to +0.14), so it went to the eval tasks.

Pages: [dpo2](../harness/results/dpo2_dev.md),
[dpo3](../harness/results/dpo3_dev.md),
[original](../harness/results/base_writer_dev.md).

### The two remaining baselines (2026-11-10)

Both see the same 28 train tasks and use dpo3's training settings, so only
the training signal differs:

- **Static ranking:** prefers the program with the higher Radon
  Maintainability Index. `scripts/static_ranking.py` gives 271 pairs, and
  `scripts/match_pairs.py` keeps as many per task as ours has (160).
  - 33 of the 160 are pairs of ours with the same winner;
  - 22 are pairs of ours with the opposite winner;
  - 105 are pairs ours does not have.
- **Correctness-only:** supervised fine-tuning
  (`harness/src/harness/train_sft.py`) on the 201 passing programs these
  tasks' pairs were built from (`scripts/sft_programs.py`). It sees the same
  programs as our writer but not which were easier to change.

## Findings so far

1. **No method changes how far the editor gets.** The three finished
   methods are within 0.02 changes of each other on 16 tasks, and every
   interval includes 0.
2. **Our writer's small gain comes from one task.** Per task, 6 tasks go up
   and 9 go down. race_telemetry carries the average (1.20 → 2.23 on 5
   programs); without it, the difference is about −0.05.
3. **Our training makes the writer pass the initial tests more often** (+6
   points), although every pair compares two passing programs. The
   correctness-only baseline tests whether plain fine-tuning on passing
   programs does the same.
4. **The learning rate matters, and too high a rate narrows the writer.**
   dpo2 lost program variety and collapsed on one task. dpo3 kept the
   variety.
5. **Most editing failures are the editor running out of turns.** That is
   two thirds of the failed steps for dpo3 (337 of 507), mostly while a
   public check it can see still fails. That limits how much a
   better-structured program can show.
6. **The comparison can only see large effects.** With 16 tasks, the 95%
   interval of the main measure spans 0.2 to 0.3 changes, and the training
   signal is 160 pairs from 28 tasks.

## Open questions for the team

- **Seeds:** the proposal asks for several random seeds for our writer.
  Only one (seed 42) is done, and each costs about a day of evaluation.
- **Stronger signal:** should we strengthen the training signal before
  spending GPU days on seeds? Options: more pairs (more samples or train
  tasks), different beta or epochs (chosen on dev tasks), or longer change
  sequences.
- **Protocol:** these results use the collection store's protocol: selected
  passing programs, at most 8 per task. `harness/docs/evaluation.md`
  describes a different one (one unselected first attempt per task and
  seed), which has not been run. We should agree which one the final report
  uses.
- **Task list:** items still open in `Task_list.md` include the training
  tests (the loss, trained tokens, frozen weights), how often old behaviour
  breaks, and the cost summary.
- **Hard tasks:** library_catalog stays a hard dev task (6 of 16 samples
  pass), and job_board and clinic_appointments got worse with each
  redesign, so they were restored. Keep them, or drop them?
- **Windows Update:** a WSL update restarted WSL in the middle of the dpo3
  eval run. The run resumed from the store, but long runs on Windows can
  be interrupted this way.

## Where things are

| What | Where |
|---|---|
| Results pages | `harness/results/` |
| Task documentation and every task fix | `harness/tasks/FAMILIES.md` |
| Decisions that differ from the proposal | README, "Changes from the proposal" |
| Training, export and baselines | README, "DPO training", "Serving the trained writer", "Static-ranking baseline", "Correctness-only baseline" |
| Configs | `harness/configs/rtx5070_*.yaml` (`_pc` dev, `_train`, `_eval`, and one per writer) |
| Summaries and comparisons | `scripts/eval_summary.py`, `scripts/eval_compare.py` |
| Task checklist | `Task_list.md` |
