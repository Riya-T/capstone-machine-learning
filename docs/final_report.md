# Training a Code Writer on Later-Edit Outcomes: A Controlled Study

CMSC673 capstone, final report (draft of 2026-11-17). Results marked
*pending* are still running; the rest are final.

## Abstract

We asked whether a code-writing model trained on how well a fixed editing
model can later change its programs learns to write code that is easier
to change. We built 60 Python task families with initial specifications,
sequences of later change requests and hidden tests, sampled programs
from Qwen2.5-Coder-7B, had a frozen Qwen2.5-Coder-14B editor apply the
changes (2 sequences × 3 repetitions per program), turned the outcomes
into preference pairs and trained the writer with DPO (QLoRA, one 12 GB
GPU). On 16 held-out task families, neither our writer nor any of four
controls (the original writer, a maintainability prompt, DPO on Radon
maintainability rankings, fine-tuning on correct programs only) changes
how many changes the editor completes before its first failure: all
five lie within 0.12 of each other (1.35 to 1.47 of 3), and every
interval against the original writer includes 0. Diagnostics explain
why: within a task, 95% of the variance of a trial's score is the
editor's randomness and 4% the program, so a program's mean over its six
trials has a reliability of 0.18. A label-noise control shows this noise
alone does not rule the method out: Radon scores degraded with
per-program noise of the same reliability still teach DPO the Radon
preference on held-out tasks when every pair is used (81% of held-out
pairs, as with clean labels). The same training on every pair of our
editing labels (634 pairs) carries nothing over (54% of held-out editing
pairs, where a writer that had learned their signal as well would reach
about 65%). On this testbed the editing outcomes contain no preference
that is shared across tasks. We release the pipeline, tasks, every
preference pair, the diagnostics and the controls.

## 1. Introduction

Code that passes today's tests can still be hard to change tomorrow.
Agent-written code is measurably harder for later agents to build on
(CodeThread reports resolve-rate drops of up to 13.1 points; SlopCodeBench
finds structural erosion in 77% of trajectories), and static
maintainability metrics explain these differences only in part. A natural
response is to train the writer on the outcome that matters: how well a
later editor manages to change its code. CodeRhapsody proposes this but
reports no experiment. We implement it under controlled conditions.

Our research question: does training a code writer with preferences from
later-edit outcomes make it produce code that a fixed editor can change
more reliably, compared with training on initial correctness alone or on
a static quality score?

Contributions:

1. A rerunnable pipeline (task registry, sandboxed execution, a turn-based
   editor, a scorer with ties and consistency rules, DPO training and an
   evaluation that serves the trained writer exactly like the original),
   with component tests and CI.
2. 60 reviewed task families (36 train, 8 dev, 16 eval) with change
   sequences of nine kinds, two of which appear only in eval.
3. The controlled comparison of five writers on the 16 eval tasks, with
   paired task-bootstrap intervals and a comment ablation.
4. Diagnostics that measure, before any training, whether a testbed's
   editing outcomes can carry a learnable signal (variance components,
   held-out headroom, cross-sequence stability), and seven probes of
   editor, task and writer variants against them.
5. A label-noise control that separates "the labels are too noisy" from
   "the labels have no shared direction", using a known learnable signal
   (Radon MI) degraded to the editing labels' reliability.

## 2. Related work

MaintainBench and MaintainCoder evaluate and improve generation under
changing requirements through an orchestrated workflow; CodeThread holds
the follow-on task fixed while varying who wrote the base code; SWE-CI
evaluates maintenance over continuous-integration cycles; SlopCodeBench
measures quality decay as agents extend their own code. These establish
that later-modification performance can be measured. ReaL trains for
quality with program-analysis feedback, and Sivapiran and Uddin compare
DPO and BoNBoN alignment for functional and non-functional quality, which
motivates our static-ranking and correctness-only controls. CodeRhapsody
proposes training on maintenance trajectories; our contribution is a
controlled implementation and evaluation of that idea, including what it
takes for such labels to be learnable. References are those of the
proposal (`docs/Project_Proposal_473_v2.docx.pdf`).

## 3. Setup

### 3.1 Tasks

