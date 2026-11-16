# Progress report, 2026-11-16

## The project in plain words

This section assumes no knowledge of the project. The rest of the report
gives the details.

### The question

Code is rarely written once and left alone. After a program is written,
people keep asking for changes: a new feature, a new rule, a fix. Some code
is easy to change, because it is organized so that a new feature fits in
one place. Other code is hard to change, because one small request means
touching many places, and something else breaks along the way.

AI models that write code are usually trained only to write code that works
today. Our question: **if an AI that writes code is trained on how easy its
code turned out to be to change later, does it learn to write code that is
easier to change?**

### The two AI models

- **The writer** is the model we try to improve. It is a coding model
  called Qwen2.5-Coder-7B ("7B" means it has 7 billion parameters, the
  numbers it learns). It gets a task description and writes a small Python
  program.
- **The editor** is a larger coding model of the same family
  (Qwen2.5-Coder-14B). It plays a programmer who comes along later. It gets
  the writer's program and a change request, such as "add discount codes",
  and edits the program. The editor is never trained or changed, so it
  treats every writer's code the same way. If it does better on one
  program than another, the difference comes from the code.

Both models run on one home graphics card (an RTX 5070 with 12 GB of
memory). They are stored in a compressed 4-bit form, so that both fit.

### The tasks

We wrote 60 small programming tasks, such as a bank ledger, a parking
garage, a library catalog or a shopping cart. Each task has:

- a description of the first version of the program;
- tests that check the first version works ("initial tests");
- a sequence of later change requests, 2 or 3 of them, each with its own
  tests. Some tests are shown to the editor ("public checks") and the rest
  are hidden, so the editor cannot just aim at the tests.

The tasks are split three ways, like in a school course:

- **36 training tasks** are used to collect training examples.
- **8 development ("dev") tasks** are used to choose training settings,
  like practice exams.
- **16 evaluation ("eval") tasks** are never used for training or for
  choosing settings. They are the final exam: the only fair test of
  whether a writer really got better.

Much of the early work went into making the tasks fair: fixing tests that
were wrong or unclear, so that a program fails only for real reasons.

### How a program is scored

1. The writer writes 16 versions of the program for a task.
2. The versions that pass the initial tests go on, at most 8 per task.
3. The editor applies the change requests one by one. After each change,
   all the tests run: the new feature must work, and nothing that worked
   before may break.
4. The program's score is **how many changes in a row the editor got
   done before the first failure**. On the eval tasks that is 0 to 3.
   This is the main number in this report: a higher number means code
   that was easier to change.

The editor does not give the same answer every time, so each program goes
through 2 different change sequences, 3 times each, and the results are
averaged.

### How the writer is trained

Take two working programs for the same task. If the editor clearly did
better with program A than with program B, that makes a **preference
pair**: A is preferred over B. From the 36 training tasks we collected
229 such pairs, and kept the 160 most reliable ones.

The training method is **DPO** (Direct Preference Optimization). It nudges
the writer to make programs like A more likely and programs like B less
likely. The writer has billions of parameters and the graphics card only
12 GB, so we train a small add-on to the model (a "LoRA adapter"), not the
whole model.

After training, the trained writer is compressed the same way as the
original. We checked that the conversion itself changes nothing, so any
difference in results comes from the training.

### What we compare

Five ways of producing a writer, all scored on the same 16 eval tasks with
the same editor:

1. **The original writer**, unchanged. This is the starting point.
2. **A maintainability prompt:** the original writer, asked in its
   instructions to write clean, maintainable code. This tests whether
   simply asking is enough.
3. **Ours:** the writer trained with DPO on the editing results.
4. **Static ranking:** the same training, except that programs are
   preferred by a standard code-quality formula (the Radon Maintainability
   Index) instead of by how the editor did. This tests whether a simple
   formula works as well as real editing results.
5. **Correctness-only:** the writer trained on its own working programs,
   with no preferences at all. This tests whether any gain comes simply
   from extra training on correct code.

### What we found so far

All five methods are done:

- **None of them makes the code easier to change.** The editor gets 1.43
  (original), 1.43 (maintainability prompt), 1.45 (ours), 1.35 (static
  ranking) and 1.47 (correctness-only) changes done before its first
  failure, out of 3. Those differences are smaller than the random
  variation between runs.
- **Our training does no better than plain training on the same
  programs.** The correctness-only writer saw the same working programs as
  ours, but not which ones were easier to change, and the two behave
  almost identically on every measure. So the editing results in our 160
  pairs had no effect we can detect.
- **Training on the writer's own working programs has a side effect:** it
  writes working programs more often. 64% of our writer's programs and 66%
  of the correctness-only writer's pass the initial tests, against 58% for
  the original, and both differences are too large to be chance. So this
  comes from the extra training on working code, not from our method. The
  static-ranking writer, trained on the formula's preferences, does not
  have it: only 50% of its programs pass.
- **Training too aggressively made the writer repetitive:** it kept
  writing the same few programs. A gentler setting fixed this, and that
  gentler version is the one we evaluated.
- **Comments make no difference.** We reran all five methods with every
  comment removed before the editor sees the code, and the results did not
  change. The writers rarely write comments unless asked for maintainable
  code, and our trained writer did not learn to add hints for the editor.
