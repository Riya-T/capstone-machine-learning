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

### Files and checks

Exactly as README.md: references for every set of changes a sequence
reaches (train and dev: `v0`, `U`, `U+B`, `C`, `C+U`; eval: `v0`, `U`,
`U+B`, `U+B+K`, `C`, `C+U`, `B+C+U`; keys are the sorted change ids joined
by `+`), the planted bugs the loader requires, and `split` and `family`
in `task.yaml` (`family` = the task id). The task must pass
`validate-tasks`.
