# Evaluation inspection and verification features

These additions make saved comparisons easier to inspect and share. They do not
change the scorer, test suites, editor, original configuration or training pipeline.

## Open the offline dashboard

From `harness/`:

```bash
uv run python -m harness evaluation-report --input fixtures/evaluation/fixture_original.json fixtures/evaluation/fixture_candidate.json --reference fixture_original --out runs/evaluation-features-demo
uv run python -m harness evaluation-verify --report runs/evaluation-features-demo
```

Open `runs/evaluation-features-demo/report.html` in a browser. No web server,
Internet connection or account is needed. This example is prominently labeled
**synthetic software-validation data**, not actual original/trained model results.
Choose a new output directory for different data or report versions.

The dashboard contains overall scores, paired completion differences and their
exploratory family-bootstrap intervals, and individual checkpoint/first-stop tables.
Filter the latter by writer method or outcome, or search task/family/change/reason.
Filters never alter the summary scores or intervals. All rows remain readable when
JavaScript is disabled. Links lead to the adjacent CSV, JSON and Markdown files.
The HTML does not embed raw source, full configurations or local provenance paths.
The separate JSON retains fuller metadata; inspect it before sharing externally.

## Inspect where attempts stopped

- `checkpoints.csv` contains every planned change. Recorded success, feature
  failure, preserved-behavior failure, budget stop, infrastructure error, missing
  work, and not-reached work are distinct. Recorded source hashes, test counts,
  tool-call counts and costs remain available; unknown values stay empty.
- `failures.csv` contains one initial non-pass per initial sample, or the first
  non-success per editing trajectory. An initial failure is not repeated as an
  editing failure for every scheduled change.

A missing checkpoint is not an independently failed model attempt. After a stop,
later checkpoints are explicitly not reached. Infrastructure/budget stops without
behavioral evaluation do not acquire invented regression labels. End reasons are
stored metadata, not an automated explanation of executable failure causes.

## Verify a shared report without inference

`evaluation-verify` checks the manifest, every declared checksum, and safe regular
artifact paths. It recomputes the stored analysis from the embedded outcome records
and checks the claimed scores, coverage, counts, costs, trajectory records and
family results. It writes nothing, contacts no models, and reruns no private tests.

An altered file fails verification. An altered aggregate score still fails after
its checksum is updated, because the analysis no longer matches its outcome records.
This is a local consistency check, not authentication: someone who changes both
the outcome records and the derived analysis can produce a consistent false claim.
Keep the original raw evidence and experimental provenance.

Manifest-bearing older bundles may omit newly added outputs. A report with no
manifest cannot be certified complete. Use `--checksums-only` explicitly when a
historical analysis intentionally differs from the currently installed version;
the receipt reports that analysis was not recomputed. Errors return exit code 2.

## Implementation and validation receipt (2026-11-05)

Working increments were committed separately, locally only:

1. `c8c600d`: checkpoint accounting and first-stop diagnostic exports.
2. `aac3fd1`: read-only report verification and analysis recomputation.
3. `9eb44d4`: self-contained HTML dashboard and display filters.

The relevant broad suite passed **1,614 tests**, with the same four documented
exclusions as the prior audit: two existing Windows fixture/symlink restrictions
and two container/slow tests. Ruff and whitespace checks passed. The new modules
parse with Python 3.11 grammar; runtime tests used Windows Python 3.12.14.

Specific controls cover missing versus not-reached steps, initial and editing
failures, budget/infrastructure stops, source lineage, damaged bundles, unsafe
manifest paths, linked artifacts, modified scores with recomputed checksums,
legacy manifests, HTML injection and lack of external assets. Installed Node
ran the display-filter script against mock elements, including combined filters,
case-insensitive search and reset. Node is not a tool runtime dependency; this
optional test skips when Node is unavailable.

The browser tool rejected a local-file preview under its security policy. No
alternate browser route was used. Rendered visual/browser inspection remains
unverified; HTML structure, escaping, filter logic and file integration were
tested locally. The existing real Docker smoke also remains pending because
Docker/WSL is unavailable on this machine.

The new ten-file demo and previous seven-file audited report both verify without
writes. Replaying the new report produces identical bytes. All 60 task hashes,
original prompts/core/settings and prior results are preserved. No experimental
inference, downloads or training ran. Source changes create a new evaluation
fingerprint as designed; use exported JSON or the pinned original checkout for
historical runs, without rewriting their locks or scores.

Local command/log/XML, replay and preservation receipts are in
`../evaluation_features/` relative to the checkout. Observed weekly usage remained
1% used / 99% remaining at the account's whole-percentage resolution. Nothing
was pushed. See [the main guide](evaluation.md) for the complete run protocol.
