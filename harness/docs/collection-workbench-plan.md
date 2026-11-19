# Collection results workbench

The history-suite results now include two DPO+NLL training seeds and a
correctness-only control. The existing matched evaluator deliberately uses
one unselected writer sample per task. The team's actual collection runs
instead generate 16 samples and edit up to eight distinct passing programs.
They need a separate reporting path; neither population should be silently
converted into the other.

## Scope

1. Export native collection stores through a consistent, read-only SQLite
   snapshot, using the current config, task versions and explicit image ID.
   Never initialize a Store, start Docker or contact a model. Keep every
   scheduled sample, duplicates, caps, missing checks and unfinished trials.
2. Validate portable exports, including parent identity, sample order,
   selection, stop-at-first-failure and resource records. Reject inconsistent
   evidence; do not repair it or adopt a different cache key automatically.
3. Produce a self-contained comparison bundle with JSON, CSV and readable
   HTML/Markdown. Distinguish initial correctness, selected-program editing,
   exact all-sample outcomes when identifiable, and bounds otherwise. Show
   every cohort exclusion and exploratory family-level uncertainty.
4. Record historical costs once per sampled writer answer and once per
   unique edited parent. Missing usage stays missing. Do not interpret cost
   or static descriptions as maintainability.
5. Exercise the complete export/report/verification flow on labeled fixtures,
   including failures, duplicates, selection caps and interrupted work.
   Add a ready-to-edit history-suite manifest, documentation and meaningful
   regression tests. Check that source stores and all existing task hashes
   remain unchanged. Commit logical milestones locally; do not push.

## Boundaries

No training, model generation, model download or changes to task contracts,
training data, collector behavior or prior scores. The workbench does not
retroactively freeze an experiment or produce preference labels. Published
summary pages cannot reconstruct missing raw stores. A fixture walkthrough
validates software, not the history-suite result. Generated source is
described without executing it and is not included in portable exports.

Start from team revision `ebed082` (November 19). Keep this work on
`jtsno/results-workbench-20261119`, separate from prior research branches.
Preserve the existing 30% allowance reserve; spend only what useful work
requires. A final review must cover read-only behavior, report integrity,
population accounting, tests and the exact push diff.
