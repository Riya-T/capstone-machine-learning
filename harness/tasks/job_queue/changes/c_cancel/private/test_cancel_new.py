"""Hidden tests for the c_cancel change (cancelling jobs). Never shown to the
writer or the editor.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from jobs import JobQueue, QueueError


@pytest.fixture
def queue():
    q = JobQueue()
    q.add_job("fetch", 5)
    q.add_job("parse", 1, depends_on=["fetch"])
    q.add_job("notify", 3)
    q.add_job("archive", 2, depends_on=["parse", "notify"])
    return q


def state(q):
    jobs = {j: (q.get_priority(j), q.get_dependencies(j)) for j in q.get_pending_jobs()}
    return jobs, q.get_ready_jobs(), q.get_pending_jobs(), q.get_completed_jobs(), q.get_cancelled_jobs()


def test_nothing_is_cancelled_to_begin_with(queue):
    assert queue.get_cancelled_jobs() == []


def test_a_cancelled_job_leaves_pending_and_ready(queue):
    queue.cancel_job("archive")
    assert queue.get_pending_jobs() == ["fetch", "parse", "notify"]
    assert queue.get_ready_jobs() == ["fetch", "notify"]
    assert queue.get_completed_jobs() == []


def test_cancellations_are_listed_in_order(queue):
    queue.cancel_job("archive")
    queue.cancel_job("notify")
    assert queue.get_cancelled_jobs() == ["archive", "notify"]


@pytest.mark.parametrize(
    "call",
    [
        lambda q: q.get_priority("archive"),
        lambda q: q.get_dependencies("archive"),
        lambda q: q.complete_job("archive"),
        lambda q: q.cancel_job("archive"),
        lambda q: q.add_job("extra", 1, depends_on=["archive"]),
    ],
)
def test_a_cancelled_job_counts_as_unknown(queue, call):
    queue.cancel_job("archive")
    before = state(queue)
    with pytest.raises(KeyError):
        call(queue)
    assert state(queue) == before


def test_a_reused_id_is_a_fresh_job_at_the_end(queue):
    queue.cancel_job("archive")
    queue.add_job("archive", 7)
    assert queue.get_pending_jobs() == ["fetch", "parse", "notify", "archive"]
    assert queue.get_dependencies("archive") == []
    assert queue.get_priority("archive") == 7
    assert queue.get_ready_jobs() == ["archive", "fetch", "notify"]


def test_a_reused_id_cancelled_again_is_listed_twice(queue):
    queue.cancel_job("archive")
    queue.add_job("archive", 7)
    queue.cancel_job("archive")
    assert queue.get_cancelled_jobs() == ["archive", "archive"]
    assert "archive" not in queue.get_pending_jobs()


def test_a_completed_job_cannot_be_cancelled(queue):
    queue.complete_job("notify")
    before = state(queue)
    with pytest.raises(QueueError):
        queue.cancel_job("notify")
    assert state(queue) == before
    assert queue.get_completed_jobs() == ["notify"]


def test_a_dependency_of_an_open_job_cannot_be_cancelled(queue):
    before = state(queue)
    with pytest.raises(QueueError):
        queue.cancel_job("fetch")  # parse waits for it
    with pytest.raises(QueueError):
        queue.cancel_job("notify")  # archive waits for it
    assert state(queue) == before


def test_a_dependency_becomes_cancellable_once_every_dependent_is_gone(queue):
    queue.add_job("report", 4, depends_on=["fetch"])
    queue.cancel_job("archive")
    queue.cancel_job("parse")
    with pytest.raises(QueueError):
        queue.cancel_job("fetch")  # report still waits for it
    queue.cancel_job("report")
    queue.cancel_job("fetch")
    assert queue.get_cancelled_jobs() == ["archive", "parse", "report", "fetch"]
    assert queue.get_pending_jobs() == ["notify"]
    assert queue.get_ready_jobs() == ["notify"]


def test_cancelling_a_dependency_once_its_dependent_is_gone(queue):
    queue.cancel_job("archive")
    queue.cancel_job("notify")
    assert queue.get_pending_jobs() == ["fetch", "parse"]


@pytest.mark.parametrize("job", ["ghost", None, 1])
def test_cancelling_an_unknown_job_raises_key_error(queue, job):
    before = state(queue)
    with pytest.raises(KeyError):
        queue.cancel_job(job)
    assert state(queue) == before


def test_a_completed_job_with_open_dependents_reports_completed(queue):
    queue.complete_job("fetch")
    with pytest.raises(QueueError):
        queue.cancel_job("fetch")
    assert queue.get_completed_jobs() == ["fetch"]
    assert queue.get_cancelled_jobs() == []
