# Evaluation extensions

Implement these as separate local commits. Preserve primary scores, original
artifacts and frozen experiments. Use saved records and software fixtures only;
never generate missing model outcomes or training labels.

1. Add a preflight command. Default checks are local and read-only. Optional probes
   only GET advertised models from configured loopback servers and inspect Docker;
   they never generate, build images, pull weights or create collection stores.
2. Add size-matched sensitivity analysis for one named method against the reference.
   The caller specifies a physical-line field and relative tolerance before seeing
   outcomes. Keep a whole task family only when every scheduled task/generation-seed
   pair has two initially passing parents, known sizes, and
   `abs(a-b) / max(1,a,b) <= tolerance`. Selection never reads editing success.
   Disclose every exclusion and preserve the original report as primary evidence.
3. Summarize declared training checkpoints. Keep every checkpoint/seed row,
   report adverse/tied/unresolved outcomes, and bootstrap task-family means with
   the observed checkpoint set fixed. Do not claim uncertainty over future training
   seeds or treat checkpoints/repetitions as independent task families.
4. Add human failure review. Immutable case IDs bind annotations to a saved report.
   Optional explicitly supplied stores provide verified source previews, never
   executable code. Keep editable annotations separate from original outcomes.
   Distinguish reviewer hypotheses from reviewer-asserted verified explanations;
   the tool cannot establish causation from an annotation or assign preferences.
5. Export publication figures using an optional Matplotlib dependency. Preserve
   unknown values, label fixtures and development data, show existing family
   uncertainty, and distinguish recorded resource totals from measured efficiency.

Every derived analysis records its rule, source-report hash, populations and
limitations. Publish immutable outputs with checksums and support identical replay.
Validate boundaries with missing, conflicting and deliberately inconsistent data.
Add simple comments explaining the decisions that protect scientific validity.
