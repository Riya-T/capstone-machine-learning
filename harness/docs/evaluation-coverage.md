# Evaluation coverage against the proposal

The main metrics in `Task_list.md` section 6 are implemented. The later
[analysis extensions](evaluation-analysis.md) add preflight, figures, human review,
size matching and summaries over the fixed observed training checkpoints. The wider proposal
also requires experimental controls, ablation runs and human analysis; software
support is not evidence that those experiments have been completed.

Reviewed sources: [task list](../../Task_list.md), and the experimental-evaluation,
baseline and ablation sections on pages 2–4 of
[the proposal](../../docs/Project_Proposal_473_v2.docx.pdf). Review and additions:
2026-11-05. Tested implementation commit: `ace2b49`.

## Main numbers

| Requirement | Definition in this tool | Where to inspect |
|---|---|---|
| Fraction of changes completed before first failure | Consecutive successes divided by planned sequence length; no credit for partially passing tests. Initially wrong/unparseable programs contribute zero to all-generated completion. | `change_completion` and `change_completion_initially_correct` in JSON, summary/paired/family CSVs and readable reports. |
| How often the first version works | Fraction of initial attempts passing both public and initial private tests; unparseable answers fail, unresolved work prevents a complete estimate. No selection of the best passing alternative. | `initial_correctness`, explicit initial counts and source datasets. |
| How often the full sequence succeeds | Fraction of planned trajectories with every change passed. Report all-generated and initially passing populations separately. | `whole_sequence_success` and its initially-correct counterpart. |
| How often old behavior breaks | Preserved-behavior failures divided by reached steps actually behaviorally evaluated, with task families equally weighted for reported rates. An initial failure has no editing regression observation, and a budget stop is not an observed regression. | `regression_rate_reached`, numerator/denominator counts, checkpoint ledger. |
| Tokens and time | Recorded input/output tokens and attempt wall time, including unknown fields; writing and editing phases and both populations are separate. Unstarted work is not measured cost. | `costs`, `resource_breakdown`, `resources.csv`, raw checkpoint/writer records. |
| Amount of code changed | Added/removed files, byte totals and Python lines added/removed from verified before/after blobs. Unknown source yields unknown size; normalizing line endings can produce a byte change with zero textual line changes. | `change_size` in step records; `checkpoints.csv`. Descriptive only. |
| How much each method comments | Physical Python comment lines (including inline comments), actual docstring lines, and union documentation density. All-generated and initially-correct populations are distinct; syntax/unparseable/missing source is unknown and disclosed. | `all_generated_source_descriptives`, `initial_source_descriptives`, `source_descriptives.csv`, readable report. |

Repeated edits, sequences and generation seeds are averaged within task families
before equally weighting families. Paired exploratory bootstrap intervals resample
families, not individual attempts. One family has no interval. Missing or
infrastructure-interrupted work blocks the main estimate instead of becoming a
zero or being silently dropped. Conditional populations can differ between methods.
Small sample sizes and test coverage still limit scientific conclusions.

Token counts may include the existing collector's fallback estimates; elapsed time
includes latency and check execution. Code size, shorter diffs and fewer tokens
are not automatic maintainability evidence. No new behavioral scoring rule, test
or private feedback to agents is introduced by these reporting additions.

## Five methods and training seeds

```bash
uv run python -m harness evaluate --plan configs/evaluation.proposal.example.yaml
```

The new dry-run template represents the five proposal conditions:

1. Original writer.
2. Same writer with a maintainability-focused prompt.
3. Correctness-only writer, three separately served trained checkpoints.
4. Static-ranking writer, three separately served trained checkpoints.
5. Later-outcome-trained writer, three separately served trained checkpoints.

That is 11 checkpoint configurations, one fresh initial generation per task and
configuration, 16 held-out tasks, two three-change sequences and three editor
repetitions: at most 176 initial generations and 3,168 editing checkpoints. Normal
failures stop trajectories, so actual inference can be lower. The preview itself
performs no inference. Placeholder model names prevent live execution until the
trained checkpoints are actually available; this tool does not create them.

`writer_model` optionally overrides only a method's writer checkpoint. The shared
editor, budgets and task set remain matched. `method_group` and `training_seed`
declare checkpoint provenance; training seeds are never substituted for generation
seeds. The 11/22/33 labels are editable placeholders for the real training seeds,
not claims that training took place. Replicate groups require distinct declared
training seeds and distinct writer configuration identities. `methods.csv`
preserves this metadata and the configured model tags. Record actual immutable
weight/adapter digests and server quantization separately; tags are not resolved
weight digests.

Each trained checkpoint retains its own results and family-bootstrap intervals.
The optional `evaluation-seeds` workflow additionally summarizes the fixed observed
checkpoint set while bootstrapping task families. No hierarchical inference over
future training seeds is claimed.
Report every seed, including adverse seeds, and predeclare any across-seed summary
before inspecting the held-out results. The prompt-only comparison now uses the
team's `writer_maintainable_v1.md`, also used by `rtx5070_eval_maintain.yaml`.
The earlier `writer_maintainability_v1.md` draft remains for provenance but is not
used by the current example plan. Freeze the chosen plan before a real run.

New runs automatically freeze the planned checkpoint/generation-seed roster
before collection; saved-only reports can require that contract too. This detects
omitted methods and seeds, not just unresolved work in the datasets supplied.
Historical reports without a contract remain usable but cannot establish that no
checkpoint was omitted. The optional joint initial-pass analysis compares the same
task/seed pairs where both writers initially passed. See
[coverage and paired comparisons](evaluation-refinements.md) for commands and
selected-cohort limitations. Neither addition changes the primary scorer.

## Wider proposal: supported versus still requiring work

