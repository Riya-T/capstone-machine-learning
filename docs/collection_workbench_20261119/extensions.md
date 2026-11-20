# Investigation extensions

The collection workbench now helps investigate the results as well as show
them. It is an extension of the earlier evaluator: native collection records
feed its existing human-review and checkpoint-summary engines. It does not
replace the team's collection, scoring or training pipeline.

## What you can do now

**Inspect failures with the saved code.** Build a review pack from a saved
comparison, optionally supplying the original stores for source previews.
It lists initial failures and each trajectory's first terminal editing stop.
Missing samples, unfinished edits and unselected parents go into a separate
ledger. A missing checkpoint never becomes a made-up code failure.

Each case has a stable ID, parent and edited-source hashes, sample indices,
recorded test counts and stop information. Complete available previews get
a bounded display diff. Missing or truncated sources stay visibly incomplete;
the tool does not reconstruct a program or apply a patch.

**Keep human explanations separate from scores.** Copy the annotation CSV,
record a reviewer, category, confidence and supporting evidence, then compile
one or more reviewers' files. The summary retains every reviewer, unresolved
cases and disagreements. A reviewer marking a cause verified must cite
evidence, but the tool does not verify that causal claim. Evidence references
are text, never files or commands for the tool to execute. Training labels
remain unset.

**Compare the observed training checkpoints.** Summarize methods grouped by
training procedure and seed on a fixed task population. Individual results,
worse checkpoints, initial correctness and selected editing completion remain
visible. A supplied expected-seed roster can detect a missing or unexpected
checkpoint and block the affected aggregate. It is a historical declaration,
not proof the roster was chosen before seeing results.

Checkpoint ranges describe the supplied checkpoints. Family resampling does
not estimate variation across future training seeds. The summary never turns
two training seeds into two independent task samples, picks the best seed or
assigns a winner automatically.

**Share and verify the investigation.** Each derived bundle includes the
source comparison snapshot needed to recompute it. Compiled reviews archive
the exact annotation inputs, without their original local filenames. A
recipient can verify a bundle without the original database, annotation file,
model server or source-report directory. Checksums and recomputation detect
inconsistency; they cannot authenticate a fabricated original store.

## Try it without a model

From `harness/`:

```bash
uv run python examples/collection_workbench.py --out runs/investigation-demo --investigate
uv run python -m harness collection-workbench verify --report runs/investigation-demo/checkpoints
uv run python -m harness collection-workbench verify --report runs/investigation-demo/disagreement-demo
```

Open the HTML files printed by the walkthrough. Everything in this example,
including the checkpoint tags and reviewer disagreement, is an authored
synthetic fixture. It is not new evidence about a model or training run.

The [usage guide](../../harness/docs/collection-workbench.md) gives commands
for real saved collections, explicit store mappings, annotation compilation
and expected-seed coverage.

## What changed in existing code

Three existing evaluation modules now share small helpers with the adapter:
`evaluation/review.py`, `evaluation/seeds.py` and `evaluation/artifacts.py`.
The old public command interfaces and default analysis remain compatible.
Native review pages receive their own source/diff details; old review pages
retain their prior bytes. A training-purpose label was added. The new
workbench workflow also exercises the legacy review and seed tests on Linux.

The task tree, task hashes, prompts, published results, training data, models,
training scripts, collector, scorer, sandbox, lockfile and original CI
workflow remain identical to the reviewed main commit. The original
validation receipt is retained unchanged. No teammate needs to rerun an
experiment to adopt these reporting features.

## Validation and limits

| Check | Observed result |
|---|---|
| Native Windows workbench | 91 passed, one unprivileged symlink-creation skip |
| Linux workbench plus legacy review/seed tests | 110 passed, two Windows-only skips |
| Real Docker checks | Both native and original evaluator mock-collection checks passed |
| Full Linux CPU suite before final display polish | 4,437 passed; the same 42 upstream header failures; 13 skips |
| Final display refinement | 37 affected Windows tests passed; complete Linux targeted suite rechecked |
| Legacy review compatibility | Old pack and compiled files are byte-identical to saved prior-code outputs |
| Legacy seed defaults | Same analysis as the trusted prior repository implementation on the compatibility fixture |
| Earlier native report | Verifies under current code; all ten saved files unchanged |
| Browser inspection | Checkpoint, review and disagreement views rendered; long digest layout corrected |

The full suite is not green: the 42 existing missing-Usage-header failures
also occur on unchanged main. This contribution neither edits those task
inputs nor suppresses their check. Docker uses deterministic mock replies
and actual behavioral evaluation, not an experimental model.

Two local validation launch issues were retained separately: a Linux check
initially imported the installed older checkout because its source path was
omitted, and the unmodified legacy publisher hit the already-known Windows
hard-link restriction. The intended Linux source-path run and legacy Linux
comparison passed. These were test-launch/platform issues, not scored
experimental failures. The native Windows publisher remains independently
tested and does not inherit that hard-link requirement.

The [extension receipt](extensions_validation.json) records tested source
hashes, JUnit hashes, compatibility checks and preservation checks. Raw logs,
browser profiles, synthetic stores and source-preview bundles remain in the
separate local validation namespace, outside the proposed Git contribution.

Real team stores and adapters are still unavailable here. This is working,
validated investigation software, not a raw-data replication of the team's
reported improvement. Its next practical use is on the machine holding those
saved stores. No generation, retraining, new preference labels or push was
performed for this extension.