- **Why nothing shows up: the editor's luck.** The same program, given the
  same changes, often passes one time and fails the next. Within a task,
  95% of the differences in score come from this luck and about 4% from
  the program itself. The writer's programs are small (about 47 lines) and
  almost all built the same way, so there is little for training to find,
  and our 160 pairs mostly taught the writer to repeat them. Training
  tweaks cannot fix this; the tasks need to change (see "Why nothing shows
  up, in plain words").

- **A less random editor does not fix it.** With the editor's randomness
  turned down (temperature 0.2 instead of 0.7), the editor repeats itself
  a little more on the same changes, but which program does better still
  does not carry over to other changes. The program's share falls to 1%.
- **An editor that patches code instead of rewriting it does not fix it
  either.** Our editor model is bad at sending small edits: it finishes
  both changes 25% of the time instead of 53%, and the program's share is
  again 1%.
- **Tasks built for design to matter do not fix it with this editor.** We
  built three tasks with about 90-line programs whose bulk operations can
  either reuse the basic ones or repeat their logic, and changes that cut
  across every operation. The editor managed the main change for nearly
  every program, whichever way it was built, and failed undo for every
  program; the program's share is 0%.
- **A weaker editor does not fix it either.** A 7B editor finishes the
  first change 40% of the time instead of 72%, but which programs it fails
  on still does not carry over from one set of changes to another (program
  share 7%). A 3B editor almost never finishes a change.
- **The editor ignores the program's design unless asked to use it.** We
  wrote two programs by hand for the same spec. One changes its state
  directly. The other records every call in a log and rebuilds its state
  from it, so undo is just dropping the last entry. With the usual
  instructions, the editor wrote undo its own way for both, adding its own
  history next to the log. With one added paragraph asking it to build on
  what the program already has, it used the log: on one task, undo then
  worked 4 times in 6 for the log program and never for the other. This is
  the first case where a program's design decided whether a change worked.
  On the second task the editor broke both programs either way.
- **On the writer's own programs the new instructions help only a little.**
  Which program wins on one set of changes carries over to the other more
  often (75% instead of 59%), but the program's share is 7% and the
  held-out headroom +0.13. The writer's programs for a task all have the
  same design, so there is little for the editor to build on.
- **Programs built in different ways do not fix it either.** We had the
  writer draw its samples with a menu of 8 general design hints (an
  operation log, one method per kind of change, checks written once, a
  class per kind of thing, and so on). The programs did come out
  different, but the editor, with the new instructions, did about as well
  on all of them: the program's share is 2%, and no design did better than
  its task's average by more than chance.
- **How big the editor's edits are is not a usable label.** A program
  whose changes needed few lines or few functions on one set of changes
  needs as many as the others on the other set. Only the length of the
  editor's replies carries over a little, because it sends the whole file
  back, so shorter programs cost fewer words. That rewards short code, not
  better design.
- **An editor that has to work within the program does not fix it
  either.** Instead of the whole program, this editor sees an outline
  (every function's name, parameters and description, with the code
  hidden), asks for the code it needs, and sends back whole functions,
  which are put in place by name. Real maintainers of large codebases work
  like this. On the same 44 design-hinted programs it gets fewer changes
  done (0.94 per sequence instead of 1.23; the whole sequence works 32% of
  the time instead of 51%), and which programs it fails on is again luck:
  the program's share is 0% (0% to 4%), and the best program on one set of
  changes does no better on the other.

### What is running now

A readability control (`configs/rtx5070_pc_obscure.yaml`, about 5 hours).
Every check so far says the editor does about as well on any of the
writer's programs. To find out whether this measure could notice a
hard-to-read program at all, the editor gets the same 51 dev programs as
in the first dev run, made as unreadable as possible without changing what
they do: no comments or docstrings, no blank lines, and private names,
data attributes and local variables renamed to `_x1`, `a1`, `v1` and so on
(`editor.view_transform: obscure`). All 51 still pass their initial tests,
and every trial uses the same random seed as in the first run, so the two
can be compared trial by trial. If the editor does clearly worse, the
measure can see code quality but the writer's programs do not differ
enough in it; if not, no change to the writer can show up in it on these
tasks.

### Words used in the rest of this report

- **Change sequence:** the list of later change requests for a task.
- **Trial:** one run of the editor through one change sequence for one
  program.
- **Pass rate, or initial pass:** the share of the writer's programs that
  pass the initial tests.
- **"First change works", "whole sequence works":** how often the editor
  got the first change done, or all of them.
- **95% interval:** the range the true difference most likely lies in,
  given the random variation. If it includes 0, we cannot say the
  difference is real.
- **Learning rate:** how big each training step is. Too big, and the model
  overdoes it; too small, and it barely learns.
- **dpo2, dpo3:** our two trained writers, trained with a larger and a
  smaller learning rate; dpo3 is the one evaluated.

## Who did what

What has been done on the RTX 5070 machine since 2026-10-21 (Karin): the
tasks, the training data, DPO training, serving the trained writer, and the
first held-out results. It builds on the harness (Noah), the evaluation
tool (Thoomy), and the confidence intervals, static-ranking generator and
first training code (Riya). Pull requests #6 and #7 (2026-11-10) added
tests of the DPO training loop on a tiny CPU model and the code for the
comment ablation (`editor.view_transform: strip_comments`), whose runs on
all five writers followed (2026-11-12 to 11-13). Details and reproduce
commands are in the pages linked from each section; this report collects
them in one place.

## In short

- **The full pipeline runs end to end on one 12 GB GPU:** 60 tasks, writer
  sampling, editing trials, preference pairs, DPO training, a trained writer
  served exactly like the original, and held-out evaluation.
- **All five methods are done on the 16 eval tasks, and none makes the
  code measurably easier to change.** The editor gets through 1.43 of 3
  changes before its first failure with the original writer, 1.43 with the
  maintainability prompt, 1.45 with our DPO writer, 1.35 with the
  static-ranking (Radon) writer and 1.47 with the correctness-only writer.
  Every interval against the original includes 0.
- **Our DPO writer and the correctness-only writer cannot be told apart.**
  Fine-tuning on the same programs without preferences gives the same
  results on every measure (main measure +0.03, interval −0.05 to +0.10).
  The editing outcomes in our 160 pairs add nothing detectable.
- **The one clear effect of training is not the one it aimed for, and it
  is not ours.** Both writers trained on the writer's own passing programs
  pass the initial tests more often: 64% (ours, +2 to +12 points) and 66%
  (correctness-only, +1 to +15) against 58%. The Radon writer passes less
  often (50%).
- **No result depends on comments.** With every comment and docstring
  removed before the editor sees the code, no writer's main measure moves
  by more than 0.02. On the 52 programs that had any, the editor does
  about as well without them (−0.04, interval −0.26 to +0.19).
- **The testbed cannot show an effect yet, because the labels are mostly
  the editor's randomness.** Within a task, 95% of the variance of a
  trial's score on the train tasks is the editor (temperature 0.7), 4% the
  program. The best program on one change sequence is no better than
  average on the other (+0.03), and a pair's winner on one sequence wins
  on the other only 58% of the time. dpo3 ranks pairs it never saw 55%
  correctly (97% on its training pairs). Programs are about 47 lines and
  share one design in 30 of 36 train tasks. An editor at temperature 0.2
  does not help: on the dev tasks the program share is 1% (0% to 16%) and
  the held-out headroom −0.00. Neither does an editor that sends
  SEARCH/REPLACE edits instead of whole files: the 14B editor handles the
  format poorly (whole sequence 25% against 53%, −43 to −13 points), and
  the program share is again 1% (0% to 16%).
  [Diagnostics](../harness/results/diagnostics.md).

## The five methods

| Method | Status | Changes done before first failure (of 3) | First change works | Whole sequence works | Samples passing initial tests |
|---|---|---:|---:|---:|---:|
| Original writer | done | 1.43 | 67% | 26% | 58% |
| Maintainability prompt | done | 1.43 | 70% | 25% | 60% |
| Ours (DPO on editing outcomes, dpo3) | done | 1.45 | 71% | 25% | 64% |
| Static ranking (DPO on Radon MI) | done | 1.35 | 67% | 23% | 50% |
| Correctness-only (fine-tuning on passing programs) | done | 1.47 | 72% | 25% | 66% |

All rows use the same 16 eval tasks, the same frozen editor
(Qwen2.5-Coder-14B), budget and selection. The selection is the writer's
passing programs, at most 8 per task in sample order, each given 2 change
sequences × 3 repetitions. Differences from the original writer, from a
paired bootstrap over the 16 tasks:

| Method | Changes done before first failure | First change works | Whole sequence works | Samples passing initial tests |
|---|---|---|---|---|
| Maintainability prompt | +0.00 (−0.10 to +0.10) | +3 pts (−1 to +8) | −1 pt (−5 to +4) | +2 pts (−3 to +8) |
| Ours (dpo3) | +0.02 (−0.11 to +0.19) | +4 pts (+0 to +9) | −1 pt (−6 to +5) | +6 pts (+2 to +12) |
| Static ranking | −0.08 (−0.23 to +0.08) | +0 pts (−6 to +8) | −3 pts (−8 to +1) | −8 pts (−18 to +1) |
| Correctness-only | +0.05 (−0.09 to +0.22) | +5 pts (+1 to +10) | −1 pt (−7 to +6) | +8 pts (+1 to +15) |

Against ours (dpo3), same measures in the same order:

| Method | Changes done before first failure | First change works | Whole sequence works | Samples passing initial tests |
|---|---|---|---|---|
| Static ranking minus ours | −0.10 (−0.35 to +0.11) | −4 pts (−11 to +3) | −3 pts (−10 to +3) | −14 pts (−24 to −5) |
| Correctness-only minus ours | +0.03 (−0.05 to +0.10) | +1 pt (−2 to +4) | −0 pts (−2 to +2) | +2 pts (−5 to +8) |

Pages: [original writer](../harness/results/base_writer_eval.md),
[maintainability prompt](../harness/results/maintainability_prompt_eval.md),
[ours](../harness/results/dpo3_eval.md),
[static ranking](../harness/results/radon_eval.md),
[correctness-only](../harness/results/sft_eval.md).

## The two trained baselines, in plain words

Both ran on the RTX 5070 machine, one after the other: static ranking from
2026-11-10 05:00 to 2026-11-11 03:54 PST (run 20261110T134603Z-31b2e3),
correctness-only from 2026-11-11 03:55 to 2026-11-12 03:34 PST (run
20261111T122905Z-5cae35). Nothing is running now.

A baseline is a simpler alternative that our method is compared against,
to see whether learning from real editing results is worth its cost. Both
of these were planned in the proposal from the start. They are part of the
five-method comparison, not new attempts after the first results.

**1. Static-ranking baseline (Radon)**

- **The idea:** instead of watching an editor change the code, a fixed
  formula judges which program is "more maintainable". Radon is a standard
  tool that scores code from things like length and complexity.
- **How it was trained:** exactly like dpo3, with the same 28 tasks, the
  same number of pairs (160), the same training settings and the same
  conversion. The only difference is who decided which program in each
  pair was better: the formula instead of the editor. If it does as well
  as dpo3, a cheap formula could replace our expensive editing step.
- **The terms used for it:**
  - `configs/rtx5070_eval_radon.yaml` is the settings file for this run.
  - `20261110T134603Z-31b2e3` is the run's ID: its start time plus a
    random tag. It is how its results are found in the database later.
  - "Loss 0.54 at the last step (dpo3: 0.55)" is a training progress
    number. The two being so close means both trainings went about
    equally far, which keeps the comparison fair.
  - "Passed the same export checks" means it was converted for Ollama the
    same verified way as dpo3, so the conversion did not change anything
    by accident.
- **The result (finished 2026-11-11):** it did no better than the original
  writer. The editor got 1.35 changes done before its first failure,
  against 1.43 (difference −0.08, interval −0.23 to +0.08), and fewer of
  its programs passed the initial tests (50% against 58%). Its programs
  score only slightly higher on the formula itself (43.5 against 42.6 out
  of 100), about as much as just asking for maintainable code. Against
  dpo3 the main measure cannot be told apart either (−0.10, interval −0.35
  to +0.11). Because neither trained writer beat the original, this
  comparison cannot yet say whether real editing results are a better
  training signal than the formula. Its pass rate is 14 points below
  dpo3's, although both were trained on pairs of working programs.
  Together with the correctness-only result below, this suggests the
  formula's preferences work against the pass rate, while training on the
  writer's own working programs lifts it.

**2. Correctness-only baseline**

- **The idea:** no preferences at all. The writer is simply trained on its
  own programs that worked, 201 of them from the same 28 tasks.
- **Why it matters:** dpo3's one clear effect was writing working programs
  more often (64% vs 58%). This baseline tests whether that comes from our
  method or just from extra training on correct code. If this one gets the
  same boost, the boost is not special to our method.
- **The steps:** 16 minutes of training, about 15 minutes converting the
  model ("export", with the same checks as dpo3), then 23 hours on the
  eval tasks.
- **The result (finished 2026-11-12):** it got the same boost. 66% of its
  programs pass the initial tests, against 58% for the original (interval
  +1 to +15 points) and 64% for dpo3. On every measure it is as good as
  dpo3: 1.47 changes done before the first failure against dpo3's 1.45
  (difference +0.03, interval −0.05 to +0.10), and the first change works
  72% of the time against 71%. So the boost is not special to our method,
  and the preferences in our 160 pairs (which program the editor found
  easier to change) made no difference we can measure. Its programs are a
  little less varied: 234 different programs among 256 samples, against
  252 for the original and dpo3.

## The comment test, in plain words

- **The worry:** a writer could "win" without writing better-organized
  code, by leaving comments that tell the editor what to do. The proposal
  plans this check: rerun the evaluation with all comments removed before
  the editor sees the code. If a method's results drop, its advantage came
  from the comments.
- **How it ran:** all five methods, on the same programs, from 2026-11-12
  03:47 to 2026-11-13 07:16 PST (27.5 hours). Most programs have no
  comments at all. The editor sees exactly the same thing for those as in
  the normal run, so their results were reused from the store instead of
  asking the editor again (all 2,904 of these trials came out identical,
  as they should). Only the 52 programs with comments needed new editing.
  That made it about a day instead of five.
- **The result (finished 2026-11-13):** nothing changes.

  | Method | Programs with comments | Changes done before first failure, normal → no comments |
  |---|---:|---:|
  | Original writer | 4 of 110 | 1.43 → 1.41 |
  | Maintainability prompt | 32 of 108 | 1.43 → 1.44 |
  | Ours (dpo3) | 5 of 113 | 1.45 → 1.45 |
  | Static ranking | 8 of 94 | 1.35 → 1.35 |
  | Correctness-only | 3 of 111 | 1.47 → 1.48 |

  Only the maintainability prompt makes the writer comment much (a third
  of its programs), and the editor does just as well without those
  comments. Our writer comments as rarely as the original, so it did not
  learn to leave hints. Page:
  [comment ablation](../harness/results/nocomments_eval.md).

## Why nothing shows up, in plain words

Four checks on the results we already have (2026-11-13), to find out
whether the problem is the test, the training signal or the training:

- **Is there room to improve at all?** For each task, take the program
  that did best on one list of changes and see how it does on the other
  list. On the train tasks it does no better than average (+0.03 changes).
  On the eval tasks it does somewhat better (+0.15 to +0.27), but a writer
  that only leans towards its better programs would gain under 0.1, less
  than this eval can detect.
- **Do winners stay winners?** If program A beats program B on one list of
  changes, does it also beat B on the other? Only 58% of the time, close
  to a coin flip. Even two runs of the same list agree only 60% of the
  time.
- **Did our writer learn anything that carries over?** On pairs it never
  saw, it prefers the winner 55% of the time (63% on eval tasks, 36% on
  dev tasks), against 97% on the pairs it was trained on. It mostly
  memorized its training pairs.
- **What do winners look like?** No code feature (length, number of
  functions, complexity, Radon score, comments, ...) tells winners from
  losers consistently, and our writer's code did not change on any of
  them. The Radon writer's code did change, on exactly the features its
  formula rewards, so training works when the labels are consistent.

**The reason:** the editor is random enough (temperature 0.7) that the
same program, given the same changes, often succeeds once and fails the
next time. 95% of the differences in score within a task come from this,
and 4% from the program. The programs are about 47 lines long, nearly all
built the same way (the task fixes the methods), and the editor rewrites
whole files, so how a program is organized barely matters to it.

**Is it just the editor's temperature?** No. We reran the dev tasks with
the editor at temperature 0.2. It got the same results and repeated
itself a little more on the same changes, but a program that did well on
one set of changes still did no better on the other. Only 1% of the
differences came from the program. Most of the luck stayed.

**Is it because the editor rewrites whole files?** We can't tell yet. We
made the editor send small search-and-replace edits instead, so it has to
work within the existing code. The editor model is bad at this: it sends
too many edits at once, gets cut off, or tries to edit code that isn't
there yet. It finished both changes 25% of the time instead of 53%. Again
only 1% of the differences came from the program, but with this many
format mistakes the run can't tell whether a better patching editor would
help.

**What it means:** more seeds or other training settings cannot help. The
tasks need to make the program matter: bigger programs with room for
different designs, changes that cut across the design, an editor that
works within the existing code (which needs a stronger editor or a
simpler edit format than search-and-replace), and a check with these
diagnostics on a few pilot tasks before more training. Page:
[diagnostics](../harness/results/diagnostics.md).

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

### The two trained baselines (2026-11-10 to 11-12)

Both see the same 28 train tasks and use dpo3's training settings, so only
the training signal differs:

- **Static ranking:** prefers the program with the higher Radon
  Maintainability Index. `scripts/static_ranking.py` gives 271 pairs, and
  `scripts/match_pairs.py` keeps as many per task as ours has (160).
  - 33 of the 160 are pairs of ours with the same winner;
  - 22 are pairs of ours with the opposite winner;
  - 105 are pairs ours does not have.

  Its training fit the formula's preferences more easily than ours fit
  the editing ones: by the second epoch, mean loss 0.55 against 0.61 and
  reward accuracy 99% against 96%.
- **Correctness-only:** supervised fine-tuning
  (`harness/src/harness/train_sft.py`) on the 201 passing programs these
  tasks' pairs were built from (`scripts/sft_programs.py`). It sees the same
  programs as our writer but not which were easier to change. 51 steps in
  16 minutes; the loss per program token fell from 0.051 to 0.019.

### Comment ablation (2026-11-12 to 11-13)

- One config per writer (`configs/rtx5070_eval*_nocomments.yaml`): the
  normal eval config plus `editor.view_transform: strip_comments`, which
  removes every comment and docstring before a sequence's first step.
- Programs with nothing to strip give the editor the same prompt with the
  same seed, so their trials replay from the stored replies. All 2,904 of
  them match the normal run step for step (status and output program;
  `scripts/ablation_compare.py`). The five runs needed 1,980 new editor
  calls, about a tenth of the five normal runs' 20,078.
- One trial hit a Docker error and was retried by rerunning its config.

### Diagnostics (2026-11-13)

- `scripts/diagnostics.py`: headroom (best program by one sequence, scored
  on the other), how often winners agree across sequences and repetitions,
  and a variance decomposition of trial scores (program, program ×
  sequence, trial), also for other measures of the first change.
- `scripts/implicit_reward.py`: DPO's implicit reward of the four adapters
  on the training pairs and on the base writer's dev-task and eval-task
  pairs (forward passes, 2.5 hours on the GPU).
- `scripts/winner_features.py`: 23 static features, their within-task
  correlation with the editing score, a leave-one-task-out pair
  classifier, and how far each trained writer's programs moved on them.
- Fixed: a resample in which no pair was decided on both sides gave an
  undefined share that broke the sort of the bootstrap. Every interval
  in the diagnostics page is unchanged; only the small dev-task runs drew
  such resamples.

### Editor-temperature probe (2026-11-13)

- `configs/rtx5070_pc_editor_t02.yaml`: the 8 dev tasks' programs edited
  again with the editor at temperature 0.2 instead of 0.7. Run
  20261114T014031Z-9433c1: 343 steps, 1,059 editor calls, 0 infrastructure
  errors, about 6.5 hours (paused for 3 hours on request).
- Same results on the changes (−0.03, −0.14 to +0.06). Two repetitions of
  the same sequence pick the same winner more often (68% against 50%), but
  winners on one sequence are a coin flip on the other (49%), the program
  share falls from 4% to 1% (0% to 16%), and the held-out headroom from
  +0.12 to −0.00.

### Patch-editor probe (2026-11-13 to 11-14)

- `editor.edit_format: search_replace` (`models/patch.py`,
  `prompts/editor_patch_v1.md`): the editor sends SEARCH/REPLACE edits of
  the current files instead of whole files. Off by default; the editor key
  of every existing config is unchanged.
- The format went through three versions on one dev task: edits applied
  one by one instead of all or nothing, a message for edits that quote
  code not yet in the file, and a worked example in the prompt.
- `configs/rtx5070_pc_editor_patch.yaml`: the same 51 dev-task programs.
  Run 20261114T075822Z-4da442: 482 steps, 1,889 editor calls, 0
  infrastructure errors, about 10 hours.
- Much worse on the changes: the whole sequence works 25% of the time
  against 53% (−43 to −13 points). Per step, 3.9 editor calls against 2.2,
  out of turns 22% against 10%, and 6% of replies cut off at the length
  limit (none for whole files). Program share 1% (0% to 16%), winners on
  one sequence win on the other 48% of the time, held-out headroom +0.05
  (−0.22 to +0.32).

### Design-sensitive pilot (2026-11-14)

- Three new dev tasks (`tasks/fuel_depot`, `tasks/herd_paddocks`,
  `tasks/sample_freezers`): primitives plus composite operations that move
  everything from one place to another, whose construction the spec leaves
  open, and changes that cut across every operation (a capacity or
  allowed-species rule, a flag that blocks every move, undo).
  `configs/rtx5070_pilot.yaml` and `configs/rtx5070_pilot_maintain.yaml`
  (the plain and the maintainability prompt).
- The first version passed 0 of 96 writer samples because of spec traps
  unrelated to design (re-adding removed ids, the order of `KeyError` and
  `ValueError`, type checks, an inconsistent parameter name, the order of
  moved items). After fixing them, 25 of 96 passed.
- Editing them failed the gate: 5 of 137 steps work, program share 0%,
  held-out headroom +0.00. The failing hidden tests are again edge rules
  (zero-sized moves, error order). Re-graded without those, the capacity
  and allowed-species changes work in about 85% of trials for programs
  built either way, and undo fails for every program.
- `scripts/diagnostics.py` no longer crashes when no task's scores vary.

### Editor-size probe (2026-11-14 to 11-15)

- `configs/rtx5070_pc_editor_7b.yaml` and `configs/rtx5070_pc_editor_3b.yaml`:
  the same 51 dev-task programs edited by Qwen2.5-Coder-7B (run
  20261115T040402Z-94b9a5, 428 steps, about 5 hours) and Qwen2.5-Coder-3B
  (run 20261115T091404Z-24e38f, 316 steps, about 3 hours).
- 7B: first change works 40% (14B: 72%); program share 7% (0% to 19%),
  program × sequence 7%, held-out headroom +0.03 (−0.10 to +0.16).
- 3B: first change works 3%; 284 of 316 steps run out of turns.

### Design probe (2026-11-15)

- `scripts/design_probe.py` takes hand-written programs for a task through
  its change sequences with the editor, in a store of its own. The programs
  and every trial are in `harness/results/design_probe/`: a `state` and a
  `log` program each for sample_freezers and herd_paddocks.
- Prompt v2, both sequences, 6 reps: the `log` program passes undo in 1 of
  6 on each task and the `state` program in 0. Of the editor's 77 undo
  methods for the `log` programs, 35 keep a stack of their own, 42 use the
  log but add inverse operations or copies, and none just drops the last
  entry and rebuilds.
- `prompts/editor_v3.md` (`configs/rtx5070_pilot_editor_v3.yaml`) adds one
  paragraph: build the change on the program's existing design rather than
  next to it, and keep it as small as that design allows. Undo first
  (sequence s2), 6 reps: herd_paddocks `log` 4 of 6, `state` 0 of 6
  (one-sided Fisher p = 0.03); 10 of its 31 undo methods for the `log`
  program are the two-line version. sample_freezers: 0 and 0. The editor
  breaks existing behavior for both programs and runs out of turns.
- `configs/rtx5070_pc_editor_v3.yaml`: prompt v3 on the 51 dev-task
  programs (run 20261115T145931Z-d53335, 516 steps, about 6 hours). First
  change works 69% (v2: 72%); program share 7% (4% to 10%; v2: 4%);
  winner on A also wins on B 75% (64% to 86%; v2: 59%); held-out headroom
  +0.13 (+0.05 to +0.21; v2: +0.12).
- `writer.design_hints` (`config.py`, `collection/collect.py`): sample i is
  sent the writer prompt with hint i mod the number of hints added as a
  "Design" section, while candidates and pairs keep the plain prompt.
  `scripts/hint_summary.py` reports how each hint's programs fare against
  their task's average. `configs/rtx5070_pc_hints.yaml` is the dev probe
  with 8 hints and prompt v3 (run 20261115T211638Z-3f73df, 335 steps, about
  5 hours): 52 of 124 distinct programs pass the initial checks (3 to 8 of
  16 samples per hint, 11 without one), 44 edited. First change works 74%;
  program share 2% (0% to 7%); winner on A also wins on B 53% (36% to 69%);
  held-out headroom +0.02 (−0.16 to +0.16). Against the task mean, the
  best hints are a class per kind of thing (+0.24, +0.00 to +0.69, 3
  programs) and rules as data (+0.09, −0.11 to +0.39).
- `scripts/edit_carryover.py`: whether the lines changed, tokens written
  and existing functions modified by successful steps carry over between
  sequences. On the train tasks the program with the smallest edits on one
  sequence is at −0.005 log lines (−0.025 to +0.015), −0.055 log tokens
  (−0.114 to +0.004) and −0.06 functions (−0.12 to +0.01) on the other;
  the dev configs are alike (`harness/results/diagnostics.md`).
- Programs with a public method that changes data and calls another (what
  breaks a snapshot-per-method undo): 13 of 353 train programs, all
  robot_fleet; none of the dev programs. So a general undo change was not
  built.

### Outline editor (2026-11-15)

- `editor.edit_format: functions` (`models/outline.py`,
  `prompts/editor_outline.md`, `collection/editor.py`): the program is
  shown as an outline with function bodies hidden; `SHOW <names>` opens
  them; complete functions, methods and classes are spliced in by name. A
  def that would replace a hidden one not opened in an earlier turn, or
  whose body is only `...`, is skipped with a message; SHOW lines count
  inside code blocks too. Whole-file and SEARCH/REPLACE keys are unchanged;
  the format adds its own protocol version to the editor key.
- Smoke tests on bank_ledger: without the opened-first rule the editor
  rewrote whole classes from the outline and ran out of turns; with it, 7
  of 8 steps work (2 programs × 2 sequences), at 6.5 calls per step.
- `configs/rtx5070_pc_outline.yaml`: the dev probe on the hints run's
  programs, 10 turns per step (run 20261116T031616Z-73eee1, 440 steps,
  2,650 editor calls, about 10 hours, 0 infrastructure errors). Against
  the whole-file editor on the same programs: 0.94 changes per sequence
  against 1.23 (−0.29, −0.49 to −0.10), whole sequence 32% against 51%;
  program share 0% (0% to 4%), program × sequence 14%, winners agree
  across sequences 49%, held-out headroom −0.01 (−0.14 to +0.10). Fails
  the gate, so `configs/rtx5070_train_outline.yaml` and
  `configs/rtx5070_eval_outline.yaml` (drafted for a rerun) were not run.

### Readability control (2026-11-16)

- `editor.view_transform: obscure` (`collection/view.py`): before a
  sequence's first step, comments, docstrings and blank lines go, and
  private names, data attributes (names only ever set as `self.x = ...`)
  and local variables are renamed to `_x1`, `a1`, `v1`. Public functions,
  classes and methods, parameters, keywords, imports, class attributes and
  attribute names of builtin types stay. Tests: a program behaves the same
  before and after, and every task's reference and planted-bug programs
  keep their public interface.
- `scripts/obscure_check.py`: all 51 of the first dev run's programs pass
  their initial tests once obscured (on average 0.4 private names, 1.7
  data attributes and 0.8 local variables renamed per program).
- `configs/rtx5070_pc_obscure.yaml`: the same programs, editor and seeds as
  `rtx5070_pc.yaml`, with the obscured view (run 20261116T133752Z-e9bd81,
  running).

## Findings so far

1. **No method changes how far the editor gets.** The five methods are
   within 0.12 changes of each other on 16 tasks (1.35 to 1.47), and every
   interval against the original writer includes 0.
2. **DPO on editing outcomes does no better than plain fine-tuning on the
   same programs.** The correctness-only writer and ours cannot be told
   apart on any measure, and their intervals are the narrowest of all
   (main measure +0.03, −0.05 to +0.10). With 160 pairs, which program the
   editor found easier to change adds nothing we can detect.
3. **Both small gains come from one task.** Per task, ours has 6 tasks up
   and 9 down, the correctness-only writer 8 up, 7 down and 1 the same.
   race_telemetry carries both averages (1.20 → 2.23 and 2.17 on 5
   programs); without it, the differences are about −0.05 and −0.01.
4. **Training on the writer's own passing programs makes it pass the
   initial tests more often**: +6 points for ours (+2 to +12) and +8 for
   the correctness-only writer (+1 to +15), which get the same boost
   without any preferences. The Radon writer's pairs also compare passing
   programs, with the same tasks and settings, yet it passes less often
   (−8 points against the original, −14 against ours), so the formula's
   preferences seem to work against the pass rate (one seed each).
5. **Training on the code-quality formula does not help either.** The
   Radon writer gets 1.35 changes against 1.43 (−0.08, −0.23 to +0.08).
   Its programs score only a little higher on Radon's own index (43.5
   against 42.6 out of 100), about as much as the maintainability prompt
   gives (43.6).
