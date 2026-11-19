# Read the results of an existing collection

The collection workbench turns the team's saved runs into a portable report.
It shows initial correctness, later editing, regressions, costs and missing
work together. It does not run models, start Docker, train anything or change
the saved scores.

Use it for collections such as the history suite: 16 writer samples per
task, with up to eight distinct passing programs edited. The existing
[matched evaluator](evaluation.md) still handles the separate experiment
with one unselected sample per task. Neither tool changes the other's
population or schema.

## Try it without any experimental files

From `harness/`, after the normal `uv sync`:

```bash
uv run python examples/collection_workbench.py --out runs/collection-demo
uv run python -m harness collection-workbench verify --report runs/collection-demo/report
```

Open `runs/collection-demo/report/report.html` in a browser. It works
offline and has a searchable task table. JSON, Markdown and CSV files sit
beside it. The example also creates an unfinished report to show how
missing trials are handled. Use a new demo directory each time.

**Every demo result is synthetic.** Native SQLite records and source blobs
are created solely to test the reporting flow. They are not model results,
new training data or evidence that a writer improved.

## Build the history-suite comparison

This command must run where the original `harness.sqlite` and `blobs/`
directories are available. Published Markdown summaries are not enough.

1. Copy `configs/collection.history.example.json` to another file in the
   same directory, for example `configs/collection.history.local.json`.
2. Replace the image placeholder with the sandbox **content ID used by
   those runs**, such as `sha256:` followed by 64 hexadecimal characters.
   Do not guess from a tag. If the original image is still installed,
   `docker image inspect harness-sandbox:py3.11-v1 --format '{{.Id}}'`
   retrieves its current content ID; confirm it is the recorded image.
3. Check the four checkpoint configs and their stores. They are the base,
   correctness-only control, and DPO+NLL seeds 42 and 43. An optional
   `"store": "../runs/rtx5070_pc"` field overrides a checkpoint's store
   root when files have been copied. Paths are relative to the manifest.
4. Run:

```bash
uv run python -m harness collection-workbench build --manifest configs/collection.history.local.json --out runs/history-comparison
uv run python -m harness collection-workbench verify --report runs/history-comparison
```

Share the resulting report directory, not your whole model/store directory.
The report contains outcomes, counts, source hashes and run provenance. It
omits generated code, raw replies, machine hostnames, absolute store paths,
server endpoints and credentials. Review the bundle before sharing: task
names, model tags, run IDs and commit identities are still experiment data.
Configured model tags do not attest the actual weight or adapter files.

The manifest describes a historical analysis. It is not a retroactive
preregistration. This template keeps the training seeds separate; its
intervals condition on these checkpoints and do not estimate variation
across possible training seeds.

These are additional diagnostics, not replacements for the published
tables. Four checkpoints use their common available cohort; a comparison
of only base and seed 43 can retain an extra task. The workbench also
requires complete selected trajectories and uses the evaluator's
family-weighted, interpolated bootstrap. Historical `eval_summary.py` and
`eval_compare.py` remain the exact reproduction route for their published
estimands and intervals. No historical score or script is modified.

## Export on one machine and report on another

Export each checkpoint where its store exists:

```bash
uv run python -m harness collection-workbench export --config configs/rtx5070_hist2_eval.yaml --image-id sha256:YOUR_RECORDED_DIGEST --method base --purpose heldout --out runs/base.collection.json
```

Use the other checkpoints' configs and distinct method IDs for their
exports. Add `--method-group dpo_nll --training-seed 42` or `43` to preserve
training provenance. Then copy only the export JSON files:

```bash
uv run python -m harness collection-workbench compare --input base.collection.json sft.collection.json dpo42.collection.json dpo43.collection.json --reference base --out runs/shared-comparison
uv run python -m harness collection-workbench verify --report runs/shared-comparison
```

Export opens a consistent read-only SQLite snapshot, including committed
WAL records, and verifies referenced content-addressed blobs. It never
initializes a writable `Store`, invokes a sandbox or executes source.
SQLite may use its normal read-lock/WAL bookkeeping while taking the
snapshot; the exporter does not update the saved database records or blobs.
Use a copied, closed store when byte-level filesystem immutability is
required. A corrupt/missing referenced blob is an error, not an invitation
to reconstruct code.

