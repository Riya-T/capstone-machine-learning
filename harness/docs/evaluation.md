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

## Try the report now, without models or Docker

From `harness/`, using the existing Python environment:

```bash
uv run python -m harness evaluation-report \
  --input fixtures/evaluation/fixture_original.json fixtures/evaluation/fixture_candidate.json \
  --reference fixture_original --out runs/evaluation-demo
```

On PowerShell, put that command on one line instead of using Bash backslashes.
These two inputs are hand-authored fixtures. Their rates are known software-test
answers, not measured original/trained model performance. The report is labeled
SYNTHETIC FIXTURE. The point is to demonstrate the complete reporting workflow.

Outputs:

- `report.md`: readable method comparison, paired difference, interval, costs and limits.
- `comparison.json`: all metrics, family values, provenance, and input records.
- `summary.csv`: one method/metric row, including coverage and interval bounds.
- `trajectories.csv`: each scheduled sequence/repetition, including initial failures
  and unresolved outcomes. Steps after a failure are not fabricated.

Identical output can be replayed; differing existing reports are never overwritten.
Choose a new output directory when changing the inputs or analysis options.

## Preview and run a matched comparison

```bash
uv run python -m harness evaluate --plan configs/evaluation.example.yaml
# Only after a trained writer is locally served and its placeholder is replaced:
uv run python -m harness evaluate --plan configs/evaluation.example.yaml --run
# Rebuild exports/reports from this plan's saved jobs, no models or containers:
uv run python -m harness evaluate --plan configs/evaluation.example.yaml --export-only
```

The first command is a dry-run, not inference. The example uses the existing
16 eval tasks and 7B-writer/14B-editor configuration. The trained writer name is
explicitly a placeholder; `--run` rejects it. Add other controls or separately
trained seeds as more method/config entries, and choose the reference method.
The tool does not train or download any checkpoint. Use immutable/pinned model
names and record the actual server context/quantization separately: the existing
collector records a model tag, not a resolved weight digest.

An evaluation plan is a distinct YAML schema, not a `collect --config` file.
Relative config/output paths resolve from the plan directory. Method configurations
use the existing collection schema and `extends` rules. The tool explicitly forces
one writer sample and one retained program, rather than selecting a successful
answer from the training collection's 16 attempts. It keeps the supplied inference
settings and editor, and uses each declared generation seed in its own store.
Training checkpoint seeds should be separate named methods; generation seeds are
not a replacement for training seeds.

The preview lists tasks, namespaces, and logical upper bounds on writer calls,
editing checkpoints, editor generations and output tokens. Calls often stop earlier
after initial/step failures. The bounds exclude operational HTTP retries in the
existing backend. Plan caps can be tightened before execution. No remote non-loopback
model endpoint is permitted in this first version.

Every real job reuses `collection.collect` and the existing Linux container evaluator.
No generated implementation executes on the host. A consistent read-only database
snapshot produces the evaluation export; opening it does not initialize/migrate the
source store. Writer candidates, checks, model answers, and checkpoints retain their
existing keys and formats. No original store is moved or converted.

## Resume and provenance

The output tree is `<output_dir>/<plan-name>/<input-fingerprint>/`:

```text
evaluation.lock.json       source/config/task fingerprints and resolved image id
stores/<method>/<seed>/    new normal collector stores and original raw artifacts
exports/                  content-addressed evaluation snapshots
reports/                  content-addressed report directories
```

The controller is exclusive across processes. It locks the sandbox image before
inference and checks it across methods. Completed jobs have a verified dataset hash
and resume without constructing a runner, contacting a model, or adding a new run.
Interrupted jobs use the collector's existing resume/cache behavior. Normal code or
budget failures are terminal, not regenerated. Infrastructure failures remain
unresolved and follow the collector's explicit next-run retry behavior.

`--export-only` cannot create a new experiment. It needs a prior lock, but no
Docker daemon or model server. Standalone `evaluation-report` needs only exported
JSON and the lightweight package dependencies. An incomplete report returns unknown
primary estimates, preserves diagnostic coverage, and does not rank missing trials
as zero. An unfinished evaluation command exits 3; configuration/input errors exit 2.
An interrupted command can still be exported with `--export-only`.

Changing source/config/task fingerprints creates a new namespace. To report a
historical store, keep its original inputs/checkout or use its exported JSON.
Do not edit fingerprints to make old scores match a changed task. Previous
snapshots and reports are retained; output filenames never replace their inputs.

## Metrics and uncertainty

The main score is the fraction of requested changes completed consecutively,
using the existing scorer. Initial failures have zero completion on each planned
sequence, but no fabricated editing failures. The initially passing subset is also
reported; it can contain different populations for different writers.

Each family contributes equally. Seeds/tasks within a family are averaged before
family-level inference. Reached-step regression and new-feature failure rates use
only recorded steps that actually received private evaluation; within each family
the denominator is its number of such steps. Budget stops without private testing
are recorded separately. Counts and the original categories remain visible.

Default uncertainty is a reproducible 2,000-draw, 95% percentile bootstrap over task
families. Comparisons resample paired family differences, never individual editing
attempts. Reported differences are absolute rates: 0.10 means 10 percentage
points, not a 10% relative gain. One family has no interval. Conditional comparisons use common applicable
families and must not be read as population-wide causal effects. No p-values,
preference labels, statistical-proof claims, or automatic training recommendation
are generated. All estimates are exploratory at this project's sample size.

Recorded token/time totals show missing fields and preserve the collector's caveats:
editor tokens may contain fallback estimates, and wall time includes latency and
execution. Reporting a complete-case diagnostic does not make unresolved primary
results complete. Passing the tests is not proof of every written requirement.

## Validation and remaining limits

```bash
uv run pytest tests/evaluation -rs
uv run pytest tests/evaluation/test_docker.py --slow -rs
```

Tests include hand-calculated rates, initial failures, missing/infrastructure/budget
outcomes, related tasks grouped as one family, reproducible paired intervals,
read-only SQLite/WAL export, bad records, strict matched-plan checks, output
preservation, real collector integration with a fake evaluator, interrupted resume,
and completed zero-inference replay. The optional Docker smoke uses the real sandbox
with mock/reference code; it is software validation, not model evidence.

No real model comparison has been run for this software change. The first version
still needs Linux/Docker execution validation where that runtime is available.
Graphical plots, comment-density/stripping and size matching, inference serving of
trained adapters, baseline training, and hierarchical pooling across trained seeds
are follow-up work, not silently supplied by these fixtures.

## First-version implementation receipt (2026-11-05)

- Local validation: 1,537 relevant CPU/header checks passed. Four tests were
  excluded: two pre-existing Windows newline/symlink restrictions and two
  Docker/slow runtime tests. The optional real Docker smoke has not run here;
  no Docker CLI or installed WSL distribution is available. No system runtime
  was installed to work around that limitation.
- The report CLI was executed on the committed, explicitly synthetic fixtures
  and produced all four output formats. No real model or training call ran.
- Original task definitions, prompts, collector/editor/scorer, schema, sandbox,
  model settings and old result directories are unchanged by this feature.
- Existing Windows checkout caveat: task/source hashes cover raw bytes. The
  earlier header push/main checkout produced CRLF in its 12 meeting_rooms
  files on this machine. Those files are not edited here. Real experiments
  should retain their original LF/Linux checkout; use exported JSON for
  portable saved-only reporting. This tool does not normalize old hashes
  or migrate saved scores.

This receipt describes software validation, not evidence that training improves
modification outcomes. Cross-training-seed pooling, plots and proposal ablations
remain explicit follow-up work.
