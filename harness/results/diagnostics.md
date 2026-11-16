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
bootstrap, 20,000 resamples, seed 20261105); resamples in which a share
is undefined (no pair decided on both sides) are left out.

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
editor rewrites whole files. A cooler editor does not fix it: at
temperature 0.2 instead of 0.7 the program's share on the dev tasks is 1%
(0% to 16%) and the held-out headroom is gone (probe below). Nor does an
editor that patches the code instead of rewriting it: the 14B editor
handles SEARCH/REPLACE edits poorly (the whole sequence works 25% of the
time instead of 53%), and the program's share is again 1% (0% to 16%).
Nor do tasks built for design to matter (pilot below): the 14B editor
handles programs that reuse their primitives and programs that repeat
their logic alike, and the program's share is 0%. Nor does a weaker
editor: a 7B one fails more often (the first change works 40% of the time
instead of 72%) but not on particular programs (program share 7%, 0% to
19%; held-out headroom +0.03), and a 3B one almost never finishes a change.
Hand-written programs show why (design probe below). The editor writes a
change its own way, whatever the program already offers. Asked to build on
the program's design instead, it does: a program that keeps a log of its
operations then passes undo in 4 of 6 trials, against 0 of 6 for the same
program keeping plain state. But programs that differ in design are not
enough: writer samples drawn with 8 design hints, edited with that prompt,
give a program share of 2% (0% to 7%) and no held-out headroom, and no
hint's programs beat their task's average. Nor is edit size a label: how
many lines or functions a successful change touches does not carry over
between sequences. Nor does an editor that sees only an outline and has
to open the code it needs, so that it works within the program: on the
same design-hinted programs it gets fewer changes done (0.94 per sequence
against 1.23), and the program's share is 0% (0% to 4%), with no held-out
headroom. And the measure barely notices how readable a program is at all
(readability control below): with every program obscured (no comments,
docstrings or blank lines; private names, data attributes and locals
renamed to `_x1`, `a1`, `v1`), the editor gets 1.21 changes done per
sequence instead of 1.25 (−0.04, −0.17 to +0.07), and its first change
works as often as before. A writer's programs differ in readability far
less than that, so no change to the writer in names, comments or layout
can show up in this score. Nor is a weaker writer an option: a 3B writer
passes the initial tests with 8% of its dev programs, so almost no task
has two programs to compare (writer-size probe below). The same control
with the 7B editor is running.

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

## Editor-temperature probe

The base writer's dev-task programs (8 tasks, 51 programs) edited again
with the editor at temperature 0.2 instead of 0.7, everything else the
same (`configs/rtx5070_pc_editor_t02.yaml`, run 20261114T014031Z-9433c1:
343 steps, 1,059 editor calls, 0 infrastructure errors, about 6.5 hours).

| Dev tasks, base writer | Editor at 0.7 | Editor at 0.2 |
|---|---:|---:|
| Changes done before the first failure (of 2) | 1.25 | 1.22 (−0.03, −0.14 to +0.06) |
| Whole sequence works | 53% | 52% (−1 point, −10 to +6) |
| All 3 repetitions of a sequence get the same score | 55% of 102 | 59% of 102 |
| Two repetitions of the same sequence pick the same winner | 50% (42% to 63%) | 68% (65% to 76%) |
| Winner on one repetition of A also wins on one of B | 55% (51% to 60%) | 49% (29% to 73%) |
| Winner on A (3 repetitions) also wins on B | 59% (48% to 71%) | 49% (21% to 84%) |
| Variance share: program | 4% (0% to 7%) | 1% (0% to 16%) |
| Variance share: program × sequence | 0% | 9% |
| Variance share: trial | 96% | 89% |
| Held-out headroom (best program on the other sequence) | +0.12 (+0.01 to +0.27) | −0.00 (−0.23 to +0.19) |

The cooler editor does no better or worse on the changes. It repeats
itself a little more: two repetitions of the same sequence agree on the
winner 68% of the time instead of 50%. But what it repeats is particular
to that sequence and does not carry over to the other one. The program's
share falls to 1%, winners on one sequence are a coin flip on the other,
and the held-out headroom disappears. Most of the trial-to-trial
variation is still there (89%; all three repetitions agree in 59% of
cells against 55%), so it does not come mainly from the sampling
temperature. With 8 tasks the intervals are wide, but no measure points
towards a cooler editor making the labels depend on the program.

## Patch-editor probe