6. **No result depends on comments.** With comments and docstrings
   removed before the editor sees the code, no writer's main measure moves
   by more than 0.02. On the 52 programs that had any (32 of them from the
   maintainability prompt), the editor does about as well without them
   (−0.04, −0.26 to +0.19). dpo3 comments as rarely as the original writer
   (5 of 113 programs against 4 of 110), and only 14 of the 256 train
   programs have comments, so comments did not drive our pairs either.
7. **The learning rate matters, and too high a rate narrows the writer.**
   dpo2 lost program variety and collapsed on one task. dpo3 kept the
   variety (252 distinct programs among 256 eval samples, as many as the
   original); the correctness-only writer has a little less (234).
8. **Most editing failures are the editor running out of turns.** That is
   two thirds of the failed steps for dpo3 (337 of 507), mostly while a
   public check it can see still fails. That limits how much a
   better-structured program can show.
9. **The comparison can only see large effects.** With 16 tasks, the 95%
   interval of the main measure spans 0.2 to 0.3 changes, and the training
   signal is 160 pairs from 28 tasks.
10. **The labels are mostly the editor's randomness.** Within a task, the
    editor's randomness is 95% of the variance of a trial's score on the
    train tasks (89% on eval tasks), the program 4% (0% to 8%; eval 11%).
    A program's mean over its 6 trials measures its own part with a
    reliability of 0.18. The best program by one sequence gains +0.03 on
    the other (−0.04 to +0.10), and winners agree across sequences 58% of
    the time (47% to 68%). Turns used, edit size, reply length and the
    share of hidden tests passed are no better (program share 0% to 13%).
