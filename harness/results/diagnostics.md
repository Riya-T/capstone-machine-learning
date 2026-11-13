# Diagnostics: why no method shows an effect

None of the five methods changes how far the editor gets
(`harness/results/sft_eval.md`). These checks use only stored results (and,
for check 3, forward passes of the trained writers) to find out whether the
eval could show an effect at all, whether our labels carry a signal, and
whether dpo3 learned one. Run 2026-11-13 at the commit that adds this page.

Scores are changes done before the first failure, per change sequence (the
main measure is their mean over a task's two sequences). Every task has 2
sequences × 3 repetitions per program (3 changes per sequence on train and
eval tasks, 2 on dev tasks). Intervals resample the tasks (paired task
bootstrap, 20,000 resamples, seed 20261105).

## Summary

| Check | Result | Threshold | Verdict |
|---|---|---|---|
| 1. Headroom: pick each task's best program by one sequence, score it on the other | Train +0.03 (−0.04 to +0.10); eval +0.27 (+0.10 to +0.45) for the base writer, +0.15 (+0.02 to +0.28) pooled over the five writers; the top half instead of the best: +0.03 train, +0.06 to +0.08 eval | about 0.15 | Fails on train, borderline on eval |
| 2. Do winners stay winners on the other sequence? | 58% (47% to 68%) on train tasks; two repetitions of the same sequence agree only 60% | about 50% means noise | Close to noise |
| 3. Does dpo3's implicit reward rank held-out pairs? | 55% (47% to 63%) on dev and eval pairs pooled: 63% on eval-task pairs, 36% on dev-task pairs; 97% on its own training pairs | about 50% means nothing carried over | Weak; mostly memorized |
| 4. What separates winners from losers? | A leave-one-task-out classifier gets 54% (43% to 64%); no feature replicates on eval tasks; dpo3 moved on no feature | – | Nothing to learn, nothing learned |

The reason underneath all four (below): within a task, **95% of the
variance of one trial's score is the editor's randomness.** Only 4% (0% to
8%) belongs to the program on train tasks, 11% (0% to 26%) on eval tasks.
The writer's programs are small (median 47 lines) and nearly identical in
design (the same functions and classes in 30 of 36 train tasks), and the
editor rewrites whole files.

## 1. Headroom

Per task, the program that did best on one sequence (mean over its 3
repetitions) is scored on the other sequence and compared with the task's
average there, both ways round. Ties are broken at random. This is the most
any writer could gain on held-out changes by favouring its better samples.

| Programs | Best program on the other sequence | Top half on the other sequence | Best on both sequences (in-sample) |
|---|---:|---:|---:|
| Train, base writer (36 tasks, 256 programs) | +0.03 (−0.04 to +0.10) | +0.03 (−0.00 to +0.07) | +0.30 (+0.25 to +0.35) |
| Dev, base writer (8 tasks, 51 programs) | +0.12 (+0.01 to +0.27) | +0.03 (−0.01 to +0.08) | +0.31 (+0.17 to +0.46) |
| Eval, base writer (16 tasks, 110 programs) | +0.27 (+0.10 to +0.45) | +0.06 (−0.05 to +0.17) | +0.64 (+0.53 to +0.75) |
| Eval, five writers pooled (16 tasks, 536 programs) | +0.15 (+0.02 to +0.28) | +0.08 (+0.01 to +0.15) | +0.75 (+0.67 to +0.83) |

On the train tasks, where our labels come from, the best program on one
sequence is no better than average on the other. The in-sample gain (+0.30)
is mostly luck that does not carry to new changes. The eval tasks leave
more room, mostly in 4 tasks (race_telemetry +1.13, time_clock +0.81,
rover_fleet +0.64, light_grid +0.52 for the base writer). A writer that
shifts towards its better half of programs, which is about what training
on preferences can do, would gain at most 0.06 to 0.08 there. That is
below what 16 tasks can detect (the main measure's interval spans 0.2 to
0.3 changes).

## 2. Do winners stay winners?

For every pair of programs of a task: does the one that wins on sequence A
also win on sequence B? Pairs where either side ties are left out.

| Decision compared | Train (36 tasks) | Eval, base writer | Eval, pooled |
|---|---:|---:|---:|
| One repetition vs another, same sequence | 60% (50% to 70%) | 60% (50% to 71%) | 58% (54% to 63%) |
| One repetition of A vs one of B | 55% (48% to 62%) | 59% (51% to 71%) | 54% (51% to 59%) |
| Winner on A (3 reps) vs winner on B | 58% (47% to 68%) | 57% (46% to 71%) | 54% (50% to 60%) |
| Same, A won by at least 2 changes | 64% (44% to 81%) | 51% (36% to 70%) | 55% (50% to 62%) |
| Spearman correlation of A and B means, within task | +0.06 | +0.21 | +0.15 |

A single trial is barely better than a coin flip even against a repeat of
itself (60%). Half the time sequence B does not separate the two programs
at all (239 of 476 train pairs that A decides tie on B). In the 160
training pairs, the chosen program wins on both sequences in 86 (54%) and
wins on one and ties on the other in 74 (46%). The rule never keeps a pair
that loses on a sequence, but many of its pairs rest on one sequence.

## 3. Did dpo3 learn a preference that carries over?

DPO's implicit reward, log p_adapter(program) − log p_base(program), for
the chosen and rejected program of pairs the adapter never saw: the base
writer's dev-task pairs and its eval-task pairs, built by the same scorer.
The training pairs are shown as a check. `scripts/implicit_reward.py`,
`runs/rtx5070_pc/dpo/implicit_reward.jsonl`.

Share of pairs whose chosen program gets the higher score (95% interval);
"mean margin" is the implicit reward margin with beta 0.1, as in training:

| Pairs | Chosen is shorter | Base model log-probability | dpo3 | dpo2 | Correctness-only | Radon |
|---|---:|---:|---:|---:|---:|---:|
| Training pairs (160, 28 tasks) | 51% | 54% | 97% (93 to 99), margin +0.220 | 98% (96 to 100), +1.341 | 44% (31 to 57), −0.019 | 60% (49 to 70), +0.068 |
| Dev-task pairs (47, 7 tasks) | 53% | 55% | 36% (20 to 52), −0.023 | 51% (33 to 69), −0.056 | 53% (28 to 74), +0.009 | 32% (11 to 54), −0.040 |
| Eval-task pairs (119, 16 tasks) | 46% | 58% | 63% (56 to 70), +0.020 | 63% (54 to 72), +0.071 | 54% (41 to 67), +0.013 | 50% (38 to 62), +0.006 |
| Dev and eval pooled (166, 23 tasks) | | | 55% (47 to 63) | 60% (51 to 68) | 54% (42 to 65) | 45% (33 to 55) |

dpo3 fits its training pairs (97%) but its reward on pairs it never saw is
a tenth as large (mean margin +0.020 against +0.220) and ranks them only a
little better than chance. On the eval-task pairs it is right in 12 of 16
tasks (2 at half, 2 below), and dpo2, trained on the same pairs with a
higher learning rate, agrees with it on 133 of the 166 held-out pairs; on
the dev-task pairs it is wrong more often than right. The correctness-only
writer, trained on the same programs without preferences, is at chance
throughout. So DPO did pick up a weak preference that partly carries over,
but it is mostly memorization of 160 noisy pairs, and the margin is too
small to change what the writer generates (check 4). With labels this
noisy (check 2) even a perfect ranker of the programs' real quality could
not score much above 60% here.

## 4. What separates winners from losers?

`scripts/winner_features.py` measures 23 static features of each program
(size, functions and classes, function length, nesting, Radon MI and
cyclomatic complexity, comments, docstrings, validation code, exception
classes, constants, comprehensions, annotations, duplicated lines).

- **Within-task correlation with the editing score** (train programs, 36
  tasks): the strongest are comprehensions (+0.23, +0.06 to +0.37) and if
  statements (−0.17, −0.33 to −0.02); everything else is within ±0.13 or
  varies in only a few tasks (6 features never vary among a task's
  programs). On the eval tasks (all five writers' programs) neither
  replicates (−0.05 and +0.05); there the strongest that varies in more
  than 3 tasks is nesting depth (+0.16, +0.05 to +0.27), which went the
  other way on train tasks (−0.11). Most features change sign between the
  train and eval tasks, and none has a clear correlation on both.
- **Pair classifier:** a logistic regression on the 160 training pairs'
  feature differences, leaving one task out at a time, picks the chosen
  program 54% of the time (43% to 64%): chance.
- **Did dpo3's programs move?** Against the base writer's passing programs
  on the eval tasks, no feature moved by more than 0.18 standard
  deviations, every interval includes 0, and the classifier's score moved
  −0.19 (−0.56 to +0.22), not towards the training winners. The
  correctness-only writer moved little too: only its largest cyclomatic
  complexity rose clearly (+0.27 SD, +0.02 to +0.53), and its classifier
  score moved −0.38 (−0.95 to +0.21). The Radon writer did move, and on
  its own features: Radon MI +0.43 SD (+0.04 to +0.86), mean function
  length −0.32 (−0.59 to −0.08), cyclomatic complexity −0.31, isinstance
  calls −0.38, more helper functions. So the training pipeline can move a
  writer when its labels are consistent; the editing labels give it nothing
  consistent to follow.

## Why: the editor's randomness swamps the program

A two-way variance decomposition of one trial's score within each task
(program, program × sequence, trial; pooled over tasks, programs and
sequences random):

| Programs | Program | Program × sequence | Trial (editor randomness) |
|---|---:|---:|---:|
| Train, base writer | 4% (0% to 8%) | 2% | 95% |
| Dev, base writer | 4% (0% to 7%) | 0% | 96% |
| Eval, base writer | 11% (0% to 26%) | 0% | 89% |
| Eval, five writers pooled | 7% (1% to 15%) | 3% | 90% |

So a program's mean over its 6 trials measures its own lasting part with
a reliability of only 0.18 on train tasks (0.42 on eval tasks). More trials
help slowly because the program part is small: 2 sequences × 10 reps give
0.40, 8 sequences × 3 reps 0.47. The editor runs at temperature 0.7.

No other measure of the first change does better (train tasks; eval in
brackets): whether it works, 2% program share (4%); editor calls, 5% (9%);
reply tokens, 8% (13%); lines changed, 0% (8%); share of hidden tests
passed, 5% (3%).

The programs leave little room to differ:

- they are small: median 47 lines of code on train tasks (quartiles 43 and
  52, largest 74), 49.5 on eval tasks;
- they share one design: in 30 of 36 train tasks and 15 of 16 eval tasks
  every program has exactly the same functions and classes (the spec fixes
  the public methods, and the writer rarely adds helpers);
- the editor sends complete new file contents (`prompts/editor_v2.md`), so
  it can rework whatever structure a 50-line program has.

The two writers trained on deliberately different code support this: the
Radon writer's programs differ in exactly the features one would expect to
matter (shorter, simpler functions, more helpers), and the editor does no
better on them (−0.08, −0.23 to +0.08).

## What this means for the next step

Tuning DPO (beta, epochs, seeds) cannot help while the labels are mostly
editor luck: with 160 such pairs, DPO memorizes them (check 3). An effect
needs a testbed where the program matters more:

1. **Programs big enough for design to matter.** Tasks whose solutions run
   to a few hundred lines with several interacting parts, specs that fix
   only the public interface, and change sequences that cut across the
   design (a rule used in several places, a new kind of entity, a new
   output format).
2. **An editor that edits rather than rewrites:** search-and-replace
   patches instead of whole files, so it has to work within the existing
   structure.
3. **Less editor luck per label:** a cooler editor and more, shorter
   change sequences per task rather than more repetitions. The probe
   below tests the temperature.
4. **Check before training.** Run `scripts/diagnostics.py` on a pilot of
   a few dev tasks first, and train only once the program share is well
   above today's 4% (say 25% or more) and the held-out headroom above
   0.3.

Running now: the editor-temperature probe, the dev tasks re-edited with the
editor at 0.2 instead of 0.7 (`configs/rtx5070_pc_editor_t02.yaml`).

## Reproduce

From `harness/`, inside WSL:

```bash
uv run python scripts/diagnostics.py --config configs/rtx5070_train.yaml --measures \
    --pairs runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl
uv run python scripts/diagnostics.py --config configs/rtx5070_pc.yaml --measures
uv run python scripts/diagnostics.py --config configs/rtx5070_eval.yaml --measures
uv run python scripts/diagnostics.py --config configs/rtx5070_eval.yaml \
    --config configs/rtx5070_eval_maintain.yaml --config configs/rtx5070_eval_dpo3.yaml \
    --config configs/rtx5070_eval_radon.yaml --config configs/rtx5070_eval_sft.yaml
uv run python scripts/winner_features.py --config configs/rtx5070_train.yaml \
    --pairs runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl --base configs/rtx5070_eval.yaml \
    --writer configs/rtx5070_eval_dpo3.yaml --writer configs/rtx5070_eval_sft.yaml \
    --writer configs/rtx5070_eval_radon.yaml
uv run python scripts/winner_features.py --config configs/rtx5070_eval.yaml \
    --config configs/rtx5070_eval_maintain.yaml --config configs/rtx5070_eval_dpo3.yaml \
    --config configs/rtx5070_eval_radon.yaml --config configs/rtx5070_eval_sft.yaml
.venv/bin/python scripts/implicit_reward.py --model /home/pc/models/hf/Qwen2.5-Coder-7B-Instruct \
    --adapter dpo3=/home/pc/models/dpo/dpo3 --adapter sft=/home/pc/models/dpo/sft \
    --adapter radon=/home/pc/models/dpo/radon --adapter dpo2=/home/pc/models/dpo/dpo2 \
    --pairs runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl \
    --config configs/rtx5070_pc.yaml --config configs/rtx5070_eval.yaml \
    --out runs/rtx5070_pc/dpo/implicit_reward.jsonl
```

`scripts/implicit_reward.py` needs the training extras and the GPU (about
2.5 hours for 4 adapters on 313 pairs).