Each task family has an initial specification with public and hidden
initial tests, and two sequences of later change requests, each change
with its own public checks and hidden tests for the new feature and for
earlier behaviour. Change kinds: validation rule, state flag, atomic
operation, undo, derived value, grouping, query, configuration and
concurrency control; the last two occur only in eval sequences. Train and
dev sequences have 2 changes, eval sequences 3. Every task passes
`validate-tasks`: the reference solution passes and planted bugs fail,
for the initial version and after each change. Task design, fixes and
the splits are documented in `harness/tasks/FAMILIES.md`.

### 3.2 Models and serving

- **Writer:** Qwen2.5-Coder-7B-Instruct, the official Q4_K_M GGUF, served
  by Ollama with an 8,192-token context; temperature 0.4 (chosen on dev),
  16 samples per task.
- **Editor:** Qwen2.5-Coder-14B-Instruct, Q4, same server, temperature
  0.7, never trained. A turn loop: per change it sees the whole current
  program, the request, summaries of its latest turns and the output of
  the public checks it last ran, and replies with complete new files and
  either RUN_CHECKS or DONE; at most 8 turns, 32,000 tokens and 600 s per
  change. It never sees hidden tests.
- **Hardware:** one RTX 5070 (12 GB) under WSL2; sandboxed execution in
  Docker (1 CPU, 512 MB, no network, 60 s).
- **Serving a trained writer:** the LoRA adapter is merged into the f16
  weights, converted to GGUF and quantized with the official file's
  per-tensor types. Applied to the untrained model, this route reproduces
  the official GGUF byte for byte, so differences between writers come
  from training, not conversion.

### 3.3 Scoring and preference pairs

A trial is one run of the editor through one change sequence on one
program, from a fresh copy. Its score is the number of consecutive
changes completed before the first failure; a change fails if a hidden
test of the new feature or of earlier behaviour fails or the editor runs
out of budget. Each passing, distinct program (at most 8 per task, in
sample order) gets 2 sequences × 3 repetitions; its score per sequence is
the mean over repetitions.

Two programs of a task form a pair under weak dominance (at least as good
on both sequences, better on one) when the winner is ahead by at least 2
changes in total; ties and inconsistent comparisons give no pair; at most
8 pairs per task, by margin. These settings were frozen on the dev tasks
before collecting training data.

The train collection drew 576 samples on 36 tasks: 177 failed the initial
tests, 46 were duplicates and 97 exceeded the 8-program cap, leaving 256
programs and 2,679 editing steps (72 GPU-hours of editing). They gave 821
comparisons and 229 pairs from 31 tasks (tie rate 0.19). Keeping pairs
whose winner wins in at least 2 of the 3 repetitions (182) and dropping
pairs whose programs differ only in strings, docstrings, local names and
annotations gives the training set: **160 pairs from 28 tasks**.

### 3.4 Training

Our own DPO loop (TRL's trainer exceeded 12 GB because it materializes
full-vocabulary logits): QLoRA with 4-bit NF4 weights, LoRA rank 16
(alpha 32, dropout 0.05) on every linear layer, beta 0.1, 2 epochs, 8
pairs per optimizer step, maximum length 3,200 tokens, seed 42; about 25
minutes and 8.3 GB per run. The learning rate was chosen on the dev tasks
between two runs (dpo2 and dpo3); dpo3 (2e-5) is our writer.

### 3.5 Methods compared

1. **Original writer.**
2. **Maintainability prompt:** the original writer, instructed to write
   clean, maintainable code.
3. **Ours (dpo3):** DPO on the 160 editing-outcome pairs.
4. **Static ranking (Radon):** DPO with dpo3's settings on 160 pairs of
   the same programs ranked by Radon Maintainability Index, matched per
   task to our pairs.
5. **Correctness-only (SFT):** supervised fine-tuning with dpo3's
   settings on the 201 passing programs our pairs were drawn from, without
   preferences.

All five are scored on the 16 eval tasks with the same editor, budget and
selection. Intervals resample the tasks with replacement, keeping each
task's pair of results together (paired task bootstrap, 20,000
resamples).

## 4. Results

### 4.1 Main comparison

| Method | Changes before first failure (of 3) | First change works | Whole sequence works | Samples passing initial tests |
|---|---:|---:|---:|---:|
| Original writer | 1.43 | 67% | 26% | 58% |
| Maintainability prompt | 1.43 | 70% | 25% | 60% |
| Ours (dpo3) | 1.45 | 71% | 25% | 64% |
| Static ranking (Radon) | 1.35 | 67% | 23% | 50% |
| Correctness-only | 1.47 | 72% | 25% | 66% |