11. **There is little difference between programs to find.** The writer's
    programs are about 47 lines and have exactly the same functions and
    classes in 30 of 36 train tasks; the editor rewrites whole files. No
    static feature separates winners from losers (leave-one-task-out
    classifier 54%, 43% to 64%).
12. **dpo3 mostly memorized its pairs.** It ranks its training pairs 97%
    correctly but pairs it never saw 55% (47% to 63%; 63% on eval tasks,
    36% on dev tasks), with a tenth of the reward margin, and its programs
    moved on no feature. The Radon writer's programs did move, on the
    features its formula rewards (Radon MI +0.43 SD), so training follows
    labels that are consistent.
13. **A cooler editor does not make the labels depend on the program.**
    At temperature 0.2 the editor agrees with itself more on the same
    changes, but the program's share of the variance is 1% (0% to 16%)
    on the dev tasks, against 4% at 0.7, and the best program on one
    sequence gains nothing on the other.
14. **The 14B editor cannot patch code reliably.** Sending SEARCH/REPLACE
    edits instead of whole files halves how often it finishes a sequence
    (25% against 53% on the dev tasks): it sends too many edits at once,
    gets cut off, or quotes code that is not in the file yet. The program
    share stays at 1% (0% to 16%). Because the format failures dominate,
    this does not show whether an editor that patches well would make the
    program matter; it does rule out this editor with this format.