The same 51 dev-task programs edited again by an editor that sends
SEARCH/REPLACE edits of the current files instead of whole files
(`editor.edit_format: search_replace`, `configs/rtx5070_pc_editor_patch.yaml`,
editor temperature 0.7 as in the base run; run 20261114T075822Z-4da442:
482 steps, 1,889 editor calls, 0 infrastructure errors, about 10 hours).
The idea was that an editor which must work within the existing code
would make the program's structure matter more.

| Dev tasks, base writer | Whole files | SEARCH/REPLACE edits |
|---|---:|---:|
| Changes done before the first failure (of 2) | 1.25 | 0.81 (−0.44, −0.67 to −0.20) |
| First change works | 72% | 56% (−16 points, −26 to −5) |
| Whole sequence works | 53% | 25% (−28 points, −43 to −13) |
| All 3 repetitions of a sequence get the same score | 55% of 102 | 44% of 102 |
| Two repetitions of the same sequence pick the same winner | 50% (42% to 63%) | 63% (54% to 80%) |
| Winner on one repetition of A also wins on one of B | 55% (51% to 60%) | 53% (37% to 73%) |
| Winner on A (3 repetitions) also wins on B | 59% (48% to 71%) | 48% (24% to 69%) |
| Variance share: program | 4% (0% to 7%) | 1% (0% to 16%) |
| Variance share: program × sequence | 0% | 8% |
| Variance share: trial | 96% | 91% |
| Held-out headroom (best program on the other sequence) | +0.12 (+0.01 to +0.27) | +0.05 (−0.22 to +0.32) |

Steps of the same 306 trials (a step is one change; a trial stops at its
first failure):

| Per step | Whole files | SEARCH/REPLACE edits |
|---|---:|---:|
| Change works | 75% | 53% |
| Ran out of turns (8) | 10% | 22% |
| Public checks pass, hidden checks fail | 14% | 23% |
| Editor calls | 2.2 | 3.9 |
| Tokens written by the editor | 1,756 | 3,377 |
| Replies cut off at the 3,072-token limit | 0% | 6% |

The 14B editor handles the format poorly. Its median reply holds two
edits, but 12% hold ten or more, and a reply cut off at the length limit held 18
edits on median. In the trials replayed by hand, edits also quoted new
methods as if they were already in the file, or applied only in part and
left code that no longer ran. Each problem costs a turn, so steps take
nearly twice as many calls and run out of turns twice as often. Even its
replies are not shorter (median 672 tokens against 748 for whole files).
The prompt and the parser went through three versions on one task
(partial application, a message for quoted new code, a worked example)
before this run; none closed the gap.

The labels depend on the program no more than before: a 1% program share,
winners on one sequence a coin flip on the other, and no reliable held-out
headroom. Because format failures dominate, this does not settle whether
an editor that patches well would make structure matter. It does settle
that this editor, given this format, does not.

## Design-sensitive pilot

Three new dev tasks built for design to matter
(`tasks/fuel_depot`, `tasks/herd_paddocks`, `tasks/sample_freezers`;
`configs/rtx5070_pilot.yaml` and `configs/rtx5070_pilot_maintain.yaml`,
runs 20261115T000113Z-81cad4 and 20261115T015243Z-ae4b13, about 4 hours).
Each has primitives and composite operations that move everything from one
place to another (whose construction the spec leaves open: they may reuse
the primitives or repeat their logic), and changes that cut across every
operation: a capacity or allowed-species rule on every inbound move, a flag
that blocks every move, and undo. The public checks of a change cover one
or two operations; the hidden tests cover all of them. The programs are
about twice the size of the old ones (77 to 95 lines).

The first version's spec traps (re-adding a removed id, the order of
`KeyError` and `ValueError`, type checks, a parameter named differently
from the same role elsewhere, the order of moved items) let 0 of 96
programs pass. After fixing them, 25 of 96 passed, both writer prompts
pooled (1 + 2, 2 + 4 and 11 + 5 of 16 per task).

Editing them (at most 8 per task and pool, 22 programs) failed the gate
completely:

| Per step (both pools) | Count |
|---|---:|
| Change works | 5 of 137 |
| Public checks pass, hidden checks fail | 90 |
| Ran out of turns (8) | 42 |

The program's share of the variance is 0% in both pools and the held-out
headroom is +0.00. The hidden tests that fail are again rules at the edges
of a change, not the parts that depend on the design. Two examples:

