# Additional evaluation workflows

These five additions use the same evaluation tool and preserve its primary scores.
They do not train a writer, generate new programs, repair candidates, or infer
preference labels. Use a new output directory for a new rule or report version.

For planned-roster verification and aligned initial-pass comparisons, see the
[refinement guide](evaluation-refinements.md). The original five workflows below
remain available. New walkthrough outputs also include `joint-pass/`.

## Try everything with synthetic data

From `harness/`:

```bash
uv sync --locked --extra plots
uv run python examples/evaluation_workflow.py --out runs/evaluation-refinement-demo --plots
```

The walkthrough writes a primary comparison, size-matched sensitivity report,
training-checkpoint summary, failure-review pack, all-unreviewed annotation
summary, and PNG/SVG figures. Open `comparison/report.html`, `review/review.html`
and `figures/outcomes.png` under that output directory.

Every outcome, size and checkpoint label in the walkthrough is an explicit
software fixture. No model was called or trained. Its differences demonstrate
the analysis software, not improvement in a writer. An unchanged replay writes
identical bytes in the same rendering environment; older demo directories remain
untouched. The optional plotting extra does not install training dependencies.

## Check readiness before a live run

```bash
uv run python -m harness evaluation-preflight --plan configs/evaluation.proposal.example.yaml
uv run python -m harness evaluation-preflight --plan configs/evaluation.proposal.example.yaml --probe
```

The default checks the plan, Linux execution platform, Docker CLI and nearest
writable output parent. It makes no network requests and creates no directories.
Unchecked requirements remain visible. `--probe` additionally inspects the Docker
engine, existing images and an existing saved image lock, and GETs the configured
loopback servers' advertised model lists. It does not generate text, build/pull an
image, download weights, or create a collection store.

Exit 0 means every readiness check passed; exit 3 means something is failed or
unchecked; malformed configuration returns 2. A mock-only Linux plan can pass
without a model server. The full proposal template intentionally remains blocked
until its placeholder checkpoints are configured.