15. **Tasks built for design to matter do not make the 14B editor depend
    on the design.** On three pilot tasks with about 90-line programs whose
    bulk operations reuse the basic ones or repeat their logic, the editor
    applies a cross-cutting rule to every operation either way (about 85%
    of trials once edge-case tests are set aside) and fails undo for every
    program. Program share 0%.
16. **A weaker editor fails more, but not on particular programs.** With a
    7B editor the first change works 40% of the time instead of 72%; the
    program share is 7% (0% to 19%), as large a share depends on which
    changes come, and the best program on one sequence gains +0.03 on the
    other. A 3B editor almost never finishes a change.
17. **The editor uses a program's design only when asked to.** With
    hand-written programs for the same spec, the usual prompt makes the
    14B editor write undo its own way whether or not the program keeps a
    log of its operations. A prompt that asks it to build on the existing
    design makes it use the log on herd_paddocks: undo works 4 of 6 times
    for the log program and 0 of 6 for the plain one. It is one task and 12
    trials, and on sample_freezers the editor fails both programs anyway.
    On the writer's own dev programs the same prompt raises the program's
    share only from 4% to 7% (headroom +0.13): those programs all share
    one design.
18. **Programs that differ in design do not make the 14B editor depend on
    the program either.** Writer samples drawn with 8 design hints and
    edited with the same prompt give a program share of 2% (0% to 7%) and
    held-out headroom +0.02; no hint's programs beat their task's average
    with an interval clear of 0.