| Item | Current status |
|---|---|
| Matched held-out task families, editor and budgets | Enforced in plan preparation and comparison; family split checks reuse the registry. New eval task sequences retain their third change. |
| Familiar versus eval-only change kinds | New exports record the actual change-kind mapping and checkpoint ledger column. Older exports honestly lack it. Kind-specific success must be interpreted among reached checkpoints, not as an independent causal test; a predeclared aggregate analysis remains work. |
| Repeated editing and random seeds | Supported and fully recorded. Training checkpoint seeds and generation seeds are explicitly distinct. |
| Failure analysis | Immutable review packs, source previews and separate human annotations complement the first-stop/checkpoint tables. These distinguish code/new-feature/preserved-behavior failures, budget, infrastructure, missing and not-reached work. Establishing initial bugs, editor mistakes, unclear tests or structural difficulty still requires human review and executable reproductions. The tool does not invent causal labels. |
| Comments/docstrings removed | Done in the collection harness, not this tool: `editor.view_transform: strip_comments` (`collection/view.py`) checks that each stripped file parses to the same syntax tree without its docstrings (no test reads `__doc__`), and its own editor key keeps ablation trials apart from the normal ones. All five writers were rerun on the eval tasks; results in `harness/results/nocomments_eval.md`. |
| Size-matched check | Source sizes are available. The size-matching workflow now records a required tolerance, whole-family membership and all exclusions. Freeze its rule before outcomes; it is a separate sensitivity result, not a replacement primary score. |
| One versus two changes / one versus three repetitions for training pairs | Existing team scorer already exposes `max_changes` and `reps` for saved-result preference construction. Training and evaluating those derived writers is separate work. |
| Second editor | Supported as a separate matched plan in which every method shares that editor. Different editors cannot be mixed in one primary comparison. Actual independent-editor inference is a stretch experiment, not completed here. |
| Plots and final scientific report | Offline dashboard, CSV/JSON tables and PNG/SVG publication-figure export exist. Actual scientific findings, interpretations and the final write-up still require real experimental data. |
| Train all controls and run the held-out comparison | Not done by this tool-building task. No training, real-model generation or measured model improvement is claimed. |

## Runtime validation

The original Windows checkout is preserved. Linux validation uses a separate
`CapstoneEval` Ubuntu 24.04 WSL distribution, checkout
`/root/capstone-eval-validation` pinned to `ace2b49`, and its own locked Python
3.11 environment. Docker Engine is installed from the official signed Ubuntu
repository inside that distro, following
[Docker's installation documentation](https://docs.docker.com/engine/install/ubuntu/).

Docker Engine 29.9.3, cgroups v2, Linux amd64, WSL kernel
`6.6.87.2-microsoft-standard-WSL2`; approximately 32.36 GB memory visible to the
Linux environment. This is a container test environment, not a measured GPU run.
No existing Python environment was replaced, Windows driver changed, or machine
restarted. WSL's new default distro is `CapstoneEval`.

Docker Desktop 4.98.0 was also installed per user from Docker's signed installer
(SHA-256 `cd6273d9eaa4f07fa7593fc6813d37e1004381cebc3f26047a2554fa5db24388`).
Its first-run agreement dialog could not be operated by the UI tool despite user
approval. It is not the runtime used by these successful tests. A Desktop GUI
setup/integration completion is optional for this working Engine-in-WSL route.

Real container validation passed:

- Evaluation smoke: **1 passed**, covering the real collector/evaluator orchestration
  with reference/mock responses, terminal code failures, completion markers,
  completed zero-inference resume and saved-only export.
- Sandbox/evaluator integration: **30 passed**, 65 other tests deselected. Controls
  cover memory/process/time limits, blocked network, unprivileged execution,
  read-only filesystems, output handling, cleanup and behavioral evaluation.
- Windows relevant regression suite: **1,628 passed**, with four documented
  exclusions (two Windows fixture/symlink cases and two container/slow checks).
- Full Linux CPU suite on Python 3.11.18: **1,765 passed, one optional Node check
  skipped, 79 Docker/Apptainer/slow cases deselected**. The optional JavaScript
  logic check already passed on Windows with installed Node. The Windows-only
  fixture/symlink exclusions were not necessary in this Linux run.

The first container-check wrapper omitted a temporary directory's parent: the
initial smoke had one setup error, and isolation had 28 passes/two setup errors.
Those logs are preserved. Only that wrapper setup was corrected; successful
reruns have separate `-v2` receipts. No benchmark score or candidate was repaired.

Run in the new WSL environment:

```powershell
wsl -d CapstoneEval -u root -- sh -lc 'systemctl start docker; cd /root/capstone-eval-validation/harness && .venv/bin/python -m pytest tests/evaluation/test_docker.py --slow -rs'
wsl -d CapstoneEval -u root -- sh -lc 'cd /root/capstone-eval-validation/harness && .venv/bin/python -m pytest tests/sandbox/test_runner.py tests/sandbox/test_evaluator.py -m "docker and not slow" -rs'
```

The root account controls the daemon only in this dedicated distro. Generated
programs run unprivileged inside the resource-limited containers. Windows `docker`
targets Docker Desktop; Linux `docker` in `CapstoneEval` targets its separate Engine.
Images and containers are separate. Keep using the tested WSL checkout for live
execution; the Windows checkout remains suitable for saved-only reporting.

Separate local receipts are in `../evaluation_requirements/` relative to the
Windows checkout: extracted proposal text, previews, CPU and container logs/XML,
runtime information, preservation receipt and setup scripts. New proposal-demo
outputs are in `harness/runs/evaluation-proposal-demo`. Older reports still verify.
All 60 original Windows task hashes, original prompts/core/settings and saved
experiments are preserved. No new real-model calls or training ran. Nothing was
pushed.
