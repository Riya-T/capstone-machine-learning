"""Unit tests for pipeline.evaluator: JUnit parsing, category and step status
rules (infra_error is never a pass or a fail), exact supersedes matching,
separate runs per category, and validate_task on a small synthetic task and
on the real record_store task.

The first group runs without Docker; tests marked `docker` use the sandbox.

Usage:
    uv run pytest tests/test_evaluator.py -rs
"""

import dataclasses
import random
import threading
import time
import uuid
from pathlib import Path

import pytest

from pipeline.config import load_config
from pipeline.evaluator import (
    DESELECT_FILE,
    CategoryResult,
    Evaluator,
    StepEvaluation,
    _Job,
    category_result,
    parse_junit,
    pytest_command,
)
from pipeline.registry import CheckSet, TaskFile, load_task, load_tasks
from pipeline.runner import RunResult, SandboxRunner

from .test_registry import make_task, rules

PILOT = Path(__file__).resolve().parents[1]
OWNER = f"pytest-eval-{uuid.uuid4().hex[:8]}"
CHECKS = CheckSet(
    (TaskFile("tests/test_a.py", b""), TaskFile("private/sub/test_b.py", b"")),
)


def junit(*cases: str) -> bytes:
    return (
        '<?xml version="1.0"?><testsuites><testsuite>'
        + "".join(cases)
        + "</testsuite></testsuites>"
    ).encode()


def run(status="ok", exit_code=0, report=None, detail="", cause="") -> RunResult:
    out = {} if report is None else {"report.xml": report}
    return RunResult(status, exit_code, "", "", False, False, out, 1.0, detail, infra_cause=cause)


PASS_A = '<testcase classname="tests.test_a" name="test_one"/>'
FAIL_B = (
    '<testcase classname="private.sub.test_b" name="test_two"><failure message="boom"/></testcase>'
)


# --- JUnit parsing ----------------------------------------------------------


def test_junit_names_map_back_to_task_relative_ids():
    report = junit(
        PASS_A,
        '<testcase classname="tests.test_a" name="test_p[1-x]"/>',
        '<testcase classname="tests.test_a.TestGroup" name="test_m">'
        '<error message="E"/></testcase>',
        FAIL_B,
        '<testcase classname="tests.test_a" name="test_s"><skipped message="why"/></testcase>',
    )
    assert [(c.node_id, c.outcome) for c in parse_junit(report, CHECKS)] == [
        ("tests/test_a.py::test_one", "passed"),
        ("tests/test_a.py::test_p[1-x]", "passed"),
        ("tests/test_a.py::TestGroup::test_m", "error"),
        ("private/sub/test_b.py::test_two", "failed"),
        ("tests/test_a.py::test_s", "skipped"),
    ]


def test_collection_error_stays_visible():
    report = junit(
        '<testcase classname="" name="tests/test_a.py"><error message="ImportError"/></testcase>'
    )
    (case,) = parse_junit(report, CHECKS)
    assert (case.node_id, case.outcome, case.message) == ("tests/test_a.py", "error", "ImportError")


def test_unreadable_report_raises():
    with pytest.raises(ValueError, match="unreadable JUnit report"):
        parse_junit(b"<testsuites><testcase", CHECKS)


# --- category status --------------------------------------------------------


@pytest.mark.parametrize(
    ("result", "status"),
    [
        (run("ok", 0, junit(PASS_A)), "passed"),
        (run("nonzero_exit", 1, junit(PASS_A, FAIL_B)), "failed"),
        (
            run("nonzero_exit", 2, junit('<testcase classname="" name="x"><error/></testcase>')),
            "failed",
        ),
        (run("nonzero_exit", 5, junit()), "failed"),  # no tests ran
        (run("ok", 0, junit()), "failed"),  # exit 0 but nothing ran: never a pass
        (run("timeout", None), "failed"),  # the program hung: its fault
        (run("oom", 137), "failed"),
        (run("infra_error", None, detail="docker create failed"), "infra_error"),
        (run("nonzero_exit", 4, junit()), "infra_error"),  # pytest usage error: our bug
        (run("nonzero_exit", 3, junit()), "infra_error"),  # pytest internal error
        (run("ok", 0, None), "infra_error"),  # report missing
        (run("ok", 0, b"not xml"), "infra_error"),
    ],
)
def test_category_status(result, status):
    assert category_result("existing", result, CHECKS).status == status


