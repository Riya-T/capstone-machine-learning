# Follow-up: from reporting to investigation

The earlier evaluator remains the tool for planned one-sample experiments.
The collection workbench is its saved-run bridge for multi-sample collections.
This follow-up adds capabilities needed to investigate the actual results,
while sharing the earlier tool's validation and statistical code.

1. Extract pure human-review rendering and annotation functions from the
   existing evaluator without changing its public commands or output bytes.
   Add native collection cases for unique failing parents, parse failures,
   and terminal editing stops. Missing work is an inventory, not a failure.
2. Allow optional, bounded before/after source previews from explicitly
   supplied stores. Never execute sources or follow report-embedded paths.
   Leave every cause unreviewed until a person records evidence. Preserve
   multiple reviewers and disagreements without replacing original scores.
3. Reuse the existing checkpoint-summary engine for native collection
   exports. Keep seeds distinct, use a fixed task population, retain adverse
   and unresolved checkpoints, and disclose that family intervals do not
   measure training-seed uncertainty. Check a supplied expected-seed roster
   without falsely calling a historical declaration preregistration.
4. Publish extensions as separate immutable, self-contained bundles with
   source snapshots. Verification must check hashes and recompute derived
   case identities, summaries and annotation results without inference.
5. Extend the walkthrough, documentation and negative controls. Exercise
   old and new commands on Linux and Windows, run the real mock-collector
   smoke, and recheck protected benchmark/task hashes. Commit logical
   milestones locally; do not push or start experiments/training.

Historical reports, receipts, data, reference code and experimental scores
remain unchanged. New validation evidence has its own namespace. These
features produce investigation material, never automatic preference labels.