- "moving zero samples never raises Full" (26 of 31 graded capacity edits);
- "not enough animals is reported before not allowed" (14 of 18).

Re-grading every first step without the tests on zero-sized moves, error
order, logs and capacity resets settles it:

- The capacity and allowed-species changes then work in about 85% of trials,
  for programs that reuse the primitives and programs that repeat their
  logic alike.
- Undo fails in every trial of every program: one undo after a composite
  call must take back the whole call, and a removed place must come back in
  its old position.

The editor finds and changes every composite whatever the design, and fails
on what it misreads. A 14B editor that sends whole files on 100-line
programs is still too strong for these designs to matter.

## Editor-size probe

The same 51 dev-task programs edited by smaller editors, everything else as
in the base run (`configs/rtx5070_pc_editor_7b.yaml`, Qwen2.5-Coder-7B,
run 20261115T040402Z-94b9a5: 428 steps, 1,738 editor calls, about 5 hours;
`configs/rtx5070_pc_editor_3b.yaml`, Qwen2.5-Coder-3B, run
20261115T091404Z-24e38f: 316 steps, 2,403 calls, about 3 hours; 0
infrastructure errors in either). On these small programs the 14B editor
seemed too strong for the design to matter, so a weaker one might leave
more of the result to the program.

| Dev tasks, base writer | 14B editor | 7B editor | 3B editor |
|---|---:|---:|---:|
| First change works | 72% | 40% | 3% |
| Variance share: program | 4% (0% to 7%) | 7% (0% to 19%) | 0% |
| Variance share: program × sequence | 0% | 7% | 0% |
| Variance share: trial | 96% | 86% | 100% |
| Winner on A (3 repetitions) also wins on B | 59% (48% to 71%) | 51% (9% to 79%) | – |
| Held-out headroom (best program on the other sequence) | +0.12 (+0.01 to +0.27) | +0.03 (−0.10 to +0.16) | +0.00 |

A weaker editor fails more, but no more on some programs than on others.
The 7B editor's failures follow the program slightly more (7%), but as
much of that depends on which changes come (program × sequence 7%), and
the best program on one sequence gains nothing on the other. The 3B editor
almost never finishes a change (284 of its 316 steps run out of turns),
so nothing is left to compare. Of the other measures, only the 7B editor's lines changed
reaches 12%.

## Design probe

Why does the design not matter? Two hand-written programs per pilot task,
both passing the initial checks, with no writer involved
(`scripts/design_probe.py`; the programs and every trial are in
`results/design_probe/`):

- `state` keeps the current contents: the reference solution.
- `log` records every successful call as an operation in `self._ops`, and
  the contents are what replaying them gives (`_record`, `_rebuild`,
  `_apply`). Undo is then two lines: drop the last operation and rebuild.
  That one undo takes back a whole composite call, and a removed place
  comes back in its old position, which are the two things the pilot's
  undo edits got wrong.

Each program ran 6 times through each sequence with the 14B editor at the
pilot settings, in a store of its own.

| Undo, the first change of sequence s2 (6 reps) | `state` works | `log` works |
|---|---:|---:|
| sample_freezers, editor prompt v2 (the one used so far) | 0 | 1 |
| herd_paddocks, editor prompt v2 | 0 | 1 |
| sample_freezers, editor prompt v3 | 0 | 0 |
| herd_paddocks, editor prompt v3 | 0 | 4 |

With sequence s1, whose first change is the capacity or allowed-species
rule, the two designs do alike (0 and 0 of 6 on sample_freezers, 1 and 0 on
herd_paddocks).

With the usual prompt the editor does not look for what the program offers.
It writes undo the way it always does. Of its 77 undo methods for the `log`
programs:

- 35 keep a stack of their own next to `_ops`;
- the other 42 use `_ops` but still add inverse operations or deep copies of
  the state;
- none simply drops the last operation and rebuilds.

Prompt v3 (`prompts/editor_v3.md`) is v2 plus one paragraph: build the
change on what the program already has (its helper methods, its data
structures, the way it keeps its state) rather than adding a parallel
mechanism, and keep the change as small as that design allows. On
herd_paddocks it changes the outcome:

- 10 of its 31 undo methods for the `log` program are the two-line version,
  and none keeps its own stack.
- 4 of 6 reps pass undo, and 2 of those also pass the allowed-species
  change that follows.
- The `state` program passes undo in 0 of 6 (one-sided Fisher p = 0.03).

