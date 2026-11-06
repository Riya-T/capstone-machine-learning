# Evaluation tool self-audit — 2026-11-05

The first version had reproducible provenance, record-validation and interrupted-write
defects. They are fixed with regression tests. The tool is ready for review and a
Linux/container smoke, followed by a real matched writer evaluation when checkpoints
exist. This audit supplies software evidence, not evidence that training works.

Audit baseline: `48cc33b`. Fix commit: `e62b491`. Reporting improvements:
`34ca6cf`. All changes are local on `feat/evaluation-comparison`; nothing was pushed.

## Verified first-version defects

Six negative regression controls failed against the original implementation before
the fixes; the saved baseline log records those failures.

| Finding | Risk | Fix and validation |
|---|---|---|
| Prepared inputs could change before execution without being checked again. | Collection could use inputs different from its frozen provenance. | Recheck source, resolved configuration, task versions and input-file hashes before execution, each job, and around collection. A changed writer template changes the fingerprint. Tests forbid inference and verify rejection. |
| A method could combine different writers across generation seeds. | Results from distinct checkpoints could silently become one method's score. | Export writer configuration identity and reject identity/model-tag drift within a method. Controls cover both different model tags and different configuration identities. |
| A sequence's changes could be a string instead of an array. | Characters could become apparently valid changes. | Validate array shapes, change identifiers and trajectory ordering; reject the malformed record. |
| A parse failure could also claim a parsed source hash. | Inconsistent initial-correctness accounting could pass validation. | Reject contradictory source/status combinations, without changing valid initial-failure scores. |
| A successful edit could claim fewer passing tests than its recorded total. | Corrupt evidence could be reported as behavioral success. | Validate counts and reject contradictions with claimed passing suites. A timeout/collection failure with 0/0 remains a failure; counts alone cannot establish success. |
| Interrupted JSON publication could leave a truncated final filename. | A partial lock/snapshot could block or confuse resume. | Flush a sibling temporary file and atomically publish via a non-overwriting hard link. Injected publication failures leave no final file; conflicting concurrent evidence is preserved. |

Additional protections reject duplicate JSON keys, nonfinite JSON numbers, malformed
saved metadata, Windows reserved output names, and case-insensitive method-name
collisions. New exports verify edited source blobs as well as initial source blobs.
No source store is opened through writable initialization during export.

## Useful additions

- `comparisons.csv` exposes every paired metric and interval; `families.csv` exposes
  the underlying task-family values and missingness.
- Readable differences explicitly use **percentage points**, avoiding confusion
  between absolute and relative improvement.
- Reports publish `manifest.json` last, with SHA-256 hashes for the other six files.
  A missing manifest means an incomplete bundle. An injected mid-report interruption
  recovers on replay without replacing previously published files. The output
  filesystem must support hard links; unsupported/denied publication fails rather
  than falling back to an unsafe overwrite.
- Initial and reached edited artifacts include non-executing source descriptions:
  physical lines and Python comment/docstring density. Only actual Python docstrings
  count; overlapping comment/docstring lines count once. Invalid source has unknown
  documentation measures. These describe code, not maintainability or correctness.
- Execution order rotates methods between generation seeds and is recorded in the
  frozen plan/preview. One generation seed cannot provide order counterbalancing;
  individual attempts inside a collector job retain the collector's existing order.

## Validation receipt

Local Python 3.12.14 / Windows regression command, from `harness/`:

```bash
uv run pytest tests/evaluation tests/test_headers.py tests/test_registry.py tests/test_config.py tests/test_train_dpo.py tests/collection tests/models tests/integration/test_writer_replay.py -m "not docker and not apptainer and not slow" --deselect=tests/test_registry.py::test_synthetic_task_loads --deselect=tests/test_registry.py::test_symlinks_are_rejected -q
```

Result: **1,579 passed, 4 deselected**. The four exclusions are two pre-existing
Windows restrictions (a newline-sensitive fixture and symlink privilege) and two
container/slow checks. Scoped Ruff checks and whitespace checks passed. New source
also parses using Python 3.11 grammar; that is not a separate Python 3.11 runtime run.

The saved-only report CLI ran successfully on the committed synthetic fixtures in
`runs/evaluation-demo-audited`, verified every manifest checksum, and replayed with
identical bytes. Older demo directories were not overwritten. The restricted agent
sandbox initially denied NTFS hard-link creation; the ordinary-permission local run
succeeded. The denied attempt's log was retained separately.

The real example's preview loaded all 16 eval tasks, bounded the plan at 32 writer
generations / 576 editing checkpoints, and performed no inference. Actual collector
integration, interrupted-job resume and completed zero-inference replay are exercised
with fake execution in tests; they are not model or container results.

All 60 raw task hashes match the completed first-version preservation receipt.
Task files, prompts, original collector/editor/scorer, store schema, backends,
sandbox, original configuration files and saved experiments are unchanged. The
earlier Windows/LF checkout caveat remains as documented in the main guide.
The evaluation tool's source fingerprint changes with these fixes, so new plans
get new namespaces; task hashes and prior scores do not change. Historical runs
remain reportable from exported JSON or their original pinned checkout.

Local evidence outside the repository is in `../evaluation_audit/` relative to the
checkout: baseline failures, regression XML/log/command, demo/replay receipt,
preview, usage and preservation receipts. The replay fixtures themselves are
committed, and the commands in the main guide reproduce the reporting workflow.

## Remaining limits and next step

No real-model calls, downloads, training or rescoring of previous experiments ran.
No Docker CLI or installed WSL distribution is available here. Therefore the real
container smoke remains unverified on this machine:

```bash
uv run pytest tests/evaluation/test_docker.py --slow -rs
```

Run that on a Linux/Docker machine before relying on a new live evaluation. Then
configure locally served writer checkpoints and execute a matched plan. The
existing collector records model tags, not resolved weight digests or guaranteed
provider-observed token counts; record immutable serving revisions separately.
Legacy exports lack the new source/configuration identity evidence and cannot
retroactively provide it.

Trained seeds remain separate method rows. Hierarchical pooling, independently
validated comment-stripping/size-matching ablations, plots and baseline training
are still separate work. Adding them casually would change the scientific protocol
or extend this audit beyond a useful bounded software review. Do not interpret
the synthetic report's known differences as measured improvements.

Observed weekly usage at start and final check: 1% used (99% remaining), at the
account's whole-percentage resolution. This does not imply zero fractional usage.
No reset credits or paid credits were used.
