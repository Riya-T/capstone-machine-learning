# Code units and their tests

Each code unit of the pilot pipeline, what it does, and where it is tested.
This table is updated at the end of every build stage. Paths are relative to
`pilot/`. Run every test from `pilot/` with `uv run pytest -rs`; `-rs` lists
each skipped test and the reason.

## Pipeline modules (`src/pipeline/`)

| Unit | Description | Unit tests | Stage |
|---|---|---|---|
| `config.py` | Loads experiment YAML (with `extends`) into frozen, strictly validated settings, and hashes them for keying results. | `tests/test_config.py` | (a) done |
| `registry.py` | Loads and checks task directories (splits, sequences, references, test sets, leak checks) and builds the writer prompt from writer-visible files only. | `tests/test_registry.py` | (b) done |
| `backends.py` | One model interface, `generate(prompt) -> text`: an OpenAI-compatible HTTP backend, a deterministic mock, a replaying call cache, and seed derivation. | `tests/test_backends.py` | (c) done |
| `store.py` | SQLite results store plus content-addressed program blobs: run logging (git commit, config), write-once records, resume points, result keys, and the model-call cache. | `tests/test_store.py` | (d) done |
| `parser.py` | Turns a model answer into program files; strict about labels, paths, duplicates and ambiguity, and reports truncation and malformed output separately. | `tests/test_parser.py` | (e) done |
| `runner.py` | Runs programs and tests in an isolated Docker container (no network, read-only, memory, CPU, process, file-size and time limits) and always cleans up. | `tests/test_runner.py` (marked `docker`) | (f) done |
| `evaluator.py` | Runs a program against a task's test categories (initial, public, new-feature, existing) and validates task references and planted bugs. | `tests/test_evaluator.py` | (g) planned |
| `scorer.py` | Trial scores, preference pairs under the configured rules and pairing modes, and exclusion counts. | `tests/test_scorer.py` | (h) planned |
| `editor.py` | The editor's turn loop over `generate()` (provisional, pending team sign-off). | `tests/test_editor.py` | planned |
| `collect.py`, `__main__.py` | Orchestration: writer sampling, initial checks, editing trials, resume. | `tests/integration/` (end-to-end) | planned |

## Data, prompts and environment

| Unit | Description | Tests |
|---|---|---|
| `tasks/record_store/` | Pilot task: spec, 3 changes, 2 sequences, 5 reference solutions, 5 planted bugs. | `tests/test_registry.py` (structure, leaks); evaluator tests in stage (g) (behavior) |
| `prompts/writer_v1.md` | Writer prompt template (`$entry_files`, `$spec`, `$public_checks`). | `tests/test_registry.py` |
| `sandbox/Dockerfile` | Sandbox image: Python 3.11 pinned by digest, with the pytest and Hypothesis versions from `uv.lock`. | `tests/test_runner.py` |
| `fixtures/mock/` | Mock writer and editor responses for the deterministic backend. | `tests/test_backends.py`, `tests/integration/test_writer_replay.py` |
| `configs/` | `base.yaml` with `pilot_mock.yaml` and `pilot_local.yaml` variants. | `tests/test_config.py` (committed configs load) |

## Integration tests (`tests/integration/`)

| Test file | What it exercises | Marker |
|---|---|---|
| `test_writer_replay.py` | registry → writer prompt → `CachedBackend(MockBackend)` → parser → store; replay with zero model calls, in memory and after closing and reopening SQLite. | none |
| `test_local_model.py` | The real writer from `configs/pilot_local.yaml` follows the output format. | `local_model` (run with `--local-model`) |

## Shared test support

| File | Purpose |
|---|---|
| `tests/conftest.py` | `--local-model` option; skips `docker` tests when no daemon answers and `local_model` tests unless asked. |
| `tests/helpers.py` | Builds valid config files for tests. |
| `tests/data/` | Real model output used as a parser fixture. |
