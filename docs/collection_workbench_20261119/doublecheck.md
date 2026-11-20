# Follow-up check

The workbench is ready for branch review, with one small input-validation
fix added during this check. No scoring defect was found in the reviewed
selection, duplicate accounting, checkpoint, review or publication paths.
This is bounded verification, not a claim that no possible bug remains.

## Defect found and fixed

The build command accepted JSON `true` as schema version `1`, because Python
compares those values as equal. It also lacked explicit checks for several
malformed manifest shapes. The version now requires an integer, and invalid
top-level objects, checkpoint objects and analysis-option shapes receive a
normal command error. Unsupported analysis keys are rejected.

Six regression cases check rejection without accessing a config or store
or creating an output directory. A separate control loaded the trusted
previous repository implementation and reproduced config access with the
boolean version, while the fixed implementation rejected the same input.
Valid version-1 inputs and saved-report contents are unchanged.

## Fresh verification

| Check | Result |
|---|---|
| Windows native workbench suite | 97 passed; one unprivileged symlink-creation skip; Docker test deselected |
| Linux native workbench, legacy review/seed suites and both Docker checks | 118 passed; two Windows-only skips |
| Ruff on workbench, tests, walkthrough and shared evaluation helpers | Passed |
| Seven earlier saved comparison/investigation bundles | All verify; every saved file unchanged |
| Eighteen protected Git objects | Unchanged, including tasks, prompts, training code, results and original CI |
| Historical validation receipts | Retained unchanged |
| Commit-history inspection | No raw databases, weights, logs, screenshots, CSVs or JSONL artifacts among contribution paths |

The collector's first-distinct-passing-parent cap matches the workbench's
selection rule. Duplicate writer answers share saved parent editing outcomes
without becoming independent editing trials. Missing work and later
checkpoints after a stop remain separate from observed behavioral failures.

The targeted history scan found no added machine-local home paths or tested
credential-like markers. This is not a guarantee against every possible
private string. Normal Git author identity remains in commit metadata.

The [check receipt](doublecheck.json) binds these checks to the implementation
commit and local JUnit hashes. Raw logs and the prior-code control remain in
the separate local `collection_workbench_doublecheck_20261119/` namespace.
The full repository suite was not rerun for this CLI-only fix; its earlier
42 upstream header failures and validation evidence remain documented in the
[extension report](extensions.md).

No experimental model calls, training, task edits, score changes or pushes
were performed. Actual team databases and adapters remain unavailable here;
this check validates the software, not the team's reported model gains.