Differences from the original writer (95% intervals):

| Method | Changes before first failure | First change works | Whole sequence works | Samples passing initial tests |
|---|---|---|---|---|
| Maintainability prompt | +0.00 (−0.10 to +0.10) | +3 pts (−1 to +8) | −1 pt (−5 to +4) | +2 pts (−3 to +8) |
| Ours (dpo3) | +0.02 (−0.11 to +0.19) | +4 pts (+0 to +9) | −1 pt (−6 to +5) | +6 pts (+2 to +12) |
| Static ranking | −0.08 (−0.23 to +0.08) | +0 pts (−6 to +8) | −3 pts (−8 to +1) | −8 pts (−18 to +1) |
| Correctness-only | +0.05 (−0.09 to +0.22) | +5 pts (+1 to +10) | −1 pt (−7 to +6) | +8 pts (+1 to +15) |

![Each method's difference from the original writer, with 95% intervals](../harness/results/figures/methods.png)

No method changes how far the editor gets. Our writer and the
correctness-only writer cannot be told apart on any measure (main measure
+0.03, −0.05 to +0.10, correctness-only minus ours), so the editing
outcomes in our pairs add nothing detectable to training on the same
programs. The one clear effect of training is on the first version: both
writers trained on the writer's own passing programs pass the initial
tests more often (+6 and +8 points); the Radon writer passes less often
(−8 points). Breaking earlier behaviour is rare for every writer (the
original writer's steps: 944 successes, 331 out of budget, 142 new-feature
failures, 12 earlier-behaviour failures, 5 both); most failures are the
editor running out of turns.

*Pending:* training seeds 2 and 3 of dpo3, correctness-only and Radon
(the proposal's three seeds per trained method; running, all by about Nov
24), and the full eval of dpo_all (§6.3, by Nov 18).

### 4.2 Comments

With every comment and docstring removed before the editor sees the code,
no writer's main measure moves by more than 0.02, and on the 52 programs
that had any, the editor does about as well without them (−0.04, −0.26 to
+0.19). Readability more broadly barely registers (§5.3): renaming
private names, data attributes and locals to meaningless ones and
removing comments and blank lines costs the editor 0.04 changes per
sequence (−0.17 to +0.07). No result depends on comments acting as hints.

## 5. Why nothing shows up

### 5.1 Diagnostics

| Check | Result | Reading |
|---|---|---|
| Held-out headroom: pick each task's best program by one sequence, score it on the other | train +0.03 (−0.04 to +0.10); eval +0.27 (+0.10 to +0.45) | a perfect selector of the writer's own programs gains almost nothing on train tasks |
| Do winners on sequence A win on sequence B? | 58% (47% to 68%) on train; two repetitions of the same sequence agree 60% | close to coin flips |
| Does dpo3's implicit reward rank held-out pairs? | 55% (47% to 63%) on dev and eval pairs; 97% on its training pairs | memorized, not learned |
| What separates winners from losers? | leave-one-task-out classifier 54% (43% to 64%); no feature replicates on eval; dpo3's code moved on no feature | nothing to learn |

Underneath all four: a two-way variance decomposition of one trial's
score within each task (programs and sequences random).

| Programs | Program | Program × sequence | Trial (editor randomness) |
|---|---:|---:|---:|
| Train | 4% (0% to 8%) | 2% | 95% |
| Dev | 4% (0% to 7%) | 0% | 96% |
| Eval | 11% (0% to 26%) | 0% | 89% |

![The variance of one trial's score within a task](../harness/results/figures/variance.png)

A program's mean over its 6 trials therefore measures its own lasting
part with a reliability of 0.18 on train tasks (0.42 on eval tasks). More
trials help slowly: 2 sequences × 10 repetitions give 0.40, 8 sequences ×
3 repetitions 0.47. The writer's passing programs are small (median 47
lines) and share one design in 30 of 36 train tasks, and the editor
rewrites whole files.

We set a gate for any further training: a program share of at least 25%
and held-out headroom above 0.3 on dev tasks.

### 5.2 Probes of the testbed

Each probe changes one part of the testbed and reruns the diagnostics on
the dev tasks (details and reproduce commands in
`harness/results/diagnostics.md`):

| Probe | Result | Program share |
|---|---|---:|
| Editor at temperature 0.2 instead of 0.7 | same results; headroom −0.00 | 1% (0% to 16%) |
| Editor sends SEARCH/REPLACE patches | whole sequence 25% against 53% | 1% (0% to 16%) |
| Tasks built so that design matters (pilot) | reusing and repeating designs fare alike | 0% |
| 7B editor | first change 40% against 72%, failures not tied to programs; headroom +0.03 | 7% (0% to 19%) |
| 3B editor | almost never finishes a change | – |
| Writer samples drawn with 8 design hints | no hint's programs beat their task's average | 2% (0% to 7%) |
| Editor sees an outline and opens code on demand | 0.94 changes per sequence against 1.23 | 0% (0% to 4%) |
| 3B writer | 8% of dev programs pass the initial tests | – |

Hand-written programs show what is missing (design probe): the editor
writes a change its own way whatever the program already offers. Asked to
build on the program's design, it does: a program that logs its
operations then passes undo in 4 of 6 trials, against 0 of 6 for the same
program keeping plain state. But the writer's own programs do not differ
in such ways, and design hints do not make them. Taken one change at a
time, 9 of the 72 first changes on the train tasks have a program share of
25% or more (stock_portfolio's undo: 4 programs always pass, 4 always
fail), but 43 have none, and a task's other change rarely favours the same
programs. A pair's label reflects how one change's edge case met one
program.

### 5.3 Readability

With every dev program obscured (no comments, docstrings or blank lines;
private names, data attributes and locals renamed), the 14B editor gets
1.21 changes per sequence instead of 1.25 (−0.04, −0.17 to +0.07), and its
first change works as often. The 7B editor does not notice either (+0.03,
−0.06 to +0.12). The writers' programs differ in readability far less than
that, so no change in names, comments or layout can show up in this
score.

## 6. Is it the noise, or the signal?

Section 5 shows the labels are noisy. It does not show whether noise
alone defeats the method: a learnable signal under the same noise might
still come through. We test this with a signal we know DPO can learn.

### 6.1 A learnable signal: Radon MI

The Radon writer learns its formula's preference and carries it over: on
114 Radon-ranked pairs of the base writer's eval-task programs, its
implicit reward (log-probability under the adapter minus under the base
model) prefers the higher-MI program 79% of the time (67% to 89%), and its
own eval-task programs score +0.43 base standard deviations higher on MI
(+0.04 to +0.88).

### 6.2 Degrading it

We retrain the Radon writer with dpo3's settings on degraded labels and
score the same held-out pairs:

- **Random swaps** of 15%, 30% and 50% of its 160 pairs. 30% makes two
  labels agree as often as the editing labels agree across sequences
  (0.7² + 0.3² = 0.58).
- **Per-program noise**, which is what the editing labels have: each
  program is ranked by its MI standardized within the task times √R plus
  Gaussian noise times √(1 − R), drawn once per program, so R is the
  reliability. R = 0.18 matches the editing scores. With 160 pairs matched
  per task to dpo3's (two seeds at 0.18), and with every unequal pair at
  0.18 (627 pairs).

![Held-out Radon pairs ranked like MI, by the noise in the training labels](../harness/results/figures/label_noise.png)

Random swaps behave as expected: 75% at 15%, 56% (39% to 73%) at 30%, 40%
at 50%; with 30% swapped the writer's programs no longer move up MI
(+0.06, −0.08 to +0.20). But random swaps contradict each other, so DPO
cannot fit them (final loss 0.67). Per-program noise never contradicts
itself, and that changes the picture. At R = 0.18, 160 pairs are a coin
toss (58% and 71% for two seeds); at 0.47, 74%; at 0.80, 81%. With every
pair at 0.18 the writer carries the preference over as well as with clean
labels, 81% (66% to 92%), although 31% of its pairs prefer the lower-MI
program. Spread over every pair of every program, what the noisy pairs
have in common is the signal. So our labels' noise explains why 160 pairs
could not be relied on; it does not by itself rule the method out.

### 6.3 The editing labels with every pair

We then train the matching writer on the editing labels: one mean
editing score per program and every pair whose scores differ (scorer
rule `aggregate`, no cap), 634 pairs from 36 train tasks, dpo3's settings
(dpo_all). It fits them tightly (final loss 0.33, against 0.59 for the
0.18 Radon writer). On the base writer's held-out editing pairs, paired
the same way:

| Ranker | Eval-task editing pairs (298, 16 tasks) | Dev-task editing pairs (98, 7 tasks) |
|---|---:|---:|
| Chosen program is shorter | 50% (39% to 60%) | 53% (39% to 67%) |
| Base model log-probability | 56% (48% to 64%) | 57% (46% to 68%) |
| dpo3 (160 pairs) | 52% (48% to 57%) | 37% (28% to 47%) |
| **dpo_all (634 pairs)** | **54% (49% to 61%)** | **47% (29% to 66%)** |

Held-out editing labels are noisy too, so even a writer that had learned
their signal could not rank them all correctly. How far it could get
follows from the control: over every pair of the Radon eval programs, the
0.18 Radon writer ranks 71% like MI, and against MI degraded to the eval
editing scores' reliability (0.42) it ranks 65% (58% to 71% over 400
draws of the noise). dpo_all ranks 54%, no better than the base model's
own log-probability.