On sample_freezers prompt v3 changes nothing. The editor rewrites the
program, breaks behavior that was already there (the order of moved
samples) whatever the design, and runs out of turns in 11 of 12 trials.

This is the first setting where a program's design decides whether a change
works. It takes an editor that is asked to use the design.

On the writer's own dev programs, prompt v3 changes little
(`configs/rtx5070_pc_editor_v3.yaml`, run 20261115T145931Z-d53335: the same
51 programs, 516 steps, about 6 hours, 0 infrastructure errors):

| Dev tasks, base writer, 14B editor | Prompt v2 | Prompt v3 |
|---|---:|---:|
| First change works | 72% | 69% |
| Variance share: program | 4% (0% to 7%) | 7% (4% to 10%) |
| Winner on A (3 repetitions) also wins on B | 59% (48% to 71%) | 75% (64% to 86%) |
| Held-out headroom (best program on the other sequence) | +0.12 (+0.01 to +0.27) | +0.13 (+0.05 to +0.21) |

Winners carry over between sequences more often, but the program's share
is still far from the 25% the next step needs. The writer's programs for a
task share one design, so there is little in them for the editor to build
on.

So the next probe gave the editor programs that differ in design. The
writer drew its 16 samples per task with a menu of 8 generic design hints
(`writer.design_hints`; sample i gets hint i mod 8, samples 0 and 8 none):
an operation log replayed into the state, one private method per kind of
change, each check in its own method, a class per kind of thing, one plain
structure replaced only on success, rules as data tables, and the most
direct code. None names a task or a later change. Candidates and pairs keep
the plain prompt, so a writer trained on them would learn the preferred
designs without hints. The editor used prompt v3
(`configs/rtx5070_pc_hints.yaml`, run 20261115T211638Z-3f73df: 128
samples, 52 of 124 distinct programs pass the initial checks, 44 edited,
335 steps, about 5 hours, 0 infrastructure errors).

| Dev tasks, 14B editor, prompt v3 | Writer's own designs | Design-hinted samples |
|---|---:|---:|
| First change works | 69% | 74% |
| Variance share: program | 7% (4% to 10%) | 2% (0% to 7%) |
| Winner on A (3 repetitions) also wins on B | 75% (64% to 86%) | 53% (36% to 69%) |
| Held-out headroom (best program on the other sequence) | +0.13 (+0.05 to +0.21) | +0.02 (−0.16 to +0.16) |

The designs differ, and the editor still does about as well on all of
them. Against their task's mean score, no hint's programs do better with an
interval clear of 0: the closest are a class per kind of thing (+0.24,
+0.00 to +0.69, only 3 programs) and rules as data (+0.09, −0.11 to
+0.39); the programs drawn without a hint are at −0.02
(`scripts/hint_summary.py`). Hinted prompts also pass the initial checks
less often (3 to 8 of 16 samples per hint, against 11 without one).

## Edit size does not carry over either

With design-hinted programs, the lines changed by the first change reach a
17% program share and the tokens the editor writes 13% (prompt v3 run
above, `--measures`). Those measures include failed changes, though, and a
share says nothing about whether a program's edits stay small on new
changes. `scripts/edit_carryover.py` takes each successful step's lines
changed, tokens written and existing functions modified, relative to the
other programs' trials of the same step, and asks whether the program with
the smallest edits on one sequence also has them on the other:

| Programs | Lines changed (log) | Tokens written (log) | Functions modified |
|---|---:|---:|---:|
| Train, base writer (30 tasks) | −0.005 (−0.025 to +0.015) | −0.055 (−0.114 to +0.004) | −0.06 (−0.12 to +0.01) |
| Dev, base writer, prompt v2 (7 tasks) | −0.008 (−0.041 to +0.028) | −0.087 (−0.153 to −0.026) | +0.04 (−0.04 to +0.12) |
| Dev, base writer, prompt v3 | −0.016 (−0.059 to +0.029) | −0.032 (−0.123 to +0.053) | +0.05 (−0.06 to +0.16) |
| Dev, design-hinted samples, prompt v3 | +0.014 (−0.028 to +0.045) | −0.051 (−0.156 to +0.041) | +0.07 (−0.10 to +0.31) |

A successful change touches 2.2 (train) to 2.7 (dev) existing functions,
and the most local program on one sequence is no more local on the other.
The lines changed do not carry over at all (×0.98 to ×1.01). Only the
tokens written do, by about 5%, and those follow the program's length,
because the editor sends whole files back: concision, not design.

