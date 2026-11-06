# Coverage and paired comparisons

The evaluator can detect missing work against a roster frozen before inference.
Run these commands from `harness/`:

```powershell
uv run python -m harness evaluation-contract freeze --plan configs/evaluation.proposal.example.yaml --out runs/proposal.contract.json
uv run python -m harness evaluation-contract check --contract runs/proposal.contract.json --input original.json trained.json
uv run python -m harness evaluation-report --contract runs/proposal.contract.json --input original.json trained.json --out runs/contracted-report
```

The example plan contains placeholder model names. Freezing it performs no model
calls or container operations; configure the real planned checkpoints before
freezing a real study. Supply **all** exports when checking or reporting. Missing,
extra, duplicate or mismatched checkpoint/seed datasets are rejected. Changes to
task versions, sequence schedules, configured writer/editor identities and budgets
are rejected too. Analysis options must match the frozen contract; use the plan's
bootstrap settings on `evaluation-report` if they differ from its defaults.

`evaluate --run` automatically saves `analysis.contract.json` in its new run
namespace before the first collection job. The final report embeds the contract
and coverage receipt. `evaluation-verify` recomputes that receipt. Ordinary code
failures are still outcomes; unresolved records remain unresolved even when the
dataset roster is complete. Coverage is not proof of successful inference.

Historical reports remain readable. They cannot acquire pre-inference provenance
retroactively. A legacy export lacking the new image-independent editor identity
cannot satisfy a new strict contract. The seed summary explicitly discloses when
it only covers the checkpoints supplied, rather than a verified planned roster.

The contract fingerprints configured checkpoint identities, prompts and settings,
not actual weight files. Its timestamp is not authenticated. The runtime image
content ID remains separately locked and must match across methods. Commit or
otherwise preserve the contract before collecting real outcomes.

Read-only preflight now rejects a mismatched or malformed saved lock, malformed
Docker metadata, and a regular file where an output directory is needed. It never
repairs saved state, creates a run, pulls an image, or generates code.

## Editing on pairs where both initial programs passed

The primary report retains both all-generated scores and scores conditional on
each writer's own passing programs. Those passing populations can differ.
For a separate comparison using the **same task and generation-seed pairs**:

```powershell
uv run python -m harness evaluation-joint-pass --report runs/primary --method trained --out runs/joint-pass
```

The command keeps a pair only when both initial programs passed. It selects pairs
without using their later editing scores, retains every sequence and editor
repetition for selected parents, and averages within task families before forming
paired differences and exploratory intervals. The JSON and `parent_pairs.csv`
show every included, excluded and unresolved pair with its source hash. No initial
failure is turned into a fabricated editing attempt.

Unknown eligibility or editing outcomes block primary cohort estimates; they
are not dropped to improve the answer. An empty cohort produces no score.
CLI exit 3 means an empty or incomplete cohort; its diagnostic bundle is still
saved. One family cannot supply an uncertainty interval. Reached-step failure
rates retain their conditional denominator, which can differ after early stops;
their estimates use only families where both rates exist.

This is secondary, selected-cohort evidence. It does not replace all-generated
scores, estimate a causal maintainability effect, or produce training labels.
All outputs are separate and immutable. `evaluation-verify` checks their hashes;
rerun the command against the source report to reproduce the derived analysis.

The saved-only demonstration now includes this comparison:

```powershell
uv run python examples/evaluation_workflow.py --out runs/evaluation-refinement-demo --plots
```

Every demonstration outcome is synthetic. Running this software example provides
no evidence that any writer was trained or performs better.

## Validation and remaining work

The implementation at local commit `eff00eb` passed **1,873 Linux CPU checks**
(one optional Node logic check skipped, 79 container/slow cases deselected),
**1,736 relevant Windows checks** (four documented platform/container exclusions),
and **31 real Docker checks**: evaluation smoke plus sandbox/evaluator isolation.
The smoke exercises the actual collector with mock responses, private behavioral
evaluation, terminal failures and zero-inference completed resume. It is software
validation, not experimental model performance. A final malformed-image guard at
`692ca4a` then passed all 14 preflight checks on Linux and the Windows preflight
and course-header suite (1,227 checks). Ruff and whitespace checks passed too.

Preservation checks confirmed all 60 original Windows task hashes, original
prompts, collector, editor, primary scoring code, configuration, model backends
and sandbox code are unchanged. Four historical manifest-bearing reports still
recompute successfully. All 152 historical demonstration files remained unchanged
during byte-identical replay of the new saved-only walkthrough. Local receipts
and scripts are in `../evaluation_refinements/` relative to the Windows checkout.
Earlier failed development checks are preserved there too. One preservation
wrapper initially assumed the oldest pre-manifest demo had a manifest; it stopped
without modifying it, and the corrected check distinguishes that historical case.

New source metadata and reporting code change the evaluation-run fingerprint,
not task hashes or previous scores. A new live run gets its own namespace.
Resume a historical live run with its original checkout; saved-only historical
reports remain readable. No teammate must rerun old experiments because of these
additions. No real-model calls, training or model-weight downloads occurred.

The remaining major project work is to provide the actual trained checkpoints,
freeze the real evaluation roster and analysis choices, run the held-out study,
and inspect its failures. Immutable weight/adapter digests still need independent
recording; configured tags do not attest the weights served. The proposal's
comment/docstring-removal ablation still needs its own frozen, validated transform
and experimental runs. It is deliberately not inserted into the existing editor
or applied to cached outcomes. These software refinements do not establish that
the capstone's training hypothesis works.
