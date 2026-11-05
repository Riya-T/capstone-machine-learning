"""Account for every planned checkpoint without inventing missing model outcomes.

Usage:
    checkpoints, failures = diagnostic_rows(comparison)
"""

from __future__ import annotations

CHECKPOINT_FIELDS = (
    "method",
    "generation_seed",
    "task",
    "family",
    "candidate_id",
    "initial_status",
    "sequence",
    "rep",
    "step",
    "change_id",
    "status",
    "recorded",
    "new_feature_failure",
    "preserved_behavior_failure",
    "input_source_hash",
    "output_source_hash",
    "new_pass",
    "new_total",
    "existing_pass",
    "existing_total",
    "tokens_in",
    "tokens_out",
    "n_calls",
    "wall_s",
    "end_reason",
    "infra_cause",
)
FAILURE_FIELDS = (
    "method",
    "generation_seed",
    "task",
    "family",
    "candidate_id",
    "sequence",
    "rep",
    "stage",
    "step",
    "change_id",
    "status",
    "end_reason",
    "infra_cause",
)
BEHAVIORAL = {"success", "fail_new", "fail_existing", "fail_both"}


def diagnostic_rows(result):
    """Return a ledger and the first stop per trajectory, never a causal diagnosis.

    Repetitions/steps are accounting rows, not independent evidence. An initial
    failure appears once in the stop table, rather than once per planned edit.
    Infrastructure, budget, missing work and not-reached work stay distinct.
    """
    checkpoints, failures = [], []
    for data in result["source_datasets"]:
        tasks = {task["id"]: task for task in data["tasks"]}
        for sample in data["samples"]:
            task = tasks[sample["task"]]
            base = dict(
                method=data["method"],
                generation_seed=data["generation_seed"],
                task=task["id"],
                family=task["family"],
                candidate_id=sample["candidate_id"],
            )
            initial = sample["initial_status"]
            if initial != "pass":
                failures.append(
                    dict(
                        **base,
                        sequence=None,
                        rep=None,
                        stage="initial",
                        step=None,
                        change_id=None,
                        status="initial_" + initial,
                        end_reason=None,
                        infra_cause=None,
                    )
                )
            sequences = {s["id"]: s["changes"] for s in task["sequences"]}
            for trial in sample["trials"]:
                trial_base = dict(**base, sequence=trial["sequence"], rep=trial["rep"])
                actual = {s["step"]: s for s in trial["steps"]}
                stopped = (
                    None
                    if initial == "pass"
                    else "not_reached_initial_unresolved"
                    if initial == "unresolved"
                    else "not_reached_initial_failure"
                )
                previous = sample["candidate_id"] if initial == "pass" else None
                for number, change in enumerate(sequences[trial["sequence"]], 1):
                    saved = actual.get(number)
                    status = stopped or (saved["status"] if saved else "missing")
                    row = dict(
                        **trial_base,
                        initial_status=initial,
                        step=number,
                        change_id=change,
                        status=status,
                        recorded=saved is not None,
                        new_feature_failure=(status in ("fail_new", "fail_both"))
                        if status in BEHAVIORAL
                        else None,
                        preserved_behavior_failure=(status in ("fail_existing", "fail_both"))
                        if status in BEHAVIORAL
                        else None,
                        input_source_hash=previous if not stopped else None,
                        output_source_hash=saved.get("output_blob") if saved else None,
                        **{
                            key: saved.get(key) if saved else None
                            for key in (
                                "new_pass",
                                "new_total",
                                "existing_pass",
                                "existing_total",
                                "tokens_in",
                                "tokens_out",
                                "n_calls",
                                "wall_s",
                                "end_reason",
                                "infra_cause",
                            )
                        },
                    )
                    checkpoints.append(row)
                    if not stopped and status != "success":
                        failures.append(
                            dict(
                                **trial_base,
                                stage="edit",
                                step=number,
                                change_id=change,
                                status=status,
                                end_reason=row["end_reason"],
                                infra_cause=row["infra_cause"],
                            )
                        )
                        stopped = (
                            "not_reached_after_missing"
                            if status == "missing"
                            else "not_reached_after_infra_error"
                            if status == "infra_error"
                            else "not_reached_after_failure"
                        )
                    previous = row["output_source_hash"]
    return checkpoints, failures