The program does decide some single changes: on stock_portfolio's undo
change, 4 of 8 programs fail in all 3 repetitions and the other 4 pass in
all 3. The losers miss one or two of its 11 hidden tests every time, an
edge of that change rather than their design, and which programs a change
favours differs from change to change, which is why nothing carries over
between sequences.

## What this means for the next step

Tuning DPO (beta, epochs, seeds) cannot help while the labels are mostly
editor luck: with 160 such pairs, DPO memorizes them (check 3). An effect
needs a testbed where the program matters more:

1. **Programs big enough for design to matter.** Tasks whose solutions run
   to a few hundred lines with several interacting parts, specs that fix
   only the public interface, and change sequences that cut across the
   design (a rule used in several places, a new kind of entity, a new
   output format).
2. **An editor that edits rather than rewrites,** so it has to work within
   the existing structure. The frozen 14B editor cannot do this with
   search-and-replace edits (probe above: the whole sequence works 25% of
   the time instead of 53%), so it needs a stronger editor or a coarser
   format, such as replacing one function or method at a time.
3. **Less editor luck per label:** more, shorter change sequences per
   task rather than more repetitions. A cooler editor alone does not help
   (probe above).
4. **Check before training.** Run `scripts/diagnostics.py` on a pilot of
   a few dev tasks first, and train only once the program share is well
   above today's 4% (say 25% or more) and the held-out headroom above
   0.3.

A separate controlled pilot (`docs/wallet_pair_pilot/`: two hand-written
wallet designs, two change requests, a Qwen3-8B editor) found no pair
whose winner led on both requests, and proposes concrete checks for the
next testbed: failure rules stated in each change, a public example per
change, and private tests certified against a reference and a broken
implementation before scoring.

Two shortcuts were ruled out before spending GPU time on them:

- **A general undo change** ("take back the last successful call, all of
  it"), the one change where a design decided the outcome in the design
  probe. The editor writes undo as a snapshot at the start of each public
  method, which only breaks when one public method that changes data calls
  another. Writer programs almost never do (13 of 353 train programs, all
  robot_fleet; none of the 61 base or 52 design-hinted dev programs), so
  undo would not separate them.
- **A cap on how many functions an edit may touch.** Locality does not
  carry over (table above), so a cap would fail programs alike.

## Outline-editor probe

Point 2 above, built on the existing tasks. With `editor.edit_format:
functions` (`models/outline.py`, `prompts/editor_outline.md`) the editor
sees each file as an outline: imports, constants and class attributes in
full, every function and method as its signature and docstring with the
body hidden. A `SHOW Ledger.withdraw` line opens a body; the editor sends
complete functions, methods and classes, which are spliced in by name. A
sent def that would replace a hidden one the editor never opened, or whose
body is only the outline's `...`, is skipped and the editor is told why.
The first smoke test showed why that rule is needed: without it the editor
rewrote whole classes from the outline, guessing every hidden body.

Large codebases, where maintainability counts, are read selectively; a
50-line program in a prompt is not. Here the editor has to find its way by
the program's names, docstrings and decomposition and change it within its
structure, so those can matter.

On one dev task (bank_ledger, 2 programs, both sequences, 1 repetition) 7
of 8 steps work, about as often as with whole files, at about 6.5 editor
calls per step instead of 2.4: opening code takes turns, and the first
reply usually adds new methods and tries to rewrite unopened ones.

The dev probe (`configs/rtx5070_pc_outline.yaml`, run
20261116T031616Z-73eee1: the 44 design-hinted programs above, the 8 dev
tasks, 2 sequences × 3 repetitions, 10 turns per step; 440 steps, 2,650
editor calls, about 10 hours, 0 infrastructure errors) fails the gate:

| Dev tasks, design-hinted samples, 14B editor | Whole files (prompt v3) | Outline |
|---|---:|---:|
| Changes done per sequence | 1.23 | 0.94 (−0.29, −0.49 to −0.10) |
| Whole sequence works | 51% | 32% (−19 points, −31 to −6) |
| Steps that ran out of turns | 59 of 459 | 72 of 440 |
| Variance share: program | 2% (0% to 7%) | 0% (0% to 4%) |
| Variance share: program × sequence | 0% | 14% |
| Winner on A (3 repetitions) also wins on B | 53% (36% to 69%) | 49% (40% to 56%) |
| Held-out headroom (best program on the other sequence) | +0.02 (−0.16 to +0.16) | −0.01 (−0.14 to +0.10) |

The first two rows are `scripts/eval_compare.py` over all trials, paired
by task; the rest are `scripts/diagnostics.py`.

The editor manages fewer changes when it has to find its way through an
outline, and it fails as evenly across programs as before. What a program
gains or loses depends on which changes come (program × sequence 14%), not
on the program. The hints look as they did with whole files: a class per
kind of thing is again the best (+0.26 against its task's mean, +0.00 to
+0.73, 3 programs; +0.24 with whole files), and one plain structure and
checks in their own methods are slightly below their tasks' means (−0.11
and −0.10, intervals clear of 0), but with 2 to 11 programs per hint and
no program share overall, none of this is a label
(`scripts/hint_summary.py`). The lines changed by the first change reach a
22% program share, as with whole files (17%), but on successful steps
they do not carry over between sequences (−0.013 log units, −0.062 to
+0.031; `scripts/edit_carryover.py`, 6 tasks).

