# History suite: tasks where the program's design decides later changes

On the original 60 tasks only 4% (train) to 11% (eval) of a trial's score
variance belongs to the program (`harness/results/diagnostics.md`): the
14B editor rewrites small files whole and fails on the edges of each change,
whatever the program. The one setting where the program's design decided
the outcome was the design probe: with the editor prompt that asks it to
build on the program's design (`prompts/editor_v3.md`), undo worked in 4 of
6 trials for a program that records its operations and in 0 of 6 for the
same program keeping plain state. What made undo fail for plain state was
exactly what a recorded history or a snapshot of the state gets right for
free: one undo after a composite call must take back the whole call, and
something removed must come back in its old position.

This suite builds on that. Every task has the usual shape (README.md), plus:

- **operations that do several things at once** (move everything from one
  place to another, close or merge a place, remove something together with
  what belongs to it), and **order that the getters expose** (things listed
  in the order they were added);
- **an undo change in both sequences**, written like `herd_paddocks`'
  `c_undo`: undo reverses the most recent successful call that changes
  anything, a composite call as a whole, and puts everything back exactly,
  including order and removed things; calls that raised are not recorded.

The spec never says how to store the state. A writer that records its
operations, or keeps its state in one structure it can copy, finds undo
easy; one that writes the logic out in each method leaves the editor to
write an inverse for every operation. The writer's samples for the train
collection are drawn with the generic design hints already used on the dev
tasks (`configs/rtx5070_pc_hints.yaml`; none names a task or a change), and
pairs keep the plain prompt, so a writer trained on them would learn the
preferred designs without hints.

## Rules for each task (on top of README.md)

### Spec

- One file, one class plus exception classes, 6 to 8 public methods. Two
  or more of them are **composite or destructive**: they move, merge or
  remove several things in one call (for example `move_all`,
  `close_x(name, into)`, `merge_x(a, b)`, `remove_x` that also removes
  what belongs to it).
- At least one getter returns things **in the order they were added** (or
  in an order the caller set), so that putting something back in the wrong
  place is visible.
- Easy to get right for a 7B model in one attempt: one obvious error class
  per kind of problem, no formulas, no zero-size special cases beyond "a
  count must be greater than 0", no rule about which of two errors comes
  first (say it is unspecified), and "a failed call has no effect".
- Do not prescribe the internal design (no `self._ops`, no history, no
  snapshots, no undo, no "keep a log"). Nothing in the spec may mention
  undo, history or later changes.
- Hidden initial tests check the stated rules on ordinary inputs. No traps.

### Changes

