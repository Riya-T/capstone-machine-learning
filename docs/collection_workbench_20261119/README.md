# Push review: collection results workbench

This records the initial version at `dad0165`. The
[investigation extensions](extensions.md) add failure review and checkpoint
summaries with separate validation evidence; the receipt below is historical.

**A useful standalone software contribution is ready for branch review.**
It connects the team's actual multi-sample collection runs to portable,
auditable reporting. No new experiment, training result or preference label
is claimed. Nothing has been pushed.

## Why this contribution now

The November 19 team results are materially different from the earlier
null results: the history-suite DPO+NLL writer improves conditional editing
with two training seeds, while initial correctness falls. Those are the
team's reported results, not a new raw-data replication by this contribution.
See [the current results](../../harness/results/hist2_eval.md).

The existing matched evaluator intentionally starts from one unselected
sample per task. The actual history collections instead draw 16 and edit
up to eight distinct passing parents. This contribution adds the missing
saved-store bridge and keeps that selection visible. It supports presenting
and auditing the current work without another round of model generation.

## What would be pushed

- `harness/src/harness/workbench/`: native read-only export, validation,
  family-weighted comparisons, portable ledgers, offline HTML/Markdown,
  missing-data bounds and immutable report verification.
- `harness/tests/workbench/`: manually checked denominator examples,
  deliberately inconsistent controls, real SQLite/WAL reads, platform
  publication/race controls and a real mock-collector Docker smoke.
- An executable synthetic walkthrough, a four-checkpoint history-suite
  input manifest, and [plain setup/use instructions](../../harness/docs/collection-workbench.md).
- A separate Linux/Windows workbench CI workflow. The original full-project
  workflow stays enabled and unchanged.
- Seven additive lines in the main command dispatcher and five in the root
  README. These expose and link the new optional command.

Everything else is in new files. The original task tree, prompts, data,
published results, report text, training code, models, collector, scorer,
sandbox, dependency lock and original CI workflow are byte-identical Git
objects to base `ebed08262e7299ba31c3893319f1fc12a15b0665`. No teammate
needs to rerun an experiment to adopt this tool. Source exports require
the actual saved store and matching config/task/image identities.

Earlier local research branches are not included in this branch. Raw model
responses, generated sources, local databases, environment directories,
browser profiles and machine-specific logs are not proposed for publication.
No existing branch or remote history was rewritten.

## Validation

| Check | Observed result |
|---|---|
| Linux workbench checks | 51 passed; 2 native-Windows controls skipped |
| Native Windows workbench checks | 52 passed; symlink-creation check skipped without privilege |
| Real Docker mock collection | Passed; private behavioral scoring, duplicate accounting and zero-call completed resume |
| Full Linux CPU suite | 4,393 passed, 42 existing header failures, 13 optional/platform skips, 80 deselected |
| Untouched upstream comparison | Exactly the same 42 failure IDs; no new failures |
| Lint | All contribution Python files and dispatcher pass Ruff |
| Browser | Final synthetic report rendered in a fresh headless Edge profile and inspected |
| Report integrity | Checksums and recomputed analysis agree; altered/rehashed false analyses are rejected |
| Preservation | Protected Git trees match base; real smoke leaves durable database, blobs and run files unchanged |

The new Windows publisher avoids a managed environment's hard-link denial
using non-overwriting rename. It was tested natively, including a competing
publisher, and is isolated from the older evaluator's publisher. The first
failed Windows run and the earlier Docker assertion about SQLite sidecars
are retained in local logs; their fixes did not change scores.

SQLite's `mode=ro` connection may create an empty WAL and shared-memory
bookkeeping file. The durable database and source blobs are unchanged.
Use a closed copy when filesystem-level immutability is needed. This limit
is explicit in the usage guide and real smoke test.

The full-suite baseline is **not green**. Forty-two existing reference/bug
modules lack a Usage example. They fail on untouched main too. This branch
does not relax that check or edit benchmark inputs to hide it. A coordinated
documentation fix can be handled separately, with its task-fingerprint
effects reviewed. The separate workbench workflow does not suppress the
original check. No remote CI run is claimed before a push.

The JSON [validation receipt](validation.json) lists the baseline failures,
protected object IDs, tested source hashes and local JUnit hashes. Logs and
the labeled demo are retained outside Git in the local
`collection_workbench_20261119/` namespace. Torch-dependent training checks
were skipped, and no training validation is claimed.

## Limits and next use

The team's actual training/evaluation SQLite stores and adapters are not
published in the repository. This tool was validated against authored
native fixtures and an actual mock collection, not reconstructed real
outcomes invented from rounded Markdown tables. The first useful deployment
is to run the four-checkpoint manifest on the machine holding those stores.
No model server is needed.

The workbench's completeness rules, population accounting and bootstrap
are separately labeled diagnostics. Historical scripts remain the exact
reproduction route for their own published tables. Unknown over-cap
programs cannot become scored successes or failures, and a pass-rate-times-
selected-score product is not silently called exact per-sample performance.

There are no automated preference labels or causal maintainability claims.
Repeated edits, test cases, duplicate answers and two supplied training
seeds do not become independent task-level evidence. Integrity verification
cannot authenticate a forged original store.

In class, the contribution can be described simply:

> I added a tool that reads our saved collection runs and compares the
> original writer, correctness-only control and trained checkpoints in an
> offline dashboard. It shows correctness, later editing, costs and missing
> results, and verifies the reports without running the models again.

All development commits are local on `jtsno/results-workbench-20261119`.
The working branch is separate from main. Pushing it remains the user's
decision; no push, pull request or message to teammates was sent.
