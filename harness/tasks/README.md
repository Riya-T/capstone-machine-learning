# Tasks

One directory per task, each with a `task.yaml` manifest. There are no
tasks yet. `tests/data/tasks/record_store/` is a complete example to copy;
it is about 1,200 lines including tests, so plan on roughly a day per task.

A task belongs here only after `validate-tasks` reports no problems and the
team has reviewed its tests.

## Creating a task

### The files

```
tasks/<task_id>/
  task.yaml                       manifest that ties everything together
  spec.md                         initial request             → writer sees it
  public/test_*.py                a few public checks         → writer and editor see them
  private/test_*.py               hidden initial tests        → nobody sees them
  changes/<change_id>/
    request.md                    one later change request    → editor sees it
    public/test_*.py              a few public checks for it  → editor sees them
    private/test_*.py             hidden new-feature tests    → nobody sees them
  reference/<name>/<files>        correct solutions           → nobody sees them
  bugs/<name>/<files>             deliberately broken ones    → nobody sees them
```

### 1. `spec.md`: the initial request

What the writer gets. It needs:

- the exact interface: file name, class and function signatures, error
  types;
- the required behavior, including edge cases. Every rule you write here
  should be checked by a hidden test;
- an **"Unspecified behavior"** section listing what no test depends on
  (e.g. corrupt files, bad paths), so the writer can choose its own design
  without being penalized.

Don't dictate the internal design. The research question is whether some
designs are easier to change later, so the writer must be free to choose.
Tasks should have parts that interact, like validation and storage in
record_store.

### 2. Change requests: `changes/<id>/request.md`

Each one is a later feature the editor must add, written like a ticket.
Each needs:

- a precise description of the new behavior, including the order of checks
  and errors where it matters;
- the line **"All existing behavior must keep working."** at the end;
- a `kind` in `task.yaml` (e.g. `validation_rule`, `concurrency_control`,
  `atomicity`). Eval tasks need kinds the training tasks never use, so use
  the team's agreed list of kinds.

How many you need depends on the split:

- **train and dev:** 2 sequences of **2** changes each, so at least 3
  changes if the sequences share one (record_store uses `conflict → txn`
  and `unique → conflict`);
- **eval:** 2 sequences of **3** changes each, so at least 4–5 changes.

### 3. Tests

| File | Who sees it | What it checks |
|---|---|---|
| `public/test_*.py` | writer and editor | 3–6 basic tests: the format and the obvious behavior |
| `private/test_*.py` | nobody | every rule in the spec. Decides whether a program is initially correct |
| `changes/<id>/public/test_*.py` | editor | 2–4 basic tests of the change |
| `changes/<id>/private/test_*.py` | nobody | every rule in the change request |

The hidden initial tests are reused as the "existing behavior" tests after
every change; that's how a step that breaks old behavior is caught.

Rules for tests:

- Test **only behavior through the public interface**: never internal
  names, attribute layout or file formats, or a valid design that differs
  from yours will fail.
- Every test file name must be unique within the task (e.g.
  `test_conflict_new.py`, not a second `test_new.py`).
- If a change deliberately changes old behavior (record_store's unique
  emails make "two records may share an email" false), list the old test
  under the change's `supersedes`.

### 4. Reference solutions: `reference/<name>/`

A correct program for **every combination of changes the sequences reach**:

- `reference/v0/` for the initial spec;
- one for each set of applied changes, mapped under `references` in
  `task.yaml`. record_store needs `c_conflict`, `c_conflict+c_txn`,
  `c_unique` and `c_conflict+c_unique`, plus v0, for 5 in total. Eval tasks,
  with 3-change sequences, need more.

Each must contain exactly the files in `entry_files`.

### 5. Planted bugs: `bugs/<name>/`

Realistically broken programs, to prove the hidden tests catch the
mistakes our scores depend on. Every task needs **at least these three**;
the task won't load without them:

1. **One on the initial spec** (in the top-level `planted_bugs`). It
   breaks a spec rule the public checks don't cover, so it must fail the
   hidden initial tests while still passing the public checks:
   `must_fail: [initial]`, `must_pass: [public]`.
2. **One regression bug per sequence**, on that sequence's **last step**
   (in that step's `planted_bugs`). It makes the step's change correctly
   but silently breaks behavior from an earlier step or the initial spec,
   for example adding transactions but dropping the version check. It must
   fail the existing-behavior tests while passing the new-feature tests:
   `must_fail: [existing]`, `must_pass: [new_feature]`.

Add more wherever they help, for example to prove the tests catch a
tricky rule. In record_store, `v0_reuses_ids` and `conflict_drops_unique`
are the required kinds; `v0_no_persist` and `conflict_nonatomic_update`
are extras.

A planted bug is usually a copy of a reference solution with a few lines
changed. Keep the change small and realistic: the kind of mistake an
editor could make, not deleted code that crashes on import.

### 6. `task.yaml`

Copy it from record_store and fill in:

```yaml
schema_version: 1
id: <task_id>              # must match the folder name
family: <family>           # close variants share a family; a family stays in one split
split: train               # train, dev or eval
entry_files: [<file>.py]
spec: spec.md
public_checks: [public/test_public.py]
private_tests: [private/test_initial.py]
reference: reference/v0
planted_bugs: [...]        # at least one bug only the hidden initial tests catch
changes: [...]             # id, kind, request, public_checks, new_feature_tests, supersedes
references: {...}          # set of applied changes -> reference folder
sequences: [...]           # 2 sequences; each last step needs a regression bug
```

### 7. Validate it

Add the task id to a config's `tasks.include`, then from `harness/`:

```bash
uv run python -m harness validate-tasks --config <config>
```

It fails if:

- a reference fails any test where it is used;
- a planted bug doesn't fail exactly its `must_fail` groups;
- the program **before** a change already passes that change's new tests
  (the tests could be passed by doing nothing);
- a line of 30+ characters from a change request appears in anything the
  writer sees (a leak);
- the sequence count or lengths are wrong for the split, a change or
  reference is never used, a test file name repeats, or there's a symlink.

### 8. Get it reviewed

`validate-tasks` can't check these; a teammate should, **before** anyone
looks at model results on the task:

- Do the hidden tests **reject a valid design**? If you can, run them
  against a second, differently structured correct solution.
- Is the spec or a change request **ambiguous**, so that two reasonable
  readings give different answers?
- Is each change **too easy or too hard** for the editor? It should take
  real work but fit the editor's turn budget (calibrated on dev tasks).
- Do the family and split keep close variants out of eval?