@pytest.mark.parametrize(
    ("result", "cause"),
    [
        (run("infra_error", None, cause="docker_create"), "docker_create"),  # from the runner
        (run("nonzero_exit", 4, junit()), "pytest_harness"),
        (run("ok", 0, None), "missing_report"),
        (run("ok", 0, b"not xml"), "unreadable_report"),
        (run("nonzero_exit", 1, junit(PASS_A, FAIL_B)), ""),  # not an infra error
    ],
)
def test_infra_cause_codes(result, cause):
    got = category_result("existing", result, CHECKS)
    assert got.infra_cause == cause
    if cause:
        assert StepEvaluation(got, got).infra_cause == cause


def test_category_counts():
    got = category_result("existing", run("nonzero_exit", 1, junit(PASS_A, FAIL_B)), CHECKS)
    assert (got.passed, got.total) == (1, 2)
    assert got.to_dict()["failed"] == ["private/sub/test_b.py::test_two"]


def cat(status) -> CategoryResult:
    return CategoryResult("x", status, 0, 0, (), "ok")


@pytest.mark.parametrize(
    ("new", "existing", "status"),
    [
        ("passed", "passed", "success"),
        ("failed", "passed", "fail_new"),
        ("passed", "failed", "fail_existing"),
        ("failed", "failed", "fail_both"),
        ("passed", "infra_error", "infra_error"),
        ("infra_error", "failed", "infra_error"),  # never scored as a failure
        ("infra_error", "passed", "infra_error"),  # never scored as a success
    ],
)
def test_step_status(new, existing, status):
    assert StepEvaluation(cat(new), cat(existing)).status == status


def test_pytest_command_loads_the_exact_deselect_plugin_and_writes_junit():
    cmd = pytest_command(CHECKS)
    assert cmd[:3] == ["python", "-m", "pytest"]
    assert "-p" in cmd and "_pipeline_deselect" in cmd and "no:cacheprovider" in cmd
    assert "--junitxml=/out/report.xml" in cmd
    assert "--deselect" not in cmd  # prefix matching would drop test_x2 with test_x
    assert cmd[-2:] == ["tests/test_a.py", "private/sub/test_b.py"]


def test_program_files_may_not_collide_with_tests_or_harness():
    evaluator = Evaluator(SandboxRunner(load_config(PILOT / "configs" / "pilot_mock.yaml").sandbox))
    with pytest.raises(ValueError, match="collide"):
        evaluator.run_category({DESELECT_FILE: b""}, CHECKS, "existing")
    with pytest.raises(ValueError, match="collide"):
        evaluator.run_category({"tests/test_a.py": b""}, CHECKS, "existing")


class StubRunner:
    """Stands in for SandboxRunner: each run takes a random short time,
    passes, and records how many runs overlapped."""

    image_id = "sha256:stub"

    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def run(self, request):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(random.uniform(0.05, 0.15))
        with self.lock:
            self.active -= 1
        # Echo which job this was, so result order can be checked.
        name = request.files["which.txt"].decode()
        return run("ok", 0, junit(f'<testcase classname="" name="{name}"/>'))


@pytest.mark.parametrize("workers", [1, 4])
def test_run_all_uses_up_to_workers_and_keeps_job_order(workers):
    stub = StubRunner()
    ev = Evaluator(stub, workers=workers)
    jobs = [_Job({"which.txt": str(i).encode()}, CHECKS, "existing") for i in range(12)]
    results = ev.run_all(jobs)
    assert [r.cases[0].node_id for r in results] == [str(i) for i in range(12)]
    assert stub.max_active == workers


# --- with Docker ------------------------------------------------------------


