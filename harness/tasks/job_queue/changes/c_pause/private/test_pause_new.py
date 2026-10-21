"""Hidden tests for the c_pause change (paused jobs). Never shown to the
writer or the editor.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pause/private/test_pause_new.py
"""

import pytest
from jobs import JobPaused, JobQueue, QueueError


@pytest.fixture
def queue():
    q = JobQueue()
    q.add_job("fetch", 5)
    q.add_job("parse", 1, depends_on=["fetch"])
    q.add_job("notify", 3)
    return q


def state(q):
    jobs = {
        j: (q.get_priority(j), q.get_dependencies(j), q.is_paused(j))
        for j in q.get_pending_jobs()
    }
    return jobs, q.get_ready_jobs(), q.get_pending_jobs(), q.get_completed_jobs()


def test_jobs_start_unpaused(queue):
    assert not queue.is_paused("fetch")
    assert not queue.is_paused("parse")


def test_pausing_hides_the_job_from_ready_only(queue):
    queue.pause_job("notify")
    assert queue.get_ready_jobs() == ["fetch"]
    assert queue.get_pending_jobs() == ["fetch", "parse", "notify"]
    assert queue.get_completed_jobs() == []


def test_resuming_restores_readiness_and_order(queue):
    queue.pause_job("fetch")
    queue.resume_job("fetch")
    assert queue.get_ready_jobs() == ["fetch", "notify"]


def test_pausing_and_resuming_twice_is_harmless(queue):
    queue.pause_job("fetch")
    queue.pause_job("fetch")
    assert queue.is_paused("fetch")
    queue.resume_job("fetch")
    queue.resume_job("fetch")
    assert not queue.is_paused("fetch")
    assert queue.get_ready_jobs() == ["fetch", "notify"]


def test_completing_a_paused_job_raises_job_paused_and_changes_nothing(queue):
    queue.pause_job("fetch")
    before = state(queue)
    with pytest.raises(JobPaused):
        queue.complete_job("fetch")
    assert state(queue) == before


def test_dependents_of_a_paused_job_stay_blocked(queue):
    queue.pause_job("fetch")
    assert "parse" not in queue.get_ready_jobs()
    with pytest.raises(QueueError):
        queue.complete_job("parse")
    queue.resume_job("fetch")
    queue.complete_job("fetch")
    assert queue.get_ready_jobs() == ["notify", "parse"]


def test_a_paused_dependency_does_not_pause_the_dependent(queue):
    queue.complete_job("fetch")
    queue.pause_job("notify")
    assert not queue.is_paused("parse")
    assert queue.get_ready_jobs() == ["parse"]


def test_pausing_a_completed_job_is_refused(queue):
    queue.complete_job("fetch")
    before = state(queue)
    with pytest.raises(QueueError):
        queue.pause_job("fetch")
    assert state(queue) == before
    assert not queue.is_paused("fetch")


def test_resuming_a_completed_job_does_nothing(queue):
    queue.complete_job("fetch")
    queue.resume_job("fetch")
    assert queue.get_completed_jobs() == ["fetch"]
    assert not queue.is_paused("fetch")


@pytest.mark.parametrize("method", ["pause_job", "resume_job", "is_paused"])
@pytest.mark.parametrize("job", ["ghost", None, 1])
def test_pause_methods_raise_key_error_for_unknown_jobs(queue, method, job):
    before = state(queue)
    with pytest.raises(KeyError):
        getattr(queue, method)(job)
    assert state(queue) == before


def test_job_paused_is_a_queue_error():
    assert issubclass(JobPaused, QueueError)


def test_paused_is_reported_after_completed_and_before_blocked(queue):
    queue.pause_job("parse")  # blocked by fetch and paused: paused wins
    with pytest.raises(JobPaused):
        queue.complete_job("parse")
    queue.complete_job("fetch")
    with pytest.raises(QueueError) as info:
        queue.complete_job("fetch")  # completed wins over anything
    assert not isinstance(info.value, JobPaused)


def test_pausing_keeps_priorities_and_dependencies(queue):
    queue.pause_job("parse")
    assert queue.get_priority("parse") == 1
    assert queue.get_dependencies("parse") == ["fetch"]
    queue.complete_job("fetch")
    queue.complete_job("notify")
    assert queue.get_completed_jobs() == ["fetch", "notify"]