Only loopback endpoints are permitted; redirects are not followed and no API key
is sent. Recognized `:cloud`/`-cloud` tags are rejected by both preflight and live
execution. A loopback address or advertised model name cannot establish local-only
routing, correct weights, quantization, context settings or future inference
success. Keep the model server configured for local-only weights and record
immutable checkpoint/adapter digests independently. The model-list route follows
[Ollama's OpenAI-compatible API](https://docs.ollama.com/api/openai-compatibility).

## Compare similarly sized initial programs

```bash
uv run python -m harness evaluation-size-match --report runs/PRIMARY_REPORT --method trained --relative-tolerance 0.2 --size-field python_lines --out runs/size-matched
```

Choose the method, size field and tolerance using development data, before
inspecting held-out editing outcomes. The tolerance is required, not optimized
automatically. Its exact rule and SHA-256 are saved in `matching.json`:

`abs(reference_size - method_size) / max(1, reference_size, method_size) <= tolerance`

Both initial parents must pass and have known sizes. Retain an entire task family
only when every scheduled task/generation-seed pair satisfies the rule. Membership
never reads editing success, and one failing pair excludes the whole family.
`matching.csv` lists every included/excluded pair and its reason. `python_lines`
counts physical Python lines, including comments and blanks; `source_lines` is
the alternative total physical program-line measure. This is not architecture
matching or a complete control for complexity.

The result is a separately labeled sensitivity report using the unchanged scorer
and task-family bootstrap. It is conditional on initially passing, size-eligible
parents. Its initial correctness is therefore 100% by construction, not evidence
of improved correctness. It must not replace the primary all-generated result.
No eligible families produces an explicit abstention bundle and exit 3, not zero
performance or a fabricated comparison. Nested matching of an already matched
report is rejected. Older exports with unknown size remain ineligible honestly.

## Inspect variation across training checkpoints

```bash
uv run python -m harness evaluation-seeds --report runs/PRIMARY_REPORT --out runs/seed-summary
```

The command uses the declared `method_group`, `training_seed` and writer identity.
Multiple checkpoints within a group require distinct declared seeds and saved
writer configuration identities. It cannot authenticate training or weight bytes.
All supplied checkpoints remain in `seeds.csv`, including adverse, tied and
unresolved ones. `groups.csv`, `comparisons.csv` and `analysis.json` show group
estimates, per-checkpoint ranges, coverage and directions against the reference.

Each included family's value averages the same observed checkpoint set equally;
families are then equally weighted. Bootstrap intervals resample task families
with that checkpoint set fixed. They are not uncertainty intervals over new
training seeds or evidence from independent editing attempts. One family has no
interval. A genuinely unresolved seed blocks the group's primary estimate.
Conditional/reached-step summaries use common applicable families and disclose
their counts. Report per-checkpoint results as well as the group summary.

The summary covers checkpoints in the supplied saved report. It cannot detect
training runs omitted before that report was created. Freeze the intended seed
roster beforehand and report adverse seeds instead of selecting a favorable one.
Direction counts compare multiple checkpoints with the same reference-group
mean; they are descriptive, not independent significance tests or training labels.

## Review failures with your teammates

```bash
uv run python -m harness evaluation-review init --report runs/PRIMARY_REPORT --out runs/review-pack
# Optional source previews, with explicit saved-store paths:
uv run python -m harness evaluation-review init --report runs/PRIMARY_REPORT --store original=/PATH/TO/ORIGINAL_STORE --store trained=/PATH/TO/TRAINED_STORE --out runs/review-with-code
```

Read `review.html`, then copy `annotations.template.csv` to your own annotation
file. Pack files are immutable and checksummed; the editable copy is separate.
Case IDs bind each first-stop/initial-failure case to this exact source report.
Missing/infrastructure stops remain cases for investigation, not code failures.

Source previews are read only from stores you explicitly supply. Paths embedded
in somebody else's report are never automatically trusted. Source blobs must
match their saved hashes; linked or corrupt blobs are rejected. Missing blobs
stay missing. Previews are escaped HTML text, never executable, with a 2 MiB blob
display limit and 128 KiB total decoded preview limit. Truncation and replacement
decoding are disclosed; original bytes and scores remain unchanged.

Annotation columns are `case_id`, `reviewer`, `category`, `confidence`, `evidence`
and `notes`. Use a unique reviewer ID. Categories include initial bugs, edit bugs,
structural interaction, task ambiguity/difficulty, test defects, infrastructure,
submission problems and uncertainty. Confidence is `hypothesis` or `verified`;
blank templates remain `unreviewed`. Reviewed claims need notes or evidence,
and `verified` requires an evidence reference. An initial-only case cannot assert
a later edit defect. An evidence reference is never opened or executed.

```bash
uv run python -m harness evaluation-review compile --pack runs/review-pack --annotations alice.csv bob.csv --out runs/review-summary
```

Compilation preserves all cases, missing reviews, reviewer disagreements and
every annotation. It does not infer a majority explanation or preference label.
`verified` means reviewer-asserted verification, not causal proof established by
the tool. Verify suspected defects using unchanged artifacts and executable
reproductions before drawing conclusions. Spreadsheet-facing exports escape
formula-like text; JSON retains the reviewer's exact text.

## Export figures for the report or presentation

```bash
uv run python -m harness evaluation-plots --report runs/PRIMARY_REPORT --out runs/figures
```

The optional [Matplotlib](https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.savefig.html)
renderer produces `outcomes`, `differences` and `resources` in PNG and SVG.
`figure_data.json` records the exact plotted estimates, intervals, source-report
hash and renderer environment. Every figure retains synthetic/development labels.
Unknown rates are labeled unavailable, not drawn at zero. Intervals are the saved
task-family intervals, not newly selected uncertainty estimates. Differences are
absolute percentage points. Resource bars are known recorded totals, with missing
fields disclosed; unequal reached work and latency prevent automatic efficiency
or maintainability claims.

SVG IDs and metadata avoid random salts/timestamps. Same-environment replay is
deterministic. A different renderer, platform or library version may produce
different figure bytes; use a fresh output directory rather than replacing old
evidence. The dependency lock preserves the existing package versions and adds
only the plotting extra's requirements. CI installs that extra to exercise figures.

## Verify and reproduce derived outputs

```bash
uv run python -m harness evaluation-verify --report runs/seed-summary
```

Primary reports retain analysis recomputation. Derived bundles receive checksum
verification and explicitly report `analysis_recomputed: false`; rerun the saved
command/rule against the verified primary report to reproduce the derivation.
Checksums establish local integrity, not authenticity of experimental claims.
Every output is non-overwriting and its manifest is published last. Original
reports and stores remain independent of review annotations and sensitivity runs.

## Validation receipt (2026-11-05)

All five features were saved in individual local commits, followed by integration
and malformed-input checks. The full suite at `ec0d788` passed 1,821 Linux CPU
tests on Python 3.11.18 (one optional Node logic test skipped, 79 runtime/slow
cases deselected), 1,684 relevant Windows CPU tests (four documented exclusions),
and 31 real Docker smoke/isolation tests. The final input guard at `077e448`
then passed 22 targeted verification/interoperation tests on both platforms.
Ruff, formatting and whitespace checks passed.

The live Linux mock-plan preflight returned ready without inference. New commands
were exercised together through the public CLI. Figures were rendered and
visually inspected. The complete synthetic walkthrough replayed with identical
bytes, and old and new bundles verified. Human review stayed entirely unreviewed
in the walkthrough; no review findings or training labels were invented.

All 60 original Windows task hashes, original core/settings/prompts and prior
results remain unchanged. The primary analysis, record validation and exporter
have unchanged Python ASTs relative to `2b138f5`; their extra comments explain
scientific and resume decisions. New local/cloud-route guards do not change
historical scores. Previously locked package versions were preserved; plotting
adds optional dependencies only.

The HTML browser preview limitation recorded earlier still applies; automated
escaping/structure and JavaScript logic tests cover the dashboards, while the
exported PNG figures received direct visual inspection. No training, experimental
model calls, model-weight downloads or paid API use occurred. Separate logs/XML,
preflight, replay and preservation receipts are in `../evaluation_extensions/`
relative to the Windows checkout. No changes were pushed.