![Held-out Radon pairs and held-out editing pairs ranked by the Radon and editing writers](../harness/results/figures/heldout.png)

With matched noise and pair count, DPO learns MI's preference and not the
editing labels'. What the editing scores share within a task does not
point the same way across tasks.

*Pending:* dpo_all's full eval collection with the editor (main measure,
by Nov 18), and the 627-pair Radon writer's own eval-task code (whether
it moves up MI like the clean writer's).

## 7. Discussion

**What the result says.** On this testbed, preferences from later-edit
outcomes do not train a writer whose code is easier to change, and the
reason is not a training detail: neither more pairs, nor a different
learning rate, nor removing comments changes it. The editing outcomes of
the writer's own programs are dominated by the editor's randomness, and
what is left is specific to how one change's edge case meets one
program, not a design property that recurs across tasks. Training fits
those labels and learns nothing that transfers.

**What it does not say.** It does not say that maintainability cannot be
learned from downstream outcomes. Three conditions failed here, and each
points to what a testbed would need:

1. **Programs that differ in design.** A 7B writer's passing programs for
   a 50-line task are nearly the same program. Larger tasks with real
   design freedom (a few hundred lines, several interacting components)
   would give the editor something to respond to.
2. **An editor that works within the existing design.** Our editor
   rewrites whole files and solves each change its own way. When told to
   build on the program's design, it does, and design then decides
   outcomes (4 of 6 against 0 of 6 on undo). The 14B model could not use
   patch or outline formats well; a stronger editor might.