So an editor that works within the program's structure does not make the
program matter on these tasks either.

## Readability control

Every probe so far finds the editor doing about as well on any of the
writer's programs. This control asks whether the measure could notice a
hard-to-read program at all. With `editor.view_transform: obscure`
(`collection/view.py`) the editor sees each program with its comments,
docstrings and blank lines removed, private names renamed to `_x1`, `_x2`
and so on, data attributes (`self.accounts = …`) to `a1`, `a2` and local
variables to `v1`, `v2`, printed back with `ast.unparse`. The program does
the same thing: all 51 of the base writer's dev programs pass their
initial tests once obscured (`scripts/obscure_check.py`), and no change
test reads a data attribute (the dev tests read only `.value`). On average
this removes 7% of the bytes and renames 0.4 private names, 1.7 data
attributes and 0.8 local variables per program. The editor's seeds depend
only on the task, program, sequence and repetition, so every trial is
paired with the same trial of the base run (`configs/rtx5070_pc_obscure.yaml`,
run 20261116T133752Z-e9bd81: 306 trials, 536 steps, 1,134 editor calls,
6 hours 20 minutes, 0 infrastructure errors).

| Dev tasks, base writer, 14B editor | Readable | Obscured |
|---|---:|---:|
| Changes done before the first failure (of 2) | 1.25 | 1.21 (−0.04, −0.17 to +0.07) |
| First change works | 72% | 73% (+1 point, −7 to +9) |
| Whole sequence works | 53% | 47% (−6 points, −11 to −2) |
| Variance share: program | 4% (0% to 7%) | 0% (0% to 5%) |
| Winner on A (3 repetitions) also wins on B | 59% (48% to 71%) | 50% (32% to 61%) |
| Held-out headroom (best program on the other sequence) | +0.12 (+0.01 to +0.27) | +0.05 (−0.01 to +0.14) |

The first three rows are `scripts/eval_compare.py` (and
`scripts/ablation_compare.py`, trial by trial: the same −0.04); the rest
are `scripts/diagnostics.py`.

Making every program much harder to read costs the editor almost nothing.
The first change works as often as before; only the second fails a little
more often, mostly on bank_ledger (the whole sequence works 73% of the
time instead of 94%; 1.50 changes instead of 1.90) and parking_garage
(0.38 instead of 0.62), while library_catalog gains (1.61 instead of
1.39). The interval rules out a cost above 0.17 changes per sequence. The
writer's samples for a task differ in readability far less than a program
and its obscured copy, so readability differences between them can move
this score by much less than that, below the 0.15 the headroom check asks
for. At 50 lines the editor reads the whole program and changes it
whatever it is called, which is also why removing comments changed
nothing (`results/nocomments_eval.md`).

So on these tasks no change to the writer in names, comments or layout
can show up as more changes done; only programs that differ in what they
do, or in how they hold up once changed, could.

## Writer-size probe

A weaker writer's passing programs might differ in what the control above
leaves: mistakes the initial tests miss, or code that breaks once changed.
The dev run again with Qwen2.5-Coder-3B as the writer (same prompt,
temperature 0.4, 14B editor; `configs/rtx5070_pc_writer_3b.yaml`, run
20261116T195823Z-de1d3b: 128 samples, 118 steps, 1 hour 24 minutes, 1
infrastructure error):

