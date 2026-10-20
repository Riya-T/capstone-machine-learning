# Tasks

Make sure to have one directory per task. Copy one of `bank_ledger/`, `football_season/` or
`team_roster/` as a starting point; each is about 1,500 lines with tests.
A task is ready once `validate-tasks` passes and the writer check below passes.

## Files

```
<task_id>/
  task.yaml                   manifest tying everything together
  spec.md                     initial request          → writer sees it
  public/test_*.py            3–6 basic checks         → writer and editor see them
  private/test_*.py           hidden initial tests     → nobody sees them
  changes/<change_id>/
    request.md                a later change request   → editor sees it
    public/test_*.py          2–4 basic checks         → editor sees them
    private/test_*.py         hidden new-feature tests → nobody sees them
  reference/<name>/<files>    correct solutions        → nobody sees them
  bugs/<name>/<files>         planted bugs             → nobody sees them
```

## Writing the spec

The 7B writer gets one attempt and never runs the checks, so the initial
spec must be easy to get right. Save the difficulty for the changes.

- **Small interface**: one file, one class, 4–7 methods, built-in
  exceptions where possible.
- **Name every method that returns data `get_…`** (`get_balance`, not
  `balance`). Otherwise the writer stores data under the same name
  (`self.balance = …`) and replaces the method.
- **Return simple values**: a list of names beats a list of dicts with keys
  to remember.
- **No formulas with edge cases**, such as dividing by games played: the
  writer forgets the zero case. Use counts or sums instead.
- **Keep every sort direction the same** ("highest first"), and break ties
  by the order things were added, not alphabetically. The writer sorts with
  `reverse=True`, which flips a mixed order.
- **Leave Python details unspecified**: `bool` counting as `int`, returning
  copies, non-string names. List them under "Unspecified behavior".
- **Don't dictate the internal design.** The experiment compares designs,
  so the writer needs real choices (how to store things, what to compute
  on demand). If every writer program comes out the same, the spec is too
  prescriptive.
- Give parts that interact, so later changes can expose a design's
  weaknesses.

## Writing the changes

- Written like a ticket: the exact new behavior, the order of errors where
  it matters, ending with **"All existing behavior must keep working."**
- Make each change backward compatible (new methods, new keyword arguments
  with defaults), so existing tests keep passing. If a change must alter old
  behavior, list the old test under `supersedes`.
- Give each a `kind` from `tasks.change_kinds` in `configs/base.yaml`:

  | Kind | Example |
  |---|---|
  | `validation_rule` | a new constraint on inputs (unique emails, limits) |
  | `state_flag` | a status that changes what's allowed (freezing, injuries) |
  | `atomic_operation` | several changes that succeed or fail together (trades) |
  | `undo` | removing or reversing something already recorded |
  | `derived_value` | a new value computed from existing data (fees, streaks) |
  | `grouping` | splitting items into categories (divisions) |
  | `query` | new ways to search or filter existing data |
  | `configuration` | making a fixed rule adjustable (custom points) — **eval only** |
  | `concurrency_control` | detecting conflicting updates (versions) — **eval only** |

  Train and dev tasks can't use the eval-only kinds, and every eval task
  must use at least one; the task won't load otherwise. This tests whether
  the trained writer writes code that is easier to change in general, not
  just code that anticipates the kinds of change it trained on (dev counts
  too, since we tune settings on it). To add a kind, add
  it to the list in `base.yaml`.
- **Sequences.** A sequence is an ordered list of changes the editor makes
  one after another to the same program. Every task has two.
  - **train and dev**: each sequence has 2 changes. Write 3 changes and
    share one between the sequences: sequence 1 adds A then B, sequence 2
    adds C then A. In `bank_ledger`, sequence 1 is overdraft limits then
    fees, and sequence 2 is freezing accounts then overdraft limits.
  - **eval**: each sequence has 3 changes, so write 4–5 changes. Eval uses
    longer sequences to check that the advantage holds up over more edits.

## Writing the tests

- Hidden tests check every rule the spec or request states. The hidden
  initial tests are rerun after every change, to catch broken old behavior.
- Public checks cover the basics, and the cases the writer tends to get
  wrong (e.g. a team that hasn't played yet), since the writer sees them.
- Test only through the public interface: never internal names, attributes
  or file formats.
- Test file names must be unique within the task.

## References and planted bugs

- **References**: `reference/v0/`, plus one per set of changes a sequence
  reaches, mapped under `references` in `task.yaml` (5 for train and dev).
- **Planted bugs**, at least these three, or the task won't load:
  1. on the initial spec, a bug the public checks miss:
     `must_fail: [initial]`, `must_pass: [public]`;
  2. on each sequence's last step, a regression bug that makes the change
     correctly but breaks an earlier behavior:
     `must_fail: [existing]`, `must_pass: [new_feature]`.

  Each is a copy of a reference with a few lines changed: a realistic
  mistake, not code that crashes on import.

## Testing a task

From `harness/`, with the task id in the config's `tasks.include`:

1. **Validate it** (sandbox only, no models):

   ```bash
   uv run python -m harness validate-tasks --config configs/noahs_laptop.yaml
   ```

   It checks that references pass, planted bugs fail as declared, each
   change's tests fail before the change, and nothing leaks to the writer.

2. **Run the writer check** (needs the local model; about 3 minutes per
   task on the laptop):

   ```bash
   uv run python -m harness collect --config configs/noahs_laptop.yaml --until initial
   ```

   The summary's `passed` column must show **at least 3 of 8** programs
   passing. If not, look at which hidden tests fail most and simplify the
   spec using the rules above. Also check the passing programs differ in
   structure, not just in names.