19. **Edit size is not a label.** The lines changed and the functions
    modified by a successful change do not carry over between sequences
    (train tasks: −0.005 log lines, −0.06 functions for the most economical
    program on the other sequence). The tokens the editor writes carry over
    by about 5%, because it sends whole files back: that rewards short
    programs, not design.
20. **An editor that works within the program's structure does not make
    the program matter.** Shown an outline and made to open code before
    changing it, the 14B editor gets fewer changes done on the same
    design-hinted programs (0.94 per sequence against 1.23) and fails as
    evenly across programs: program share 0% (0% to 4%), held-out headroom
    −0.01.

## Open questions for the team

- **Testbed (the main question):** the diagnostics say the current tasks
  cannot show an effect, because the editor's randomness swamps the
  differences between programs. Do we build a pilot of a few bigger dev
  tasks (a few hundred lines, design left open, changes that cut across
  it), and go ahead only if the diagnostics show a program share well
  above 4% (say 25%) and headroom above 0.3? Or do we write up the current
  results as a well-explained negative result? The editor-temperature
  probe says a setting alone does not help, and the patch-editor probe
  says the 14B editor cannot work with search-and-replace edits, so a
  pilot would need a stronger editor or a coarser edit format (one
  function at a time). The
  wallet pilot in `docs/wallet_pair_pilot/` (two hand-written designs, no
  usable pair) proposes concrete test checks for such a pilot.
