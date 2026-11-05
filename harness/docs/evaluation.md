# Writer evaluation and comparison

## Purpose and first-version plan

The project proposal, pages 2–4, requires matched held-out comparisons of
the original writer, the later-edit-trained writer, and the prompt,
correctness-only, and static-ranking baselines. It also requires initial
correctness, consecutive change completion, whole-sequence success,
regressions, token/time accounting, and uncertainty by task family.

This addition builds on the existing task registry, collector, fixed editor,
resource-limited evaluator, content-addressed store, and consecutive-change
scorer. It does not replace those components or change their scoring rules.
The current base is commit `6edc355` (including the header-only CI fix).
The README records changes from the proposal: 16 training writer samples,
an 8-program training cap, and the RTX 5070/Ollama configuration. Evaluation
must not select the best of those training samples: each configured writer
seed gets one fresh initial program per task.

Implementation milestones, each saved as a meaningful local commit:

1. Specify the evaluation contract and preservation boundaries (this plan).
2. Implement read-only exports and validated outcome records with tests.
3. Implement family-level metrics, paired bootstrap comparisons, and reports.
4. Add a strict evaluation plan/CLI that reuses collection in separate stores;
   validate its matched settings, dry-run, and zero-inference reporting/resume.
5. Complete fixture integration, user instructions, and regression checks.

No commits will be pushed during implementation. No training, model downloads,
paid API calls, or real-model experiments are needed to validate this version.
Account usage is observed at milestones; approximately 60% should remain,
and unused allowance is not a target to consume.

## Scientific and preservation contract

- Keep every existing task byte, prompt, editor protocol, collection key,
  saved score, and original run unchanged. The new tool uses new output paths.
- Default to eval tasks; development runs and deterministic fixtures must be
  explicitly labeled and must not be represented as held-out evidence.
- Compare matching task versions, sequences, generation seeds, fixed editor,
  inference budgets, and sandbox settings/image. Writer checkpoints and a
  baseline's initial prompt may differ. Do not silently pool different trained
  checkpoints as independent task families.
- One writer sample per task/seed, with no regeneration of an initially wrong
  answer. Initial failures contribute zero to all-generated completion rates;
  also report the initially correct subset separately.
- Reuse the existing rule: score consecutive successful changes until the first
  failure. Later steps are not reached. Missing or infrastructure-interrupted
  work is unresolved, not a model failure or a successful partial trajectory.
- Report coverage and abstain from a complete primary estimate when scheduled
  outcomes are unresolved. Never turn passed-test counts into partial credit.
- Regression rates use behaviorally evaluated reached steps, with their
  denominator explicit. Budget stops have no private evaluation in the current
  collector; do not describe their regression status as known.
- Read saved databases without Store's writable initialization. Exports and
  reports must work without a model server, Docker, training artifacts, or
  credentials, and must not mutate the source database or blobs.
- Bootstrap task families, not editing attempts. Paired comparisons resample
  the same families for both methods. Intervals are exploratory; one family
  cannot provide a family-bootstrap interval.
- Preserve unknown costs. Existing editor token fields may contain fallback
  estimates; describe them as recorded counts, not guaranteed provider usage.
  Latency and source size do not establish maintainability.
- Fake-model/hand-authored fixtures are software validation only. No synthetic
  improvement is experimental evidence that training works.

## Boundaries of the first version

The tool will compare any separately served writer checkpoints. It does not
train the proposed baselines, merge/quantize adapters, or claim that an adapter
exists. Each trained seed can be registered as a separate method until a
separately specified cross-training-seed analysis is available. Comment
stripping, size matching, and a second editor are separate proposal deliverables;
they must not silently change the collection editor or its cached results here.

The original implementation cannot certify arbitrary external API billing.
Real execution in this version will require an explicit run option and local
loopback model endpoints; dry-run and saved-only analysis need no inference.

Usage instructions and validated examples will be completed with the CLI.
