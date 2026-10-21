"""Hidden tests for the c_deprules change (adding dependencies with rules).
Never shown to the writer or the editor.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest changes/c_deprules/private/test_deprules_new.py
"""

import pytest
from jobs import JobQueue, QueueError


@pytest.fixture
def queue():
    q = JobQueue()
    q.add_job("fetch", 5)
    q.add_job("parse", 1, depends_on=["fetch"])
    q.add_job("index", 2, depends_on=["parse"])
    q.add_job("notify", 3)
    return q


def state(q):
    jobs = {j: (q.get_priority(j), q.get_dependencies(j)) for j in q.get_pending_jobs()}
    return jobs, q.get_ready_jobs(), q.get_pending_jobs(), q.get_completed_jobs()


def test_a_late_dependency_is_appended_and_enforced(queue):
    queue.add_dependency("index", "notify")
    queue.add_dependency("index", "fetch")
    assert queue.get_dependencies("index") == ["parse", "notify", "fetch"]
    queue.complete_job("fetch")
    queue.complete_job("parse")
    assert "index" not in queue.get_ready_jobs()
    with pytest.raises(QueueError):
        queue.complete_job("index")
    queue.complete_job("notify")
    assert queue.get_ready_jobs() == ["index"]


def test_a_dependency_on_a_completed_job_is_satisfied_already(queue):
    queue.complete_job("fetch")
    queue.add_dependency("notify", "fetch")
    assert queue.get_ready_jobs() == ["notify", "parse"]
    queue.complete_job("notify")
    assert queue.get_completed_jobs() == ["fetch", "notify"]


def test_dependencies_added_late_affect_only_that_job(queue):
    queue.add_dependency("notify", "fetch")
    assert queue.get_dependencies("fetch") == []
    assert queue.get_dependencies("parse") == ["fetch"]
    assert queue.get_priority("notify") == 3


@pytest.mark.parametrize(
    "job, dep",
    [("ghost", "fetch"), ("fetch", "ghost"), (None, "fetch"), ("fetch", 1), ("ghost", "ghost")],
)
def test_unknown_jobs_in_either_position_raise_key_error(queue, job, dep):
    before = state(queue)
    with pytest.raises(KeyError):
        queue.add_dependency(job, dep)
    assert state(queue) == before


def test_depending_on_itself_is_refused(queue):
    before = state(queue)
    with pytest.raises(ValueError):
        queue.add_dependency("notify", "notify")
    assert state(queue) == before


def test_a_completed_job_cannot_gain_a_dependency(queue):
    queue.complete_job("fetch")
    before = state(queue)
    with pytest.raises(QueueError):
        queue.add_dependency("fetch", "notify")
    assert state(queue) == before
    assert queue.get_dependencies("fetch") == []


def test_a_repeated_dependency_is_refused(queue):
    before = state(queue)
    with pytest.raises(QueueError):
        queue.add_dependency("parse", "fetch")
    assert state(queue) == before
    assert queue.get_dependencies("parse") == ["fetch"]


def test_a_direct_cycle_is_refused(queue):
    before = state(queue)
    with pytest.raises(QueueError):
        queue.add_dependency("fetch", "parse")
    assert state(queue) == before


def test_a_cycle_through_other_jobs_is_refused(queue):
    before = state(queue)
    with pytest.raises(QueueError):
        queue.add_dependency("fetch", "index")  # index -> parse -> fetch
    assert state(queue) == before
    queue.add_dependency("notify", "index")
    with pytest.raises(QueueError):
        queue.add_dependency("fetch", "notify")  # notify -> index -> parse -> fetch


def test_a_shared_dependency_is_not_a_cycle(queue):
    queue.add_dependency("notify", "fetch")
    queue.add_dependency("notify", "parse")
    assert queue.get_dependencies("notify") == ["fetch", "parse"]
    assert queue.get_ready_jobs() == ["fetch"]


def test_a_completed_job_is_refused_whatever_the_graph_looks_like():
    q = JobQueue()
    q.add_job("a", 1)
    q.add_job("b", 1, depends_on=["a"])
    q.complete_job("a")
    with pytest.raises(QueueError):  # a is completed, so the error is for that
        q.add_dependency("a", "b")
    assert q.get_dependencies("a") == []


def test_self_before_completed_before_repeat_before_cycle(queue):
    queue.complete_job("fetch")
    with pytest.raises(ValueError):
        queue.add_dependency("fetch", "fetch")
    with pytest.raises(QueueError):
        queue.add_dependency("fetch", "parse")
    queue.add_dependency("notify", "parse")
    with pytest.raises(QueueError):
        queue.add_dependency("notify", "parse")
    assert queue.get_dependencies("notify") == ["parse"]
