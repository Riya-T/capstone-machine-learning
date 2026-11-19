"""Read native collection stores without starting a model, container or Store.

Usage: dataset = export_collection(cfg, image_id, method="base", purpose="heldout")
Portable evidence contains hashes and outcomes, not generated source or credentials.
"""

from __future__ import annotations

from ..collection.view import make_view
from ..evaluation.export import COST_NOTE, _blob, comparison_contract, read_snapshot
from ..evaluation.records import EvaluationError, identifier, read_json
from ..evaluation.source import describe_change, describe_source
from ..registry import build_writer_prompt, load_tasks, load_template, prompt_version
from ..store import editor_cfg_hash, sandbox_cfg_hash, writer_cfg_hash
from .records import KIND, VERSION, selection, validate_collection

STEP_FIELDS = (
    "step",
    "change_id",
    "status",
    "output_blob",
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


def _initial(check):
    if check is None:
        return "unresolved"
    if check["passed"] not in (0, 1):
        raise EvaluationError("Invalid saved initial-check boolean")
    report = read_json(check["report_json"])
    if not isinstance(report, dict):
        raise EvaluationError("Malformed initial evaluation report")
    categories = [v for v in report.values() if isinstance(v, dict)]
    if any(v.get("status") == "infra_error" for v in categories):
        if check["passed"]:
            raise EvaluationError("Passing initial check contradicts infrastructure report")
        return "infra_error"
    if check["passed"] and any(v.get("status") == "failed" for v in categories):
        raise EvaluationError("Passing initial check contradicts failed suite")
    return "pass" if check["passed"] else "fail"


def _definition(task, sequences):
    return {
        "id": task.id,
        "family": task.family,
        "split": task.split,
        "version": task.task_version,
        "change_kinds": {step.change.id: step.change.kind for s in sequences for step in s.steps},
        "sequences": [{"id": s.id, "changes": [x.change.id for x in s.steps]} for s in sequences],
    }


def export_collection(
    cfg, image_id, *, method, purpose="heldout", method_group=None, training_seed=None
):
    """Use exact current cache keys; missing/mismatched records remain unresolved.

    The explicit image ID avoids a hidden dependency on a running Docker daemon.
    A snapshot includes committed WAL records while preventing half-read tables.
    Blobs are content addressed and verified before source is described.
    """
    identifier(method, "method")
    if not isinstance(image_id, str) or not image_id.startswith(("sha256:", "apptainer:sha256:")):
        raise EvaluationError("Supply the recorded content image ID, not an image tag")
    suffix = image_id.rsplit(":", 1)[-1]
    if len(suffix) != 64 or any(c not in "0123456789abcdef" for c in suffix):
        raise EvaluationError("Invalid image content digest")
    writer_hash = writer_cfg_hash(cfg)
    sandbox_hash = sandbox_cfg_hash(cfg, image_id)
    editor_hash = editor_cfg_hash(cfg, image_id)
    contract = comparison_contract(cfg, image_id)
    contract.update(
        samples_per_task=cfg.writer.samples_per_task,
        writer_samples_per_task=cfg.writer.samples_per_task,
        max_programs=cfg.tasks.max_programs,
    )
    data = {
        "schema_version": VERSION,
        "kind": KIND,
        "method": method,
        "method_group": method_group or method,
        "training_seed": training_seed,
        "generation_seed": cfg.seed,
        "purpose": purpose,
        "writer_model": cfg.writer.backend.model,
        "writer_identity": writer_hash,
        "editor_identity": editor_hash,
        "contract": contract,
        "provenance": {
            "config_hash": cfg.config_hash,
            "source_store_present": False,
            "runs": [],
            "cost_note": COST_NOTE,
            "weights_attested": False,
            "model_revision_note": "Configured tag only; weights not attested by the collector.",
            "hint_slots": len(cfg.writer.design_hints),
            "scheduled_only": True,
        },
        "tasks": [],
    }
    tasks = load_tasks(cfg.tasks)
    template = load_template(cfg.writer.prompt_template)
    view = make_view(cfg.editor.view_transform)
    run_ids = set()
    source = cfg.runs_dir / "harness.sqlite"
    with read_snapshot(source) as db:
        data["provenance"]["source_store_present"] = db is not None
        for task in sorted(tasks.values(), key=lambda t: t.id):
            sequences = task.sequences[: cfg.tasks.max_sequences]
            pv = prompt_version(build_writer_prompt(task.writer_view(), template))
            rows = (
                []
                if db is None
                else db.execute(
                    "SELECT * FROM candidates WHERE task_id=? AND prompt_version=? "
                    "AND writer_cfg_hash=? AND sample_idx>=0 AND sample_idx<? ORDER BY sample_idx",
                    (task.id, pv, writer_hash, cfg.writer.samples_per_task),
                ).fetchall()
            )
            indexed = {row["sample_idx"]: row for row in rows}
            programs, samples = {}, []
            for index in range(cfg.writer.samples_per_task):
                row = indexed.get(index)
                sample = {
                    "sample_idx": index,
                    "candidate_id": None,
                    "initial_status": "unresolved",
                    "parse_category": None,
                    "writer_cost": {"tokens_in": None, "tokens_out": None, "wall_s": None},
                }
                if row is not None:
                    run_ids.add(row["run_id"])
                    origin = db.execute(
                        "SELECT config_json FROM runs WHERE run_id=?", (row["run_id"],)
                    ).fetchone()
                    if origin is None or read_json(origin["config_json"]).get("seed") != cfg.seed:
                        raise EvaluationError(
                            "Saved candidate generation seed disagrees with the requested config"
                        )
                    cid = row["candidate_id"]
                    if cid is not None and row["parse_error"] is not None:
                        raise EvaluationError("Candidate has both parsed source and a parse error")
                    sample.update(
                        candidate_id=cid,
                        writer_cost={k: row[k] for k in ("tokens_in", "tokens_out", "wall_s")},
                    )
                    sample["writer_cost"]["n_calls"] = 1
                    if cid is None:
                        sample.update(
                            initial_status="parse_failure",
                            parse_category=(row["parse_error"] or "unknown").split(":", 1)[0],
                        )
                    else:
                        if cid not in programs:
                            files = _blob(cfg.runs_dir, cid)
                            check = db.execute(
                                "SELECT * FROM initial_checks WHERE task_id=? AND task_version=? "
                                "AND candidate_id=? AND sandbox_cfg_hash=?",
                                (task.id, task.task_version, cid, sandbox_hash),
                            ).fetchone()
                            if check is not None:
                                run_ids.add(check["run_id"])
                            status = _initial(check)
                            parent = {
                                "candidate_id": cid,
                                "initial_status": status,
                                "sample_indices": [],
                                "source_metrics": describe_source(files),
                                "selection": "unresolved",
                                "trials": [],
                            }
                            for seq in sequences:
                                for rep in range(cfg.editor.reps):
                                    checkpoints = (
                                        []
                                        if status != "pass"
                                        else db.execute(
                                            "SELECT * FROM checkpoints "
                                            "WHERE task_id=? AND task_version=? "
                                            "AND candidate_id=? AND sequence_id=? "
                                            "AND rep=? AND editor_cfg_hash=? "
                                            "ORDER BY step",
                                            (
                                                task.id,
                                                task.task_version,
                                                cid,
                                                seq.id,
                                                rep,
                                                editor_hash,
                                            ),
                                        ).fetchall()
                                    )
                                    steps = []
                                    # Apply the original editor view, never to saved scores.
                                    previous = view(files)
                                    for checkpoint in checkpoints:
                                        run_ids.add(checkpoint["run_id"])
                                        step = {k: checkpoint[k] for k in STEP_FIELDS}
                                        after = None
                                        if checkpoint["output_blob"] is not None:
                                            after = _blob(cfg.runs_dir, checkpoint["output_blob"])
                                        step["source_metrics"] = (
                                            None if after is None else describe_source(after)
                                        )
                                        step["change_size"] = describe_change(previous, after)
                                        steps.append(step)
                                        previous = after
                                    parent["trials"].append(
                                        {"sequence": seq.id, "rep": rep, "steps": steps}
                                    )
                            programs[cid] = parent
                        sample["initial_status"] = programs[cid]["initial_status"]
                        programs[cid]["sample_indices"].append(index)
                samples.append(sample)
            exported = {
                "definition": _definition(task, sequences),
                "samples": samples,
                "programs": list(programs.values()),
                "prompt_version": pv,
            }
            for cid, state in selection(exported, cfg.tasks.max_programs).items():
                programs[cid]["selection"] = state
            data["tasks"].append(exported)
        if db is not None:
            data["provenance"]["runs"] = [
                dict(row)
                for run_id in sorted(run_ids)
                for row in db.execute(
                    "SELECT run_id, git_commit, git_dirty, config_hash, started_at "
                    "FROM runs WHERE run_id=?",
                    (run_id,),
                )
            ]
    scheduled = sum(len(t["samples"]) for t in data["tasks"])
    matched = sum(s["writer_cost"].get("n_calls") == 1 for t in data["tasks"] for s in t["samples"])
    missing_checks = sum(
        p["initial_status"] == "unresolved" for t in data["tasks"] for p in t["programs"]
    )
    warnings = []
    if not data["provenance"]["source_store_present"]:
        warnings.append("source_store_missing")
    elif matched == 0:
        warnings.append("no_matching_candidates_check_config_prompt_and_line_endings")
    elif matched < scheduled:
        warnings.append("scheduled_writer_answers_missing")
    if missing_checks:
        warnings.append("initial_checks_missing_check_task_version_and_image_id")
    data["provenance"]["lookup"] = {
        "scheduled_writer_slots": scheduled,
        "matching_writer_answers": matched,
        "parsed_parents_without_matching_initial_check": missing_checks,
    }
    data["provenance"]["warnings"] = warnings
    return validate_collection(data)