- **Seeds and training settings:** the proposal asks for several seeds
  for our writer; only seed 42 is done. More seeds, beta or epochs would
  measure training on labels that are mostly noise, so they should wait
  for the testbed decision.
- **Protocol:** these results use the collection store's protocol: selected
  passing programs, at most 8 per task. `harness/docs/evaluation.md`
  describes a different one (one unselected first attempt per task and
  seed), which has not been run. We should agree which one the final report
  uses.
- **Task list:** items still open in `Task_list.md` include how often old
  behaviour breaks, the cost summary, comment density and the size-matched
  check.
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
| Summaries and comparisons | `scripts/eval_summary.py`, `scripts/eval_compare.py`, `scripts/ablation_compare.py` (comment ablation) |
| Diagnostics | `scripts/diagnostics.py`, `scripts/implicit_reward.py`, `scripts/winner_features.py`; `harness/results/diagnostics.md` (also the editor-temperature, patch-editor, editor-size and design probes and the pilot) |
| Patch editor | `harness/src/harness/models/patch.py`, `harness/prompts/editor_patch_v1.md`, `harness/configs/rtx5070_pc_editor_patch.yaml` |
| Design probe | `scripts/design_probe.py`, `harness/results/design_probe/` (hand-written programs and trials), `harness/prompts/editor_v3.md`, `harness/configs/rtx5070_pilot_editor_v3.yaml`, `harness/configs/rtx5070_pc_editor_v3.yaml` |
| Design hints and edit size | `writer.design_hints`, `harness/configs/rtx5070_pc_hints.yaml`, `scripts/hint_summary.py`, `scripts/edit_carryover.py` |
| Outline editor | `harness/src/harness/models/outline.py`, `harness/prompts/editor_outline.md`, `harness/configs/rtx5070_pc_outline.yaml` (dev probe), `rtx5070_train_outline.yaml`, `rtx5070_eval_outline.yaml` |
| Readability control | `editor.view_transform: obscure` (`harness/src/harness/collection/view.py`), `scripts/obscure_check.py`, `harness/configs/rtx5070_pc_obscure.yaml` |
| Controlled wallet pilot | `docs/wallet_pair_pilot/` |
| Task checklist | `Task_list.md` |
