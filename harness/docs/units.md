# Code units and their tests

Each code unit of the harness, what it does, and where it is tested. Paths
are relative to `harness/`. Run every test from `harness/` with `uv run pytest -rs`; `-rs`
lists each skipped test and the reason. `--slow` adds the slow tests (full
collection, task validation, stress tests).

## Layout

```
harness/
  src/harness/           the package
    config.py              shared: settings
    registry.py            shared: tasks and writer prompts
    store.py               shared: results store
    models/                talking to models (backends, parser)
    sandbox/               running generated code (runner, evaluator)
    collection/            preference-data collection (editor, collect, scorer)
  tests/                 mirrors src/harness/; integration/ for multi-module tests
    data/tasks/            the example task the tests run on
  configs/               base.yaml and variants (mock.yaml)
  prompts/               writer and editor prompt templates
  tasks/<task_id>/       one directory per real task (none yet); its split is in task.yaml
  fixtures/mock/         mock writer and editor answers
  docker/sandbox/        sandbox image
  docs/                  this file
  runs/                  results store (gitignored)
```

Training (DPO, baselines) and held-out evaluation will go in new
subpackages next to `collection/`.

## Shared modules (`src/harness/`)

| Unit | Description | Unit tests |
|---|---|---|
| `config.py` | Loads experiment YAML (with `extends`) into frozen, strictly validated settings, and hashes them for keying results. | `tests/test_config.py` |
| `registry.py` | Loads and checks task directories (splits, sequences, references, test sets, leak checks) and builds the writer prompt from writer-visible files only. | `tests/test_registry.py` |
| `store.py` | SQLite results store (`harness.sqlite`) plus content-addressed program blobs: run logging (git commit, config), write-once records, resume points, result keys, and the model-call cache. | `tests/test_store.py` |
| `__main__.py` | Command line: `collect`, `validate-tasks`, `report` (all `--config`), with progress logging. | `tests/integration/test_end_to_end.py` |

## Models (`src/harness/models/`)

| Unit | Description | Unit tests |
|---|---|---|
| `backends.py` | One model interface, `generate(prompt) -> text`: an OpenAI-compatible HTTP backend, a deterministic mock, a replaying call cache, and seed derivation; calls after the first in a trial get their own seed (`call_seed`). | `tests/models/test_backends.py` |
| `parser.py` | Turns a model answer into program files; strict about labels, paths, duplicates and ambiguity, and reports truncation and malformed output separately. A subset mode and `prose_lines` serve editor replies. | `tests/models/test_parser.py` |

## Sandbox (`src/harness/sandbox/`)

| Unit | Description | Unit tests |
|---|---|---|
| `runner.py` | Runs programs and tests in an isolated Docker container (no network, no image pulls, read-only, memory, CPU, process, file-size and time limits) and always cleans up; OOM is detected from the container's own cgroup counter or Docker's flag, and an unexplained SIGKILL is an infra error. Containers carry the `harness.sandbox` label. | `tests/sandbox/test_runner.py` (marked `docker`) |
| `evaluator.py` | Runs a program against each test category (initial, public, new-feature, existing) in its own sandbox run, reads the JUnit reports, drops superseded tests by exact id, and validates tasks (references pass, planted bugs fail as declared, the program before each change fails its tests). Independent runs go in parallel (`execution.sandbox_workers`). | `tests/sandbox/test_evaluator.py` (mostly `docker`) |

## Collection (`src/harness/collection/`)

| Unit | Description | Unit tests |
|---|---|---|
| `editor.py` | Editor turn loop: a fresh bounded prompt each turn with one-line summaries of the latest `history_turns` turns, full-file replies and `RUN_CHECKS`/`DONE`, cumulative public checks in the sandbox (`checks_passed` once every public check passes), budgets on turns, tokens and wall time. Bad replies, replies that change nothing, and `RUN_CHECKS` on already-checked code are wasted turns (the checks are not rerun), never crashes. `PROTOCOL_VERSION` (3) is part of the editor key. | `tests/collection/test_editor.py` |
| `collect.py` | Collection: writer samples → parse → initial checks → editing trials → store → preference files; resumes at every level, including mid-trial replay from the call cache; `report` rebuilds the files from the store with no model calls; `--until writer\|initial\|edit` stops after a stage. | `tests/collection/test_collect.py`, `tests/integration/test_end_to_end.py` (marked `docker`) |
| `scorer.py` | Trial scores (consecutive changes before the first failure), step and editor endings, `strict` and `weak_dominance` rules under `all_pairs` and `best_vs_worst` pairing, per-task caps, ablations (fewer changes or reps), exclusion counts by reason, preference pairs, report files and `summary.txt`. | `tests/collection/test_scorer.py` |

## Data, prompts and environment

| Unit | Description | Tests |
|---|---|---|
| `tests/data/tasks/record_store/` | Example task the tests run on (not a real task): spec, 3 changes, 2 sequences, 5 reference solutions, 3 planted bugs. Its initial tests skip two spec rules (see `task.yaml`). | `tests/test_registry.py` (structure, leaks); `tests/sandbox/test_evaluator.py::test_record_store_task_is_sound` (behavior) |
| `prompts/writer_v1.md` | Writer prompt template (`$entry_files`, `$spec`, `$public_checks`). | `tests/test_registry.py` |
| `prompts/editor_v2.md` | Editor instructions template (`$request`, `$files`, `$history`, `$feedback`, `$allowed_files`, `$turns_left`). | `tests/collection/test_editor.py` |
| `docker/sandbox/Dockerfile` | Sandbox image `harness-sandbox:py3.11-v1`: Python 3.11 pinned by digest, with the pytest and Hypothesis versions from `uv.lock`. | `tests/sandbox/test_runner.py` |
| `fixtures/mock/` | Mock writer and editor responses for the deterministic backend. | `tests/models/test_backends.py`, `tests/integration/test_writer_replay.py` |
| `configs/` | `base.yaml` and `mock.yaml` (deterministic mock writer and editor on the example task). A real-model config for the 5090 comes later. `execution` holds settings that never affect results. | `tests/test_config.py` (committed configs load) |

## Integration tests (`tests/integration/`)

| Test file | What it exercises | Marker |
|---|---|---|
| `test_writer_replay.py` | registry → writer prompt → `CachedBackend(MockBackend)` → parser → store; replay with zero model calls, in memory and after closing and reopening SQLite. | none |
| `test_end_to_end.py` | Full collection on record_store with the mock writer and editor in the real sandbox: expected scores, one pair (modular over tangled), duplicate excluded; a rerun makes 0 model calls and leaves the store identical; an interrupted trial resumes from the cache; `report` and `validate-tasks` commands. | `docker` |

## Shared test support

| File | Purpose |
|---|---|
| `tests/conftest.py` | `--slow` option; skips `docker` tests when no daemon answers, and `slow` tests unless asked. |
| `tests/helpers.py` | Builds valid config files for tests. |
| `tests/data/` | Test inputs: the example task, and a real model answer for the parser test. pytest doesn't collect them (see `conftest.py`). |
| `tests/test_headers.py` | Enforces the course rule that every source and test file has a header with a Usage section. |
