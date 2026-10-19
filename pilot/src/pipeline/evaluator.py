"""Contract evaluator: runs a program against a task's test categories in the
sandbox and reports each category separately.

Each category (initial, public, new_feature, existing) is a separate pytest
run in a fresh container, so a crash, hang or import error in one category
can't hide or fake results in another. Results come from the JUnit XML report
pytest writes to /out, mapped back to task-relative test ids such as
"private/test_initial.py::test_ids_start_at_one_and_increase".

Superseded tests are removed at collection by a small pytest plugin placed
next to the program. It matches the exact test id, plus parametrized cases of
it ("test_x[a]"), unlike pytest's --deselect, which matches by prefix and
would also drop "test_x2". Superseded tests therefore never run.

Infrastructure failures (Docker errors, a missing report, an unexplained
SIGKILL) give status "infra_error", which callers retry and never score.

Usage:
    evaluator = Evaluator(SandboxRunner(cfg.sandbox, owner=run_id),
                          workers=cfg.execution.sandbox_workers)
    initial = evaluator.check_initial(program, task)      # initial.passed
    step = evaluator.check_step(program, task.sequence("s1").steps[0])
    step.status            # success | fail_new | fail_existing | fail_both | infra_error
    problems = evaluator.validate_task(task)              # [] when the task is sound
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

from .registry import CheckSet, Program, Step, Task
from .runner import RunRequest, RunResult, SandboxRunner

Category = Literal["initial", "public", "new_feature", "existing"]
CategoryStatus = Literal["passed", "failed", "infra_error"]
StepStatus = Literal["success", "fail_new", "fail_existing", "fail_both", "infra_error"]
Outcome = Literal["passed", "failed", "error", "skipped"]

REPORT = "report.xml"
PLUGIN_MODULE = "_pipeline_deselect"
DESELECT_FILE = "_pipeline_deselect.json"

# Loaded into pytest inside the sandbox (`-p _pipeline_deselect`). It reads
# the exact test ids to drop from the JSON file next to it.
PLUGIN_SOURCE = '''"""Pytest plugin placed in the sandbox by pipeline.evaluator: drops the
superseded tests listed in _pipeline_deselect.json, matching the exact test
id (and its parametrized cases), never by prefix.

Usage:
    python -m pytest -p _pipeline_deselect ...