Use the same task files, prompts, config and editor protocol as the source
run, preferably in a Linux checkout. A changed task version, line endings,
prompt, image or config can produce a different cache key. The exporter
does not substitute a nearby key. It leaves missing work visible. It also
checks the original candidate run's generation seed rather than relabeling
cached answers with a new config's seed.

## What the numbers mean

- **Initial pass rate:** every planned writer sample, including invalid
  output. Missing samples/checks and infrastructure errors remain unknown.
- **Selected editing:** unique passing parents in sample order, up to the
  configured cap. Each sequence starts from that parent; scoring uses the
  existing consecutive-success rule and stops at the first failure.
- **Common cohort:** tasks where every supplied checkpoint has a selected
  parent and all its selected trajectories are complete. Every exclusion
  and its reason are listed. This is each writer's own passing population,
  not matched identical parents or a causal design comparison.
- **Exact per-sample completion:** normalized consecutive successes,
  assigning zero to initial failures without inventing editing attempts.
  Duplicate answers reuse their parent's saved outcomes. They do not
  become independent editor trials.
- **Identification bounds:** unedited over-cap parents, unknown selection
  and unfinished trajectories do not receive fabricated outcomes. The
  report lets their normalized scores range from 0 to 1. These bounds
  describe missing evidence; they are not confidence intervals.
- **Pass-rate-times-selected-score proxy:** useful as a description, but
  not generally the exact sample score. Selection and duplicate frequencies
  can change it. The example and tests deliberately demonstrate this.
- **Regressions:** observed `fail_existing` and `fail_both` checkpoints,
  with the number of behaviorally evaluated steps. Later steps after a stop
  stay not reached, rather than becoming additional failures.
- **Costs:** saved writer answers counted once each, selected editor work
  once per unique parent. Missing tokens/time are shown with known subtotals
  and missing counts. Writer calls count saved answers and editor calls use
  recorded counts; transport retries and actual monetary costs are unknown.
  Collector token counts may be estimates. Cached work can be shared
  between methods, so summing method costs is not incremental spending.

Tasks are averaged within family and families equally. Paired intervals
resample families, not tests, samples or editing attempts. One family has
no interval. The JSON also contains leave-one-family-out sensitivity and
full-roster per-sample difference bounds. These are exploratory summaries,
not automatic winner labels or proof of general maintainability.

Missing work blocks the relevant point estimates instead of being dropped
to improve the result. Exit status `3` means the report was saved but the
collection is incomplete. Exit `2` means invalid/incompatible evidence or
a publication error. Successful verification returns `0` even for a
faithfully preserved incomplete report: integrity is not completion.

## Files and checks

`report.html` and `report.md` are the readable views. `comparison.json`
contains all portable source exports and the full analysis. CSV files
provide task, sample, trajectory, checkpoint, resource and paired-difference
tables. `manifest.json` records their SHA256 hashes.

Identical replay is allowed. Different output refuses to overwrite an
existing bundle. Symlink/reparse-point output paths and manifest traversal
are rejected. Verification checks checksums and recomputes the analysis
and reports. It detects inconsistent files, not forged original outcomes.

On Windows the workbench publishes a flushed sibling temporary file using
non-overwriting `os.rename`, avoiding a hard-link permission requirement.
POSIX uses the existing immutable publisher. This follows the documented
[Windows destination-exists behavior](https://docs.python.org/3.11/library/os.html#os.rename).
Neither path uses `os.replace` to overwrite evidence. The existing matched
evaluator's publisher is unchanged.

```bash
uv run pytest tests/workbench -m 'not docker'
uv run pytest tests/workbench/test_docker.py --slow -rs
uv run ruff check src/harness/workbench tests/workbench examples/collection_workbench.py
```

The Docker smoke uses the actual collector with deterministic mock replies
and real public/private tests. It checks duplicate accounting, first-stop
scoring and completed resume without further mock calls. It does not
measure an experimental model. Neither test command requires model weights.