@pytest.fixture(scope="module")
def evaluator():
    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    runner = SandboxRunner(cfg.sandbox, owner=OWNER)
    runner.ensure_image()
    yield Evaluator(runner, workers=cfg.execution.sandbox_workers)
    runner.sweep()


def checks(path: str, source: str, deselect=()) -> CheckSet:
    return CheckSet((TaskFile(path, source.encode()),), tuple(deselect))


SUPERSEDE_TESTS = """
import pytest

def test_x():
    assert False, "superseded"

@pytest.mark.parametrize("n", [1, 2])
def test_x_param(n):
    assert True

@pytest.mark.parametrize("n", [1, 2])
def test_y(n):
    assert False, "superseded too"

def test_x2():
    assert False, "must still count"

class TestGroup:
    def test_m(self):
        assert False, "superseded"

    def test_m2(self):
        assert True
"""


@pytest.mark.docker
def test_supersedes_matches_exact_test_ids_only(evaluator):
    drop = ["t/test_sup.py::test_x", "t/test_sup.py::test_y", "t/test_sup.py::TestGroup::test_m"]
    got = evaluator.run_category({}, checks("t/test_sup.py", SUPERSEDE_TESTS, drop), "existing")
    assert {c.node_id: c.outcome for c in got.cases} == {
        "t/test_sup.py::test_x_param[1]": "passed",  # test_x does not drop test_x_param
        "t/test_sup.py::test_x_param[2]": "passed",
        "t/test_sup.py::test_x2": "failed",  # test_x does not drop test_x2
        "t/test_sup.py::TestGroup::test_m2": "passed",
    }  # test_y[1], test_y[2] (parametrized cases of a dropped test) are gone
    assert got.status == "failed"


@pytest.mark.docker
@pytest.mark.slow
def test_categories_run_separately(evaluator, tmp_path):
    # A hang in the new-feature tests can't affect the existing-behavior run.
    fast = dataclasses.replace(evaluator.runner.cfg, timeout_s=8.0)
    ev = Evaluator(SandboxRunner(fast, owner=OWNER), workers=2)
    program = {"m.py": b"def a():\n    return 1\n"}
    hang = ev.run_category(
        program, checks("t/test_new.py", "def test_n():\n    while True: pass\n"), "new_feature"
    )
    ok = ev.run_category(
        program,
        checks("t/test_old.py", "from m import a\n\ndef test_o():\n    assert a() == 1\n"),
        "existing",
    )
    assert (hang.status, hang.run_status) == ("failed", "timeout")
    assert (ok.status, ok.passed, ok.total) == ("passed", 1, 1)
    assert StepEvaluation(hang, ok).status == "fail_new"


@pytest.mark.docker
def test_import_error_in_the_program_fails_the_category(evaluator):
    got = evaluator.run_category(
        {"m.py": b"raise RuntimeError('broken at import')\n"},
        checks("t/test_m.py", "import m\n\ndef test_m():\n    pass\n"),
        "initial",
    )
    assert got.status == "failed"


@pytest.mark.docker
def test_infrastructure_failure_is_infra_error_everywhere(tmp_path):
    runner = SandboxRunner(load_config(PILOT / "configs" / "pilot_mock.yaml").sandbox, owner=OWNER)
    runner._image_id = "pipeline-sandbox:does-not-exist"
    ev = Evaluator(runner, workers=4)
    one = ev.run_category(
        {"m.py": b""}, checks("t/test_m.py", "def test_m():\n    pass\n"), "existing"
    )
    assert one.status == "infra_error"
    assert StepEvaluation(one, one).status == "infra_error"
    make_functional_task(tmp_path)
    problems = ev.validate_task(load_task(tmp_path / "t", rules(tmp_path)))
    assert problems and all("infrastructure error" in p for p in problems)