| Dev task | Distinct programs | Pass the initial tests |
|---|---:|---:|
| bank_ledger | 16 | 0 |
| course_enrollment | 15 | 1 |
| football_season | 13 | 0 |
| library_catalog | 16 | 0 |
| lru_cache | 15 | 0 |
| parking_garage | 15 | 0 |
| shopping_cart | 15 | 8 |
| team_roster | 15 | 1 |

10 of 120 programs pass (8%, against 55% of the 7B writer's samples), and
7 replies did not parse. The failures are real mistakes, not format: in
bank_ledger, for example, a history kept per account whose lists are never
created, or checks raised in a different order from the spec's. Only
shopping_cart has more than one passing program, and there every trial of
a sequence gets the same score, so there is no variance to split and no
pair. On the train tasks a 3B writer would leave almost no task with two
programs to compare, so it cannot feed the method.

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
uv run python -m harness collect --config configs/rtx5070_pc_editor_t02.yaml   # GPU, ~6.5 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_editor_t02.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_pc.yaml \
    --other configs/rtx5070_pc_editor_t02.yaml --bootstrap 20000
uv run python -m harness collect --config configs/rtx5070_pc_editor_patch.yaml   # GPU, ~10 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_editor_patch.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_pc.yaml \
    --other configs/rtx5070_pc_editor_patch.yaml --bootstrap 20000
uv run python -m harness collect --config configs/rtx5070_pc_editor_7b.yaml    # GPU, ~5 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_editor_7b.yaml --measures
uv run python -m harness collect --config configs/rtx5070_pc_editor_3b.yaml    # GPU, ~3 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_editor_3b.yaml --measures
uv run python -m harness collect --config configs/rtx5070_pilot.yaml           # GPU, ~2 h
uv run python -m harness collect --config configs/rtx5070_pilot_maintain.yaml  # GPU, ~2 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pilot.yaml
uv run python scripts/diagnostics.py --config configs/rtx5070_pilot_maintain.yaml
for t in sample_freezers herd_paddocks; do                                     # GPU, ~1 h each
  uv run python scripts/design_probe.py --config configs/rtx5070_pilot.yaml --task $t \
      --variant state=results/design_probe/$t/state --variant log=results/design_probe/$t/log \
      --reps 6 --store /home/pc/design_probe/store
  uv run python scripts/design_probe.py --config configs/rtx5070_pilot_editor_v3.yaml --task $t \
      --variant state=results/design_probe/$t/state --variant log=results/design_probe/$t/log \
      --sequence s2 --reps 6 --store /home/pc/design_probe/store
done
uv run python -m harness collect --config configs/rtx5070_pc_editor_v3.yaml    # GPU, ~6 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_editor_v3.yaml --measures
uv run python -m harness collect --config configs/rtx5070_pc_hints.yaml        # GPU, ~5 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_hints.yaml --measures
uv run python scripts/hint_summary.py --config configs/rtx5070_pc_hints.yaml
for c in rtx5070_train rtx5070_pc rtx5070_pc_editor_v3 rtx5070_pc_hints; do
  uv run python scripts/edit_carryover.py --config configs/$c.yaml
done
uv run python -m harness collect --config configs/rtx5070_pc_outline.yaml      # GPU, ~10 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_outline.yaml --measures
uv run python scripts/hint_summary.py --config configs/rtx5070_pc_outline.yaml
uv run python scripts/edit_carryover.py --config configs/rtx5070_pc_outline.yaml
uv run python scripts/eval_compare.py --base configs/rtx5070_pc_hints.yaml \
    --other configs/rtx5070_pc_outline.yaml --bootstrap 20000
uv run python scripts/obscure_check.py --config configs/rtx5070_pc.yaml
uv run python -m harness collect --config configs/rtx5070_pc_obscure.yaml      # GPU, ~6.5 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_obscure.yaml --measures
uv run python scripts/eval_compare.py --base configs/rtx5070_pc.yaml \
    --other configs/rtx5070_pc_obscure.yaml --bootstrap 20000
uv run python scripts/ablation_compare.py configs/rtx5070_pc.yaml \
    configs/rtx5070_pc_obscure.yaml --bootstrap 20000
uv run python -m harness collect --config configs/rtx5070_pc_writer_3b.yaml    # GPU, ~1.5 h
uv run python scripts/diagnostics.py --config configs/rtx5070_pc_writer_3b.yaml --measures
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