3. **Enough reliability per program.** Per-program noise is not fatal
   when every pair is used, but our editing budget gave a reliability of
   0.18; tripling the repetitions would have reached only 0.40 at about
   three times the 72 GPU-hours.

**The diagnostic gate.** The checks in §5.1 cost one dev collection
(about 5 GPU-hours) and predicted every null result that followed. We
recommend running them on any later-outcome testbed before collecting
training data: a program share of at least 25% and held-out headroom
above 0.3.

**Limitations.** One writer, one editor, one hardware budget; small
self-contained tasks; one training seed so far (more running); a
selection of up to 8 passing programs per task rather than a single
unselected attempt; the noise control uses a static signal (MI) whose
learnability may differ from that of a real design signal.

## 8. Conclusion

We implemented training a code writer on later-edit outcomes end to end
and evaluated it against four matched controls on held-out tasks. None of
the five writers changes how far a fixed editor gets. The editing labels
are 95% editor randomness, and a label-noise control with a known
learnable signal shows that noise of this kind and size would not by
itself stop DPO when every pair is used; with every pair, the editing
labels still teach nothing that carries over to new tasks. The bottleneck
is the testbed's signal, not the training method.

## Reproducibility and artifacts

- Code, tasks, configs and the CPU test suite: this repository
  (`harness/`, CI in `.github/workflows/tests.yml`).
- Every preference pair: `harness/data/` (`train-v1`, `pairs-karin-v1`,
  `label-noise-v1`, `editing-all-v1`), with manifests and provenance.
- Results pages: `harness/results/` (one per method, the comment
  ablation, `diagnostics.md` with every probe and control and their
  reproduce commands); figures in `harness/results/figures/`
  (`scripts/report_figures.py`).
- Running log of all experiments, settings and costs:
  `docs/progress_report.md`.
