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
