# Training Coding Agents Using Later Modification Outcomes

Our project asks whether training a code writer on how easily its programs
can be changed later makes it write code that is easier to modify. See
`docs/Project_Proposal_473_v2.docx.pdf` for the research question and the
experimental design.

## Repository layout

```
docs/       project documents (the proposal)
harness/    the pipeline: generates programs, runs the editor, builds preference pairs
```

The harness grew out of an earlier pilot: a small trial on one task with a
local 7B model as both writer and editor. It found problems such as the
editor repeating itself, which the harness fixes. The pilot's code was
removed and is still in the git history.

## The harness

The harness builds the training data: preference pairs of
programs where both programs pass the initial tests, but one was easier for
a fixed editing agent to change later. For each task it:

1. asks the **writer** model for several implementations of the task;
2. keeps the ones that pass the initial tests;
3. has the **editor** model apply the same sequence of later changes to
   each one, several times, in a sandbox;
4. scores each implementation by how many changes in a row the editor
   completed before its first failure;
5. pairs the higher-scoring implementation (chosen) against a lower-scoring
   one (rejected) for DPO training.

It holds the core pipeline; training (DPO, baselines) and held-out
evaluation are not built yet (see [Not built yet](#not-built-yet)). All
paths from here on are relative to `harness/`.

### Quick start

Requirements: Python 3.11, [uv](https://docs.astral.sh/uv/), and Docker
(generated code only ever runs inside a container).

```bash
cd harness
uv sync                                   # install dependencies
uv run pytest -rs                         # tests; Docker tests run if a daemon answers
uv run pytest -rs --slow                  # also the slow ones (full collection, task validation)

# Check that every task's tests accept its reference solutions and reject its planted bugs.
uv run python -m harness validate-tasks --config configs/mock.yaml

# Run the whole pipeline with the deterministic mock writer and editor.
uv run python -m harness collect --config configs/mock.yaml
uv run python -m harness collect --config configs/mock.yaml --until initial   # stop after a stage

# Rebuild the preference files from stored results, with no model calls.
uv run python -m harness report --config configs/mock.yaml
```

The first run builds the sandbox image `harness-sandbox:py3.11-v1` from
`docker/sandbox/Dockerfile`. To run real models, write a config whose
`writer.backend` and `editor.backend` are `kind: openai_compat` and point at
an OpenAI-compatible server (vLLM, Ollama, llama.cpp).

### How it works

```
                   task directory (tasks/<id>/)
                   spec, tests, changes, references
                              │
              registry: writer sees spec + public checks only
                              │
  ┌───────────────────────────▼───────────────────────────┐
  │ 1. Writer samples    N answers from the writer model  │  models/backends.py
  │                      → parsed into files              │  models/parser.py
  ├───────────────────────────────────────────────────────┤
  │ 2. Initial checks    public checks + private initial  │  sandbox/evaluator.py
  │                      tests; failures and duplicates   │  sandbox/runner.py
  │                      drop out                         │
  ├───────────────────────────────────────────────────────┤
  │ 3. Editing trials    each surviving program × each    │  collection/editor.py
  │                      change sequence × each rep:      │  collection/collect.py
  │                      the editor applies the changes   │
  │                      in order; hidden tests score     │
  │                      each step; stop at first failure │
  ├───────────────────────────────────────────────────────┤
  │ 4. Scoring           per-program scores → pairs       │  collection/scorer.py
  └───────────────────────────┬───────────────────────────┘
                              │
            runs/<run_id>/preferences.jsonl  (+ report, summary)

  Every result and every model call is saved in runs/ (store.py) as it happens,
  so an interrupted run resumes where it stopped and a rerun makes no model calls.
```

#### Step by step

**1. Writer samples.** The writer prompt is built from
`prompts/writer_v1.md` and the task's spec and public checks, nothing
else. The registry enforces this by type, so later change requests,
private tests and references cannot reach the writer. Each sample gets its
own seed. The parser turns the answer into files, and it is strict: every
code block must be labelled `python file=<path>` with an allowed path. An
answer that breaks the format, or that was cut off at `max_tokens`, is
recorded as a parse failure with a reason, never guessed at.

**2. Initial checks.** Each distinct program runs the task's public checks
and its private initial tests in the sandbox. Only programs that pass both
go on. Programs with the same content are run and scored once.

**3. Editing trials.** A *trial* is one program, one change sequence and
one repetition. For each step of the sequence, the editor gets a turn loop
(below) to make the change, and the hidden tests then grade the result in
two parts:

- **new-feature tests**: does the change work?
- **existing tests**: does everything that worked before still work?

A step succeeds only if both pass. The trial stops at the first failed
step. Each trial starts from a fresh copy of the original program.

**4. Scoring.** A trial's score is the number of changes completed in a
row before the first failure. A program's score for a sequence is the mean
over its repetitions. Two programs from the same task are compared by a
rule over their per-sequence scores:

- `weak_dominance` (primary): at least as good in every sequence and
  better in at least one;
- `strict`: better in every sequence.

Ties and inconsistent comparisons (better in one sequence, worse in another)
give no pair. `pairing_mode` picks which comparisons become pairs:
`best_vs_worst` (one pair per task) or `all_pairs` (every comparison, with an
optional `per_task_cap`). All combinations are computed side by side in the
report, and the ablations from the proposal (one change instead of two, one
repetition instead of three) are computed from the same trials.

#### The editor turn loop

The editor works in turns, up to the budget in the config (`max_turns`,
`max_total_tokens`, `wall_time_s`). Each turn's prompt
(`prompts/editor_v2.md`) is rebuilt from scratch and contains:

- the current change request (never later ones, never private tests);
- the current files;
- the full result of the previous turn (check output or an error);
- a one-line summary of each of the latest `history_turns` turns.

The editor replies with complete new files and/or one command:
`RUN_CHECKS` (run the public checks and see the output next turn) or `DONE`.
The step also ends as soon as every public check passes.

Three rules keep the loop from wasting turns, a problem the pilot found
(the editor sent the same reply 7 or 8 times in a row):

- each turn is sampled with its own seed, derived from the trial's seed;
- the turn summaries show the editor what it already tried;
- `RUN_CHECKS` on code that was already checked doesn't run the checks
  again. The turn counts as wasted and the editor is shown the earlier
  result. A reply that changes nothing counts as wasted too.

Bad replies (wrong format, a file outside the program, cut off) are wasted
turns, never crashes. Nothing from them is applied.

### Key components

All code is in `src/harness/`. Each file starts with a header describing it
and how to use it; `docs/units.md` lists every unit with its tests.

| Component | File | What it does |
|---|---|---|
| Configuration | `config.py` | Loads a YAML config (with `extends`) into frozen, strictly checked settings. An unknown or misspelled key is an error, not a silent default. Hashes settings to key stored results. |
| Task registry | `registry.py` | Loads task directories and checks their rules (splits, sequences, references, leaks). Builds the writer prompt from writer-visible files only. |
| Results store | `store.py` | One SQLite database plus program files stored by content hash. Writes each result as soon as it exists and never overwrites one. Logs the git commit and full config of every run. |
| Model backends | `models/backends.py` | One interface, `generate(prompt) -> text`, for an OpenAI-compatible server or a deterministic mock. `CachedBackend` records every call, so reruns replay recorded answers. |
| Answer parser | `models/parser.py` | Turns a model's answer into program files, or a failure with a reason. |
| Sandbox runner | `sandbox/runner.py` | Runs code in a fresh Docker container: no network, not root, read-only code, limits on memory, CPU, processes, file size and time. Always removes the container. Docker's own failures are reported as `infra_error`, never as the program's fault. |
| Contract evaluator | `sandbox/evaluator.py` | Runs each test category (initial, public, new-feature, existing) in its own container and reads the results. Validates tasks: references must pass, planted bugs must fail as declared. |
| Editor | `collection/editor.py` | The turn loop above. |
| Collection | `collection/collect.py` | Runs steps 1–4 for every task in the config, resuming wherever it stopped. |
| Scorer | `collection/scorer.py` | Scores trials, applies the preference rules, counts every excluded sample or comparison by reason, writes the output files. |
| Command line | `__main__.py` | `collect`, `validate-tasks`, `report`. |

### Tasks

A task is a directory under `tasks/` with a `task.yaml` manifest. There
are no real tasks yet. The tests use one example task,
`tests/data/tasks/record_store/` (a file-backed record store), which shows
the layout:

```
record_store/
  task.yaml                 manifest: split, files, changes, sequences
  spec.md                   the initial request (the writer sees this)
  public/                   public checks for the initial request (the writer sees these)
  private/                  hidden initial tests
  changes/<change_id>/
    request.md              the change request (the editor sees this)
    public/                 public checks for the change (the editor sees these)
    private/                hidden new-feature tests
  reference/<name>/         correct solutions, one per set of changes applied
  bugs/<name>/              deliberately wrong solutions the tests must reject
```

The manifest declares the task's `split` (`train`, `dev` or `eval`) and its
`family`: close variants share a family and must share a split. A sequence
lists its changes in order. Each change has a `kind` from the list in
`configs/base.yaml`; some kinds are held out for eval tasks only, so
evaluation tests kinds of change the writer never trained on. A change can
`supersede` an initial test whose behavior it changes on purpose. A planted bug declares which test categories
must fail (`must_fail`) and which must still pass (`must_pass`).

To add a task, follow the step-by-step instructions in
[harness/tasks/README.md](harness/tasks/README.md): what to write, how many
changes and references each split needs, what `validate-tasks` checks, and
what the team must review by hand.

### Configs

`configs/base.yaml` holds every setting with comments. Variants
`extends: base.yaml` and override only what differs:

- `configs/mock.yaml`: the mock writer and editor (`fixtures/mock/`) on
  the example task in `tests/data/tasks/`, for tests and the end-to-end
  check.

Settings that change results (models, prompts, budgets, sandbox limits,
seeds) are part of the result keys. `execution` holds settings that never
change results (how many containers run at once).

### Results and resuming

```
runs/
  harness.sqlite            all results and every model call
  blobs/<sha256>.json       programs, by content hash
  <run_id>/
    run.json                git commit, dirty flag, full config
    preferences.jsonl       the DPO pairs
    preferences_report.json counts, exclusions, every rule × pairing combination, ablations
    summary.txt             the same, as a readable table
```

Each line of `preferences.jsonl` has the writer `prompt`, the `chosen` and
`rejected` programs, their ids and per-sequence scores, the `margin`, the
`rule` and `pairing_mode`, whether the `strict` rule agrees
(`strict_subset`), and the model-call keys of both programs.

Every result is keyed by everything that determines it: the writer key
includes the prompt template's contents, and the editor key includes the
editor config, its prompt, the editor protocol version and the sandbox
image. Changing any of these starts fresh results instead of mixing old
and new. Infrastructure errors (Docker failed, the model server was down)
are never scored; the next run retries them.

### Not built yet

These are in the proposal but not in the harness yet:

- DPO training with TRL and QLoRA, and the training baselines
  (correctness-only fine-tuning, DPO on Radon maintainability rankings, a
  maintainability-focused prompt);
- held-out evaluation (three-change sequences on eval tasks, confidence
  intervals by resampling task families);
- the comment ablation (`editor.view_transform: strip_comments`) and the
  size-matched subset;
- a config for the real models on the RTX 5090 (Qwen2.5-Coder-7B writer,
  14B editor);
- the 60 real tasks, and a CI workflow.


