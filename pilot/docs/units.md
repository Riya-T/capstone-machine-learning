# Code units and their tests

Each code unit of the pilot pipeline, what it does, and where it is tested.
This table is updated at the end of every build stage. Paths are relative to
`pilot/`. Run every test from `pilot/` with `uv run pytest -rs`; `-rs` lists
each skipped test and the reason. `--slow` adds the slow tests (full
collection, task validation, stress tests) and `--local-model` the tests
that call the local model server.

## Pipeline modules (`src/pipeline/`)

| Unit | Description | Unit tests | Stage |
|---|---|---|---|
| `config.py` | Loads experiment YAML (with `extends`) into frozen, strictly validated settings, and hashes them for keying results. | `tests/test_config.py` | (a) done |
| `registry.py` | Loads and checks task directories (splits, sequences, references, test sets, leak checks) and builds the writer prompt from writer-visible files only. | `tests/test_registry.py` | (b) done |
| `backends.py` | One model interface, `generate(prompt) -> text`: an OpenAI-compatible HTTP backend, a deterministic mock, a replaying call cache, and seed derivation. | `tests/test_backends.py` | (c) done |
| `store.py` | SQLite results store plus content-addressed program blobs: run logging (git commit, config), write-once records, resume points, result keys, and the model-call cache. | `tests/test_store.py` | (d) done |
| `parser.py` | Turns a model answer into program files; strict about labels, paths, duplicates and ambiguity, and reports truncation and malformed output separately. A subset mode and `prose_lines` serve editor replies. | `tests/test_parser.py` | (e) done |
| `runner.py` | Runs programs and tests in an isolated Docker container (no network, no image pulls, read-only, memory, CPU, process, file-size and time limits) and always cleans up; OOM is detected from the container's own cgroup counter or Docker's flag (each covers the other's gap), and an unexplained SIGKILL is an infra error. | `tests/test_runner.py` (marked `docker`) | (f) done |
| `evaluator.py` | Runs a program against each test category (initial, public, new-feature, existing) in its own sandbox run, reads the JUnit reports (pytest runs with a wide terminal and short tracebacks so failure causes stay readable), drops superseded tests by exact id, and validates tasks (references pass, planted bugs fail as declared, the program before each change fails its tests). Independent runs go in parallel (`execution.sandbox_workers`). | `tests/test_evaluator.py` (mostly `docker`) | (g) done |
| `scorer.py` | Trial scores (consecutive changes before the first failure; unresolved trials never scored), step endings with `budget_exhausted` split by reason (e.g. `prompt_too_large`), editor endings (`done`, `checks_passed`, `max_turns`, ...), the `strict` and `weak_dominance` rules under `all_pairs` and `best_vs_worst` pairing side by side, per-task caps, ablations (fewer changes or reps), exclusion counts by reason, and the preference pairs and report files; exclusions broken down by parse category/reason and infra cause; pairs carry the model-call keys of their programs; a candidate section (samples, parse failures, distinct and comment/format-normalized distinct programs, initial passes, low-diversity flag) and `summary.txt`. | `tests/test_scorer.py` | (h) done |
| `editor.py` | Provisional editor turn loop (pending team sign-off): a fresh bounded prompt each turn (current request, current files, last feedback), full-file replies and `RUN_CHECKS`/`DONE`, cumulative public checks in the sandbox (the step ends as `checks_passed` once every public check passes), budgets on turns, tokens and wall time; bad replies are wasted turns, never crashes. `PROTOCOL_VERSION` is part of the editor key. | `tests/test_editor.py` | (i) done |
| `collect.py` | Collection: writer samples (one cached backend per sample) → parse → initial checks → editing trials (one cached backend per trial, per-rep seeds) → store → preference files; resumes at every level, including mid-trial replay from the call cache; auto-finished steps are still scored by the hidden tests; `report` rebuilds the files from the store with no model calls; `--until writer|initial|edit` stops after a stage; prints a summary table. | `tests/test_collect.py`, `tests/integration/test_end_to_end.py` (marked `docker`) | (j) done |
| `__main__.py` | Command line: `collect`, `validate-tasks`, `report` (all `--config`), with progress logging. | `tests/integration/test_end_to_end.py` | (j) done |

## Data, prompts and environment

| Unit | Description | Tests |
|---|---|---|
| `tasks/record_store/` | Pilot task: spec, 3 changes, 2 sequences, 5 reference solutions, 5 planted bugs. | `tests/test_registry.py` (structure, leaks); `tests/test_evaluator.py::test_record_store_task_is_sound` (behavior) |
| `prompts/writer_v1.md` | Writer prompt template (`$entry_files`, `$spec`, `$public_checks`). | `tests/test_registry.py` |
| `prompts/editor_v1.md` | Editor instructions template (`$request`, `$files`, `$feedback`, `$allowed_files`, `$turns_left`). | `tests/test_editor.py` |
| `sandbox/Dockerfile` | Sandbox image: Python 3.11 pinned by digest, with the pytest and Hypothesis versions from `uv.lock`. | `tests/test_runner.py` |
| `fixtures/mock/` | Mock writer and editor responses for the deterministic backend. | `tests/test_backends.py`, `tests/integration/test_writer_replay.py` |
| `configs/` | `base.yaml` with `pilot_mock.yaml` and `pilot_local.yaml` (16 samples, 3 reps, local 7B with an 8k context) variants; `execution` holds settings that never affect results (sandbox workers). |
| `ollama/` | Ollama model variant definitions (the 8k-context Qwen2.5-Coder-7B) and how to create them. | — | `tests/test_config.py` (committed configs load) |

## Integration tests (`tests/integration/`)

| Test file | What it exercises | Marker |
|---|---|---|
| `test_writer_replay.py` | registry → writer prompt → `CachedBackend(MockBackend)` → parser → store; replay with zero model calls, in memory and after closing and reopening SQLite. | none |
| `test_local_model.py` | The real writer from `configs/pilot_local.yaml` follows the output format. | `local_model` (run with `--local-model`) |
| `test_end_to_end.py` | Full collection on record_store with the mock writer (modular, tangled, duplicate) and mock editor in the real sandbox: expected scores, one pair (modular over tangled), duplicate excluded; a rerun makes 0 model calls and leaves the store identical; an interrupted trial resumes from the cache; `report` and `validate-tasks` commands. | `docker` |

## Shared test support

| File | Purpose |
|---|---|
| `tests/conftest.py` | `--local-model` and `--slow` options; skips `docker` tests when no daemon answers, and `local_model` and `slow` tests unless asked. |
| `tests/helpers.py` | Builds valid config files for tests. |
| `tests/data/` | Real model output used as a parser fixture. |
| `tests/test_headers.py` | Enforces the course rule that every source and test file has a header with a Usage section. |