# A small task with real behavior: v0 has a(); change ca adds b(); cb adds c().
FUNCTIONAL = {
    "ref/v0/m.py": "def a():\n    return 1\n",
    "ref/ca/m.py": "def a():\n    return 1\n\n\ndef b():\n    return 2\n",
    "ref/cb/m.py": "def a():\n    return 1\n\n\ndef c():\n    return 3\n",
    "ref/ca_cb/m.py": (
        "def a():\n    return 1\n\n\ndef b():\n    return 2\n\n\ndef c():\n    return 3\n"
    ),
    "bugs/b0/m.py": "def a():\n    return 0\n",
    "public/test_pub.py": "from m import a\n\n\ndef test_pub():\n    assert a() is not None\n",
    "private/test_priv.py": (
        "from m import a\n\n\ndef test_priv():\n    assert a() == 1\n\n\n"
        "def test_old_rule():\n    assert a() == 1\n"
    ),
    "changes/ca/test_ca_pub.py": "import m\n\n\ndef test_ca_pub():\n    assert hasattr(m, 'b')\n",
    "changes/ca/test_ca_new.py": "from m import b\n\n\ndef test_ca_new():\n    assert b() == 2\n",
    "changes/cb/test_cb_pub.py": "import m\n\n\ndef test_cb_pub():\n    assert hasattr(m, 'c')\n",
    "changes/cb/test_cb_new.py": "from m import c\n\n\ndef test_cb_new():\n    assert c() == 3\n",
}


def make_functional_task(tasks_dir: Path, overrides=None) -> None:
    files = {**FUNCTIONAL, **(overrides or {})}

    def edit(root, manifest):
        for rel, text in files.items():
            (root / rel).write_text(text)

    make_task(tasks_dir, edit=edit)


def validate(evaluator, tasks_dir, overrides=None) -> list[str]:
    make_functional_task(tasks_dir, overrides)
    return evaluator.validate_task(load_task(tasks_dir / "t", rules(tasks_dir)))


@pytest.mark.docker
@pytest.mark.slow
def test_sound_task_has_no_problems(evaluator, tmp_path):
    assert validate(evaluator, tmp_path) == []


@pytest.mark.docker
@pytest.mark.slow
def test_change_tests_that_the_old_program_already_passes_are_flagged(evaluator, tmp_path):
    # cb's new test no longer needs c(): doing nothing would pass it.
    problems = validate(
        evaluator, tmp_path, {"changes/cb/test_cb_new.py": "def test_cb_new():\n    assert True\n"}
    )
    assert problems == [
        "s1 step 2 program before cb: should fail new_feature but passed (1/1; failing [])",
        "s2 step 1 program before cb: should fail new_feature but passed (1/1; failing [])",
    ]


@pytest.mark.docker
@pytest.mark.slow
def test_reference_that_drops_earlier_behavior_is_flagged(evaluator, tmp_path):
    # The {ca, cb} reference forgot b(): it fails the existing tests in s1
    # (ca came first) and the new-feature tests in s2 (ca came second).
    problems = validate(evaluator, tmp_path, {"ref/ca_cb/m.py": FUNCTIONAL["ref/cb/m.py"]})
    assert any(
        p.startswith("s1 step 2 ref/ca_cb: should pass existing but failed") for p in problems
    )
    assert any(
        p.startswith("s2 step 2 ref/ca_cb: should pass new_feature but failed") for p in problems
    )


@pytest.mark.docker
@pytest.mark.slow
def test_planted_bug_that_passes_is_flagged(evaluator, tmp_path):
    problems = validate(evaluator, tmp_path, {"bugs/b0/m.py": FUNCTIONAL["ref/v0/m.py"]})
    assert problems == ["bugs/b0: should fail initial but passed (2/2; failing [])"]


@pytest.mark.docker
@pytest.mark.slow
def test_record_store_task_is_sound(evaluator):
    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    assert evaluator.validate_task(task) == []


@pytest.mark.docker
def test_record_store_supersedes_drops_exactly_one_initial_test(evaluator):
    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    plain = evaluator.run_category(task.reference, CheckSet(task.private_tests), "initial")
    step = task.sequence("s2").steps[0]
    with_unique = evaluator.check_step(step.reference, step)
    assert with_unique.existing.total == plain.total - 1
    assert with_unique.status == "success"
    dropped = "private/test_initial.py::test_duplicate_emails_are_allowed"
    assert dropped not in {c.node_id for c in with_unique.existing.cases}
