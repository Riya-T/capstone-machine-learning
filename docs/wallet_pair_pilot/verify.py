"""Verify the compact pilot data and print per-request pass counts.

Run with Python 3.11 or later from any directory.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUESTS = ("reverse", "revise")
PARENTS = ("ledger", "materialized")
STATUSES = {
    "success",
    "fail_new",
    "fail_existing",
    "fail_both",
    "missing",
    "interrupted",
    "budget_exhausted",
    "infra_error",
    "invalid_output",
    "timeout",
}


def verify(data):
    initial = {
        parent: hashlib.sha256(
            json.dumps(
                {"wallet.py": (ROOT / "method" / f"{parent}.py").read_text(encoding="utf8")},
                sort_keys=True,
            ).encode()
        ).hexdigest()
        for parent in PARENTS
    }
    seeds = []
    for name, blocks in (("original", 6), ("explicit_contract", 4)):
        run = data[name]
        rows = run["rows"]
        expected = {
            (request, block, parent)
            for request in REQUESTS
            for block in range(blocks)
            for parent in PARENTS
        }
        identities = {(r["request"], r["block"], r["parent"]): r for r in rows}
        if len(rows) != len(expected) or identities.keys() != expected:
            raise ValueError(f"{name}: missing or duplicate planned attempt")
        if run["parents"] != initial:
            raise ValueError(f"{name}: included parent source changed")
        if any(r["status"] not in STATUSES for r in rows):
            raise ValueError(f"{name}: unknown outcome")
        matched = set()
        for request in REQUESTS:
            for block in range(blocks):
                first, second = (identities[request, block, parent] for parent in PARENTS)
                if first["seed"] != second["seed"]:
                    raise ValueError(f"{name}: expected seed matching within each block")
                matched.add(first["seed"])
        if len(matched) != blocks * len(REQUESTS):
            raise ValueError(f"{name}: seed reused across blocks")
        seeds.append(matched)
        if sum(r["replayed"] is True for r in rows) != run["original_replay_matches"]:
            raise ValueError(f"{name}: inconsistent replay accounting")
    if seeds[0] & seeds[1]:
        raise ValueError("the follow-up reused an original seed")
    historical = data["historical_diagnostic"]["rows"]
    original = {r["case"]: r["status"] for r in data["original"]["rows"]}
    if (
        len(historical) != len({r["case"] for r in historical})
        or any(original[r["case"]] != r["original_status"] for r in historical)
        or Counter(r["diagnostic_status"] for r in historical)
        != data["historical_diagnostic"]["counts"]
    ):
        raise ValueError("saved diagnostic does not match the original roster")


def summarize(data):
    for name in ("original", "explicit_contract"):
        run = data[name]
        print(f"{name} ({run['original_replay_matches']} exact replays)")
        for request in REQUESTS:
            by_parent = []
            for parent in PARENTS:
                statuses = [
                    row["status"]
                    for row in run["rows"]
                    if row["request"] == request and row["parent"] == parent
                ]
                by_parent.append(f"{parent} {statuses.count('success')}/{len(statuses)}")
            print(f"  {request}: {', '.join(by_parent)}")


if __name__ == "__main__":
    outcomes = json.loads((ROOT / "outcomes.json").read_bytes())
    verify(outcomes)
    summarize(outcomes)