"""

import json
import os


def pytest_collection_modifyitems(config, items):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pipeline_deselect.json")
    with open(path, encoding="utf-8") as f:
        drop_ids = set(json.load(f))
    keep, drop = [], []
    for item in items:
        (drop if item.nodeid.split("[", 1)[0] in drop_ids else keep).append(item)
    if drop:
        config.hook.pytest_deselected(items=drop)
        items[:] = keep
'''


@dataclass(frozen=True)
class CaseResult:
    node_id: str  # "path::test" or "path::Class::test", with "[params]" if any
    outcome: Outcome
    message: str = ""


@dataclass(frozen=True)
class CategoryResult:
    category: str
    status: CategoryStatus
    passed: int
    total: int
    cases: tuple[CaseResult, ...]
    run_status: str  # the runner's status, e.g. "nonzero_exit" or "timeout"
    detail: str = ""
    # For infra_error: the runner's cause, or pytest_harness (pytest exit 3
    # or 4), missing_report or unreadable_report.
    infra_cause: str = ""
    # pytest's console output (shown to the editor for public checks).
    output: str = ""

    def to_dict(self) -> dict:
        """Compact JSON form for the store (initial check reports)."""
        return {
            "status": self.status,
            "passed": self.passed,
            "total": self.total,
            "run_status": self.run_status,
            "failed": [c.node_id for c in self.cases if c.outcome != "passed"],
            "detail": self.detail,
        }


@dataclass(frozen=True)
class InitialEvaluation:
    public: CategoryResult
    initial: CategoryResult

    @property
    def status(self) -> CategoryStatus:
        return _combine(self.public, self.initial)

    @property
    def passed(self) -> bool:
        return self.status == "passed"


@dataclass(frozen=True)
class StepEvaluation:
    new_feature: CategoryResult
    existing: CategoryResult

    @property
    def status(self) -> StepStatus:
        """Proposal: a change succeeds only if the new-feature tests and the
        existing-behavior tests both pass. Any infrastructure failure makes
        the whole step infra_error, so it is retried rather than scored."""
        new, old = self.new_feature.status, self.existing.status
        if "infra_error" in (new, old):
            return "infra_error"
        if new == "passed" and old == "passed":
            return "success"
        if new == "passed":
            return "fail_existing"
        if old == "passed":
            return "fail_new"
        return "fail_both"

    @property
    def infra_cause(self) -> str:
        """Cause code of the first category with an infrastructure error."""
        for category in (self.new_feature, self.existing):
            if category.status == "infra_error":
                return category.infra_cause
        return ""


@dataclass(frozen=True)
class _Job:
    """One pytest run: a program against one check set."""

    program: Program
    checks: CheckSet
    category: str


class Evaluator:
    def __init__(self, runner: SandboxRunner, workers: int = 1) -> None:
        self.runner = runner
        # Sandbox runs that are independent of each other run this many at a
        # time (config: execution.sandbox_workers). Each run has its own
        # container and temp dir, so runs share nothing.
        self.workers = workers

    def run_all(self, jobs: Sequence[_Job]) -> list[CategoryResult]:
        """Run independent jobs, up to `workers` at once; results come back
        in the order of `jobs`, so output never depends on timing."""
        if self.workers == 1 or len(jobs) <= 1:
            return [self.run_category(j.program, j.checks, j.category) for j in jobs]
        # Resolve the image once up front; otherwise the first runs would
        # race to build or inspect it.
        _ = self.runner.image_id
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            return list(
                pool.map(lambda j: self.run_category(j.program, j.checks, j.category), jobs)
            )

    # -- single categories --

    def run_category(self, program: Program, checks: CheckSet, category: str) -> CategoryResult:
        files = dict(program)
        overlap = set(files) & (
            {f.path for f in checks.files} | {f"{PLUGIN_MODULE}.py", DESELECT_FILE}
        )
        if overlap:
            raise ValueError(f"program files collide with test or harness files: {sorted(overlap)}")
        files.update({f.path: f.content for f in checks.files})
        files[f"{PLUGIN_MODULE}.py"] = PLUGIN_SOURCE.encode("utf-8")
        files[DESELECT_FILE] = json.dumps(sorted(checks.deselect)).encode("utf-8")
        result = self.runner.run(RunRequest(files=files, command=pytest_command(checks)))
        return category_result(category, result, checks)

    def check_initial(self, program: Program, task: Task) -> InitialEvaluation:
        public, initial = self.run_all(
            [
                _Job(program, CheckSet(task.public_checks), "public"),
                _Job(program, CheckSet(task.private_tests), "initial"),
            ]
        )
        return InitialEvaluation(public=public, initial=initial)

    def check_step(self, program: Program, step: Step) -> StepEvaluation:
        new_feature, existing = self.run_all(
            [
                _Job(program, step.tests.new_feature, "new_feature"),
                _Job(program, step.tests.existing, "existing"),
            ]
        )
        return StepEvaluation(new_feature=new_feature, existing=existing)

    # -- task validation --

    def validate_task(self, task: Task) -> list[str]:
        """Check a task's tests against its references and planted bugs;
        returns a list of problems (empty when the task is sound):

        - each reference passes every category where it is used;
        - each planted bug fails exactly its must_fail categories and passes
          its must_pass categories;
        - the program before each change fails that change's new-feature
          tests, so the tests can't be passed by doing nothing.
        """
        # Every check is independent, so they are listed first and run
        # together; each is (label, job, whether it should pass).
        expectations: list[tuple[str, _Job, bool]] = []

        def expect(label: str, program: Program, checks: CheckSet, category: str, want: bool):
            expectations.append((label, _Job(program, checks, category), want))

        initial = {"public": CheckSet(task.public_checks), "initial": CheckSet(task.private_tests)}
        for category, checks in initial.items():
            expect("reference v0", task.reference, checks, category, True)
        for bug in task.planted_bugs:
            for category in sorted(bug.must_fail | bug.must_pass):
                expect(
                    bug.path, bug.program, initial[category], category, category in bug.must_pass
                )

        for sequence in task.sequences:
            before = task.reference
            for step in sequence.steps:
                where = f"{sequence.id} step {step.number}"
                sets = {
                    "public": step.tests.public,
                    "new_feature": step.tests.new_feature,
                    "existing": step.tests.existing,
                }
                for category, checks in sets.items():
                    expect(f"{where} {step.reference_path}", step.reference, checks, category, True)
                expect(f"{where} program before {step.change.id}", before,
                       step.tests.new_feature, "new_feature", False)  # fmt: skip
                for bug in step.planted_bugs:
                    for category in sorted(bug.must_fail | bug.must_pass):
                        expect(f"{where} {bug.path}", bug.program, sets[category], category,
                               category in bug.must_pass)  # fmt: skip
                before = step.reference

        results = self.run_all([job for _, job, _ in expectations])
        problems: list[str] = []
        for (label, job, want), got in zip(expectations, results, strict=True):
            if got.status == "infra_error":
                problems.append(f"{label}: infrastructure error ({got.detail})")
            elif (got.status == "passed") != want:
                verb = "should pass" if want else "should fail"
                failing = [c.node_id for c in got.cases if c.outcome != "passed"]
                problems.append(
                    f"{label}: {verb} {job.category} but {got.status} "
                    f"({got.passed}/{got.total}; failing {failing[:5]})"
                )
        return problems


def pytest_command(checks: CheckSet) -> list[str]:
    """The pytest call for one category. COLUMNS=200 stops pytest from
    cutting summary lines at 80 characters (which hid e.g. "has no attribute
    'add'" from the editor), and --tb=short keeps each failure's traceback to
    the lines that matter, so the cause survives the editor's output limit."""
    return [
        "env", "COLUMNS=200",
        "python", "-m", "pytest",
        "-q",
        "--tb=short",
        "-p", "no:cacheprovider",
        "-p", PLUGIN_MODULE,
        f"--junitxml=/out/{REPORT}",
        "-o", "junit_family=xunit2",
        "--rootdir=/work",
        *[f.path for f in checks.files],
    ]  # fmt: skip


def category_result(category: str, run: RunResult, checks: CheckSet) -> CategoryResult:
    """Turn one pytest run into a category result.

    passed: pytest exited 0 and the report lists at least one test, all
        passing.
    failed: the program's fault: test failures or errors (exit 1), errors
        during collection such as an import error (exit 2), no tests run
        (exit 5), a timeout, or running out of memory.
    infra_error: the runner failed, pytest reported a usage or internal error
        (exit 3 or 4, a harness bug), or the report is missing or unreadable
        after pytest ran.
    """

    def result(status: CategoryStatus, cases=(), detail="", cause="") -> CategoryResult:
        passed = sum(c.outcome == "passed" for c in cases)
        return CategoryResult(
            category,
            status,
            passed,
            len(cases),
            tuple(cases),
            run.status,
            detail,
            infra_cause=cause,
            output=run.stdout + run.stderr,
        )

    if run.status == "infra_error":
        return result("infra_error", detail=run.detail, cause=run.infra_cause)
    if run.status in ("timeout", "oom"):
        return result("failed", detail=f"pytest run ended by {run.status}")
    if run.exit_code in (3, 4):
        detail = f"pytest exit {run.exit_code}: {run.stdout[-500:]}"
        return result("infra_error", detail=detail, cause="pytest_harness")

    report = run.out_files.get(REPORT)
    if report is None:
        return result("infra_error", detail="pytest wrote no JUnit report", cause="missing_report")
    try:
        cases = parse_junit(report, checks)
    except ValueError as exc:
        return result("infra_error", detail=str(exc), cause="unreadable_report")
    if run.exit_code == 0 and cases and all(c.outcome == "passed" for c in cases):
        return result("passed", cases)
    return result("failed", cases, detail=f"pytest exit {run.exit_code}")


def parse_junit(report: bytes, checks: CheckSet) -> list[CaseResult]:
    """Read a pytest JUnit XML report into task-relative test ids.

    JUnit names a test by a dotted "classname" (the file path without ".py",
    plus a test class if any) and a "name". The dotted form is mapped back to
    the file through the check set's own paths, which are known exactly.
    """
    try:
        root = ET.fromstring(report)
    except ET.ParseError as exc:
        raise ValueError(f"unreadable JUnit report: {exc}") from None
    modules = {_dotted(f.path): f.path for f in checks.files}
    cases = []
    for case in root.iter("testcase"):
        classname, name = case.get("classname", ""), case.get("name", "")
        node_id = _node_id(classname, name, modules)
        outcome: Outcome = "passed"
        message = ""
        for tag in ("failure", "error", "skipped"):
            element = case.find(tag)
            if element is not None:
                outcome = "failed" if tag == "failure" else tag  # type: ignore[assignment]
                message = (element.get("message") or "")[:500]
                break
        cases.append(CaseResult(node_id, outcome, message))
    return cases


def _dotted(path: str) -> str:
    return ".".join(PurePosixPath(path).with_suffix("").parts)


def _node_id(classname: str, name: str, modules: Mapping[str, str]) -> str:
    if classname in modules:
        return f"{modules[classname]}::{name}"
    module, _, cls = classname.rpartition(".")
    if module in modules:
        return f"{modules[module]}::{cls}::{name}"
    # Collection errors are reported with an empty classname and the file as
    # the name; keep whatever pytest gave so the failure stays visible.
    return f"{classname}::{name}" if classname else name


def _combine(*results: CategoryResult) -> CategoryStatus:
    statuses = {r.status for r in results}
    if "infra_error" in statuses:
        return "infra_error"
    return "passed" if statuses == {"passed"} else "failed"
