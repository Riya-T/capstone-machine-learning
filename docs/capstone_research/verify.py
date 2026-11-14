"""Verify the research export and recompute the reported outcome counts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent


def require(condition, description):
    if not condition:
        raise ValueError(description)


def load(name):
    return json.loads((ROOT / "data" / f"{name}.json").read_bytes())


def verify_manifest():
    manifest = load("manifest")
    require(manifest["schema_version"] == 1, "unsupported manifest version")
    for name, expected in manifest["export_sha256"].items():
        path = PurePosixPath(name)
        require(
            path.parts
            and not path.is_absolute()
            and ".." not in path.parts
            and "\\" not in name
            and ":" not in name,
            f"unsafe manifest path: {name}",
        )
        target = ROOT / path
        require(
            target.is_file()
            and target.resolve().is_relative_to(ROOT)
            and hashlib.sha256(target.read_bytes()).hexdigest() == expected,
            f"missing or altered artifact: {name}",
        )


def verify_sourcing():
    data = load("sourcing")
    teacher = data["matched_teacher"]
    cases = teacher["rows"]
    require(len(cases) == len({row["case_id"] for row in cases}), "duplicate initial attempt")
    for family, totals in teacher["families"].items():
        group = [row for row in cases if row["family"] == family]
        require(len(group) == totals["scheduled"], "initial attempt count changed")
        for writer in ("hosted", "local"):
            require(
                sum(row[writer] == "passed" for row in group) == totals[f"{writer}_full"]
                and sum(row[f"{writer}_private"] for row in group) == totals[f"{writer}_private"],
                "writer totals differ from attempt rows",
            )
    local = sum(row["local"] == "passed" for row in cases)
    hosted = sum(row["hosted"] == "passed" for row in cases)
    differences = sum(row["local"] != row["hosted"] for row in cases)
    require(teacher["all_disagreements_reproduced"], "writer replays incomplete")
    require((local, hosted, len(cases), differences) == (8, 24, 24, 16), "writer report mismatch")

    selection = data["public_check_selection"]
    blocks = [r for family in selection.values() for r in family["blocks"]]
    control = sum(row["control_correct"] for row in blocks)
    verified = sum(row["public_verified_correct"] for row in blocks)
    require((control, verified, len(blocks)) == (8, 11, 24), "writer selection report mismatch")
    families = data["neutral"]["families"]
    require(data["neutral"]["confirmed_pair_count"] == 0, "unexpected neutral pair label")
    for name, count in (("repair_queue", 1), ("reward_wallet", 2)):
        family = families[name]
        members = [member for group in family["groups"] for member in group]
        require(
            len(family["groups"]) == count
            and len(members) == len(set(members)) == family["writer_counts"]["passed"] == 4,
            "invalid neutral writer grouping",
        )
    print(
        f"Teacher {hosted}/{len(cases)}, local {local}/{len(cases)}, "
        f"writer selection {control} to {verified}"
    )


def verify_edits():
    collection = load("six-family-edits")
    require(collection["validated_family_count"] == 0, "unexpected confirmed family")
    require(len(collection["families"]) == collection["family_count"] == 6, "wrong family count")
    require(
        sum(f["writer_counts"]["passed"] for f in collection["families"].values()) == 24,
        "six-family starts changed",
    )
    for family in collection["families"].values():
        require(family["training_label"] is None, "unexpected training label")
        for phase in family["phases"].values():
            if phase is None:
                continue
            require(len(phase) == len({r["case_id"] for r in phase}), "duplicate trajectory")
            for row in phase:
                prefix = 0
                for outcome in row["steps"]:
                    if outcome != "success":
                        break
                    prefix += 1
                require(prefix == row["successful_prefix"], "wrong successful prefix")
    print("Six-family collection: 24 correct starts, zero confirmed families")


def verify_matched_local_writers():
    data = load("matched-local-writers")
    rows = data["rows"]
    require(
        len(rows) == len({(r["task_id"], r["sample_idx"]) for r in rows}) == 18,
        "duplicate or missing matched writer slot",
    )
    outcomes = Counter()
    for task, saved in data["paired_outcomes"].items():
        task_rows = [r for r in rows if r["task_id"] == task]
        observed = Counter(f"reasoning_{r['reasoning']}__direct_{r['direct']}" for r in task_rows)
        require(observed == saved and len(task_rows) == 6, "matched writer roster differs")
        outcomes.update((r["reasoning"] == "passed", r["direct"] == "passed") for r in task_rows)
    require(
        outcomes == {(True, True): 4, (True, False): 4, (False, True): 4, (False, False): 6}
        and data["training_label"] is None,
        "matched writer totals differ",
    )
    print("Matched local writers: both 8/18, each uniquely passed four slots")


def verify_replication():
    replication = load("replication")
    expected = {
        "stock_portfolio": {
            ("sample_00", "s1"): 2,
            ("sample_00", "s2"): 6,
            ("sample_03", "s1"): 3,
            ("sample_03", "s2"): 2,
        },
        "feature_flags": {
            ("sample_00", "s1"): 4,
            ("sample_00", "s2"): 3,
            ("sample_01", "s1"): 6,
            ("sample_01", "s2"): 6,
        },
    }
    for family, counts in expected.items():
        data = replication[family]
        require(data["training_label"] is None, "unexpected replication label")
        require(data["behavioral_replay_matches"], "replication replay mismatch")
        pairs, states = Counter(), Counter()
        for row in data["trajectories"]:
            states.update(row["steps"])
            pairs[row["parent"], row["sequence"]] += row["steps"].count("success")
        require(pairs == counts and states == data["states"], "replication table mismatch")
    diagnostics = replication["historical_budget_diagnostics"]
    require(diagnostics["scores_modified"] == 0, "historical scores changed")
    require(len(diagnostics["attempts"]) == 13, "wrong historical draft count")
    require(
        all(
            row["source_changed"] and row["post_hoc_status"] in {"fail_new", "fail_both"}
            for row in diagnostics["attempts"]
        ),
        "wrong historical draft outcomes",
    )
    print("Stock Portfolio and Feature Flags: 45 exact replays, 13 historical drafts failed")


def verify_wallet():
    data = load("wallet")
    neutral = data["neutral"]
    require(len(neutral["rows"]) == 12, "neutral edit count changed")
    neutral_counts = Counter(
        (row["category"], row["parent"]) for row in neutral["rows"] if row["status"] == "success"
    )
    require(
        len(neutral_counts) == 4 and set(neutral_counts.values()) == {1},
        "neutral category counts changed",
    )

    controlled = data["controlled"]
    followup = data["followup"]
    require(
        len(controlled["rows"]) == 24 and len(followup["rows"]) == 16, "controlled roster changed"
    )
    require(
        controlled["all_original_replays_matched"]
        and followup["original_replay_matches"] == 16
        and all(row["replayed"] for row in followup["rows"]),
        "wallet replay mismatch",
    )
    require(
        controlled["training_label"] is None and followup["training_label"] is None,
        "unexpected Wallet pair label",
    )
    amended = controlled["historical_diagnostic"]
    differences = [r for r in amended if r["original_status"] != r["diagnostic_status"]]
    require(
        len(differences) == 1
        and differences[0]["case"] == "revise/r4/materialized"
        and differences[0]["original_status"] == "success"
        and differences[0]["diagnostic_status"] == "fail_new",
        "historical diagnostic drift",
    )
    drafts = controlled["intermediate_revision"]
    require(drafts == {"distinct": 21, "passed_both_suites": 0}, "revision draft count changed")
    for study, cases, expected in (
        ("Original", controlled["rows"], [1, 4, 0, 1]),
        ("Follow-up", followup["rows"], [1, 2, 4, 4]),
    ):
        counts = Counter((r["request"], r["parent"]) for r in cases if r["status"] == "success")
        actual = [
            counts[request, parent]
            for request in ("reverse", "revise")
            for parent in ("ledger", "materialized")
        ]
        require(actual == expected, f"{study}: published wallet table mismatch")
        print(f"Wallet {study}: reversal {actual[:2]}, revision {actual[2:]}, zero labels")


if __name__ == "__main__":
    verify_manifest()
    verify_matched_local_writers()
    verify_sourcing()
    verify_edits()
    verify_replication()
    verify_wallet()
