"""Project selected local Git evidence into a public-facing research export."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


class Export:
    def __init__(self, source, revision, output):
        self.source = source
        self.revision = self.git("rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
        self.output = output
        self.inputs = {}
        self.outputs = {}

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args])

    def read(self, path, *, revision=None):
        identity = f"{revision or self.revision}:{path}"
        raw = self.git("show", identity)
        self.inputs[identity] = hashlib.sha256(raw).hexdigest()
        return raw

    def load(self, path, *, revision=None):
        return json.loads(self.read(path, revision=revision))

    def save(self, path, raw):
        target = self.output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError(f"existing export differs: {path}")
        else:
            with target.open("xb") as stream:
                stream.write(raw)
        self.outputs[path] = hashlib.sha256(raw).hexdigest()

    def dump(self, path, data):
        self.save(path, (json.dumps(data, indent=2, sort_keys=True) + "\n").encode())

    def copy(self, path, destination):
        self.save(destination, self.read(path))


def fields(obj, names):
    return {key: obj[key] for key in names.split()}


def rows(records, names):
    return [fields(record, names) for record in records]


FRESH = "docs/fresh_pairs_20261113/evidence/"
NEUTRAL = "docs/fresh_label_validation_20261113/evidence/"
STOCK_DOCUMENTS = "docs/stock_replication_20261113/"
REPLICATION = STOCK_DOCUMENTS + "evidence/"
CONTROLLED = "docs/controlled_wallet_20261113/evidence/"
WALLET = "harness/probes/fresh_label_validation_20261113/tasks/"
FOLLOWUP = "harness/probes/wallet_contract_followthrough_20261113/"
PARENTS = "harness/probes/controlled_wallet_20261113/parents/"


def matched_local_writers(export):
    data = export.load("docs/writer_same_roster_20261112/comparison.json")
    return {
        "families": data["families"],
        "paired_outcomes": data["paired_outcomes"],
        "rows": rows(data["cases"], "case_id direct reasoning sample_idx seed task_id"),
        "training_label": data["training_label"],
    }


def sourcing(export):
    teacher = export.load(FRESH + "teacher_backed_writer_full_comparison.json")
    verification = export.load(FRESH + "writer_verification_summary.json")
    neutral = export.load(NEUTRAL + "pair_evidence.json")
    grouping = export.load(NEUTRAL + "grouping.json")
    return {
        "matched_teacher": {
            **fields(teacher, "all_disagreements_reproduced all_outcomes_valid"),
            "families": {
                family: fields(
                    data, "scheduled hosted_full local_full hosted_private local_private"
                )
                for family, data in teacher["families"].items()
            },
            "rows": rows(
                teacher["rows"], "case_id family hosted hosted_private local local_private"
            ),
        },
        "public_check_selection": {
            family: {
                "blocks": rows(
                    data["blocks"],
                    "block control public_verified control_correct public_verified_correct "
                    "control_private_pass public_verified_private_pass drafts",
                ),
                "counts": fields(
                    data["counts"],
                    "generated correct_drafts public_passing_drafts public_false_positives "
                    "completed_blocks control_correct public_verified_correct "
                    "selection_changed ties private_only_net_wins",
                ),
            }
            for family, data in verification["families"].items()
        },
        "neutral": {
            "confirmed_pair_count": neutral["confirmed_pair_count"],
            "families": {
                row["family"]: {
                    **fields(row, "writer_counts abstention_reason training_label"),
                    "groups": [g["members"] for g in grouping["families"][row["family"]]],
                }
                for row in neutral["families"]
            },
        },
    }


def collection(export):
    original = export.load(FRESH + "pair_evidence_final.json")
    families = {}
    for row in original["families"]:
        phases = {
            phase: (
                rows(
                    data["trajectories"],
                    "case_id parent rep seeds sequence source_sha256 steps "
                    "successful_prefix complete_behavioral",
                )
                if data is not None
                else None
            )
            for phase, data in row["phases"].items()
        }
        families[row["family"]] = {
            **fields(row, "writer_counts abstention_reason training_label"),
            "phases": phases,
        }
    return {**fields(original, "validated_family_count family_count"), "families": families}


def pantry_trial(export):
    original = export.load("docs/verified_pair_trial_20261112/evidence/pair-export.json")
    return {
        family: {
            **fields(record, "abstention_reason training_label"),
            "starts": rows(
                record["writer_source_statuses"],
                "case_id source_sha256 status writer_model",
            ),
            "discovery": rows(
                record["trajectory_outcomes"].get("discovery", []),
                "parent rep seeds sequence steps successful_prefix complete_behavioral",
            ),
        }
        for family, record in original["families"].items()
    }


def replication(export):
    results = {}
    for family, stem in (("stock_portfolio", "stock"), ("feature_flags", "feature_flags")):
        data = export.load(REPLICATION + stem + "_summary.json")
        results[family] = {
            **fields(
                data,
                "decision states submission_paths behavioral_replay_matches training_label",
            ),
            "trajectories": rows(
                data["trajectories"],
                "parent sequence block steps budget_draft_steps",
            ),
        }
    old = export.load(REPLICATION + "historical_budget_diagnostics.json")
    results["historical_budget_diagnostics"] = {
        **fields(old, "scores_modified experimental_calls"),
        "attempts": rows(
            old["attempts"].values(),
            "case_id family original_reason original_status post_hoc_status source_changed",
        ),
    }
    return results


def wallet(export):
    neutral = export.load(NEUTRAL + "summary.json")
    controlled = export.load(CONTROLLED + "summary.json")
    drafts = export.load(CONTROLLED + "intermediate_revision.json")
    published = export.load(
        "docs/wallet_pair_pilot/outcomes.json",
        revision="f5ea7eda38af87ce01f9e0e79400bb3f78718f1a",
    )
    return {
        "neutral": {
            **fields(neutral["phases"]["discovery"], "replays_match statuses gates"),
            "rows": rows(
                neutral["phases"]["discovery"]["rows"],
                "case_id category block parent seeds status submission_reason",
            ),
        },
        "controlled": {
            **fields(
                controlled,
                "observed_successes all_original_replays_matched terminal_outcomes",
            ),
            "intermediate_revision": {
                "distinct": drafts["distinct_compatible_drafts"],
                "passed_both_suites": len(drafts["drafts_passing_both_suites"]),
            },
            "historical_diagnostic": rows(
                published["historical_diagnostic"]["rows"],
                "case original_status diagnostic_status",
            ),
            "rows": rows(
                controlled["rows"],
                "case_id request block parent seeds status reason",
            ),
            "training_label": None,
        },
        "followup": {
            **fields(published["explicit_contract"], "original_replay_matches"),
            "rows": rows(
                published["explicit_contract"]["rows"],
                "case request block parent seed status handoff replayed",
            ),
            "training_label": None,
        },
    }


EXACT = {
    "docs/fresh_pairs_20261113/teacher_backed_writer_protocol.md": "protocols/teacher-sourcing.md",
    "docs/stock_replication_20261113/protocol.md": "protocols/stock-replication.md",
    STOCK_DOCUMENTS + "feature_flags_protocol.md": "protocols/feature-flags-replication.md",
    "docs/fresh_label_validation_20261113/protocol.md": "protocols/neutral-collection.md",
    "docs/controlled_wallet_20261113/protocol.md": "protocols/controlled-wallet.md",
    "docs/verified_pair_trial_20261112/protocol.md": "protocols/verified-starting-programs.md",
    "docs/wallet_contract_followthrough_20261113/protocol.md": "protocols/clarified-wallet.md",
    WALLET + "repair_queue/spec.md": "examples/repair_queue/initial.md",
    WALLET + "reward_wallet/spec.md": "examples/reward_wallet/initial.md",
    PARENTS + "ledger/wallet.py": "examples/reward_wallet/ledger.py",
    PARENTS + "materialized/wallet.py": "examples/reward_wallet/materialized.py",
    FOLLOWUP + "test_public_reverse.py": "examples/reward_wallet/public_reverse.py",
    FOLLOWUP + "test_public_revise.py": "examples/reward_wallet/public_revise.py",
}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("archive_checkout", type=Path)
    cli.add_argument("archive_revision")
    cli.add_argument("destination", type=Path)
    args = cli.parse_args()
    export = Export(args.archive_checkout, args.archive_revision, args.destination)
    for name, project in (
        ("matched-local-writers", matched_local_writers),
        ("pantry-trial", pantry_trial),
        ("sourcing", sourcing),
        ("six-family-edits", collection),
        ("replication", replication),
        ("wallet", wallet),
    ):
        export.dump(f"data/{name}.json", project(export))
    for source, target in EXACT.items():
        export.copy(source, target)
    export.dump(
        "data/manifest.json",
        {
            "schema_version": 1,
            "archive_revision": export.revision,
            "source_sha256": export.inputs,
            "export_sha256": export.outputs,
        },
    )


if __name__ == "__main__":
    main()