- **train and dev** (2 changes per sequence): three changes `U`, `B`, `C`.
  - `U`, kind `undo`: `undo()` as in `herd_paddocks/changes/c_undo/request.md`.
    It reverses the most recent successful call among the methods that
    change state (list them by name), a composite call as one call, and
    restores everything exactly, including order, removed things coming
    back where they were, and names becoming free or taken again. Calls
    that raised are not recorded. Getters and `undo` itself are not
    recorded. With nothing left to undo it raises the task's base error
    and changes nothing. No redo.
  - `B`, kind `validation_rule` or `state_flag`: a rule that every
    state-changing operation of some kind must obey, including the
    composite ones (a capacity, an allowed list, a lock or freeze flag).
  - `C`, kind `atomic_operation`, `query`, `derived_value` or `grouping`.
    In about half the tasks make it `atomic_operation`: a new method that
    applies several operations as one call that succeeds or fails as a
    whole.
  - Sequence `s1`: `U` then `B`. Sequence `s2`: `C` then `U`.
  - When `U` comes after `C`, its request lists `C`'s new method among the
    recorded calls only if `C` changes state (write `U`'s request so it
    works in both orders: "every method that changes the state, including
    any added later, is undoable" is fine, but the hidden tests for `U` in
    `s1` must not call `C`'s method). When `B` comes after `U`, `B`'s
    request says that undo still restores the exact earlier state.
- **eval** (3 changes per sequence): four changes `U`, `B`, `C`, `K`, with
  `K` of kind `configuration` or `concurrency_control` (eval-only kinds;
  every eval task needs one, and train and dev tasks may not use them).
  Sequence `s1`: `U`, `B`, `K`. Sequence `s2`: `C`, `U`, `B`.
- Every request ends with "All existing behavior must keep working."

### Tests

- Public checks for `U` cover only the basics, like `herd_paddocks`: undo
  of one simple call, undo of a simple move, and nothing to undo. The
  hidden tests cover every rule of the request, and most of them are the
  design-relevant ones: undo of each composite or destructive call as one
  call, order and removed things restored, several undos in a row, undo
  after a call that raised, new calls after an undo, undo of `add_…`.
- Hidden tests of `B` and `C` check their stated rules on ordinary inputs.
  No tests of unspecified corners (zero-size moves, error order, types).
- Test only through the public interface. A change's tests call only the
  spec's methods and that change's own methods (never another change's),
  since the same test files run in both sequences.

### Eval rule, fixed before any eval result

An eval task enters the comparison of two writers only if each writer has
at least one program that passes its initial tests (a task with none gives
no score to compare). This is what `scripts/eval_compare.py` does: it keeps
the tasks where both writers have trials. No task is dropped for any other
reason.

### Writer check

The first versions of these tasks set traps the 7B writer fell into on most
samples (rules only some programs check, such as count limits on removals
or re-adding a removed name; orders that differ from what the code
naturally keeps; lists changed while looping over them). After a writer
check (`collect --until initial`), each spec was simplified: such rules
became unspecified and untested, and short Python notes name the crashes
seen. The composite operations, the orders the getters expose and the
undo change were kept.

### Gate on the first three train tasks, and what changed

The first collection (`configs/rtx5070_hist_train13.yaml`: the prose hints
of `rtx5070_pc_hints.yaml`, 8 programs, 2 sequences x 2 reps, 8 editor
turns) was checked on cargo_holds, study_groups and garden_beds before
going on. Undo worked in 1 of 92 trials. In 57 the editor ran out of
turns and in the rest it failed about half the hidden undo tests, for
every program alike: the program's share of a trial's score was 0% and
the held-out headroom 0. The editor writes undo as inverse calls to the
program's public methods, which record themselves again, and once stuck it
sends its file back unchanged until its turns run out. Scored by the share
of hidden undo tests passed, the program's share is 19%, but programs that
record their operations do no better than the others.

The 7B writer had followed none of the hints that matter here: the
"history" hint gave a list of tuples nothing reads, and the "replace the
state" hint was ignored. A probe with hand-written cargo_holds programs
(`results/design_probe/hist_cargo_holds/`, `scripts/design_probe.py`, 3
reps per sequence) separates the designs: undo as the first change worked
in 2 of 3 trials for a program that makes every change on a deep copy of
its state and keeps the copy only when the call succeeds, and in 0 of 3
for the same program changing its state in place (0 of 3 for one that
rebuilds its state by replaying its operations). After another change,
undo failed for all three. A prose hint describing the copy design was
ignored too (2 of 35 passing programs on the three tasks made their changes
on a deep copy), and so was a code fragment of it (1 of 24). A whole small
example class for an unrelated specification was followed by every hinted
sample, though its programs passed the initial checks less often.

So the train collection was restarted with
`configs/rtx5070_hist_train_hints2.yaml`: that example, which names no
task, change or undo, given to three quarters of 16 samples per task (the
others get no hint), 5 editor turns (2.3% of the successful steps in the
store used more than 5 calls) and one trial per sequence. The eval configs use the same editor settings
(`configs/rtx5070_hist2_eval.yaml`). These were set before any eval trial
of this suite was run.

### The train collection, plain DPO, and DPO+NLL

Over all 16 train tasks, 38 of the 84 passing programs used the copy
design. Their mean score was 0.76 changes per sequence against 0.40 for
the 46 that changed their state in place, +0.16 against their task's mean
(95% interval +0.08 to +0.26), and −0.13 (−0.22 to −0.05) for the in-place
programs. The aggregate rule gave 83 pairs. 74 of them prefer a
copy-design program: 49 against an in-place one, 25 against a worse copy.

Plain DPO with dpo3's settings (`hist2_dpo`) didn't move the writer. On the
dev tasks without a hint, 0 of its 21 passing programs used the copy
design (base writer 0 of 30), and fewer of its programs passed. A
copy-design program is very unlikely under the plain prompt, and DPO can
widen the margin by lowering both programs. So `hist2_dpo` was stopped
before any eval trial. The writer was trained again with DPO+NLL
(`--nll-weight 1` in `train_dpo.py`, the chosen program's per-token NLL as
in RPO, Pang et al. 2024, the same loss as `train_sft.py`). There are two
settings, chosen on dev only by a rule fixed before training:

- **A** (`hist2_rpo`): dpo3's settings plus the NLL term.
- **B** (`hist2_rpo_b`): lr 5e-5 and 3 epochs. It is trained only if under
  a quarter of A's passing dev programs use the copy design.

Of A and B, the setting with more passing copy-design programs on dev goes
to the eval. The correctness-only control (`hist2_sft`: SFT on the same
train collection's passing programs, both designs, no editing outcomes)
is compared with it.

Here is how the two settings did on dev:

- **A** kept the writer correct (27 passing dev programs) but changed no
  design: 0 of 27. Over training, the chosen programs' log-probability rose
  16 nats from the reference and the rejected ones' 1.
- **B** learned the design: 34 of its 64 dev samples make their changes on
  a deep copy. But it overfit (final DPO loss 0.001, chosen +51 nats,
  rejected −14), and only 7 samples passed the initial checks, 4 of them
  copy designs. Its failures are about the specification (wrong exception
  types, lookups of names that aren't there, and even NameErrors in plain
  programs), not about the design.

The eval only scores tasks where both writers have passing programs, so a
writer that rarely passes would drop tasks and trade correctness for
editability. So B's eval was stopped during its first task's writer
sampling, before any editing. Two settings in between were added:

- **C:** lr 5e-5, 2 epochs.
- **D:** lr 3e-5, 3 epochs.

The rule was revised before C and D were trained. A setting is eligible
if its passing dev programs are at least two thirds of the base writer's.
The eligible setting with the most passing copy-design programs goes to
the eval (ties go to the less trained setting, in the order A, D, C, B).
If no eligible setting has any, the setting with the most passing
copy-design programs goes. The control's SFT uses the chosen setting's lr
and epochs.

| Setting | lr, epochs | Passing dev programs | Copy design among them | Chosen − ref log-prob | Rejected − ref |
|---|---|---:|---:|---:|---:|
| base | – | 30 | 0 | – | – |
| plain DPO (`hist2_dpo`) | 2e-5, 2 | 21 | 0 | – | – |
| A (`hist2_rpo`) | 2e-5, 2 | 27 | 0 | +16 | +1 |
| D (`hist2_rpo_d`) | 3e-5, 3 | 20 | 10 | +36 | −7 |
| C (`hist2_rpo_c`) | 5e-5, 2 | 18 | 11 | +40 | −2 |
| B (`hist2_rpo_b`) | 5e-5, 3 | 7 | 4 | +51 | −14 |

D went to the eval: it is the only eligible setting (20 ≥ two thirds of 30)
with any passing copy-design programs. Its passing programs per dev task
were seed_vault 13 (base 14), choir_sections 6 (8), tram_lines 0 (0) and
photo_albums 1 (8).

### Files and checks

Exactly as README.md: references for every set of changes a sequence
reaches (train and dev: `v0`, `U`, `U+B`, `C`, `C+U`; eval: `v0`, `U`,
`U+B`, `U+B+K`, `C`, `C+U`, `B+C+U`; keys are the sorted change ids joined
by `+`), the planted bugs the loader requires, and `split` and `family`
in `task.yaml` (`family` = the task id). The task must pass
`validate-tasks`.
