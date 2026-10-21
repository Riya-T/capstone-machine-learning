"""Public checks for jobs.py.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest public/test_jobs_public.py
"""

import pytest
from jobs import JobQueue, QueueError


@pytest.fixture
def queue():
    q = JobQueue()
    q.add_job("fetch", 5)
    q.add_job("parse", 1, depends_on=["fetch"])
    q.add_job("notify", 3)
    return q


def test_ready_jobs_come_highest_priority_first(queue):
    queue.add_job("cleanup", 3)
    assert queue.get_ready_jobs() == ["fetch", "notify", "cleanup"]


def test_a_job_becomes_ready_when_its_dependency_is_completed(queue):
    assert "parse" not in queue.get_ready_jobs()
    queue.complete_job("fetch")
    assert queue.get_ready_jobs() == ["notify", "parse"]


def test_completing_a_job_that_is_not_ready_raises(queue):
    with pytest.raises(QueueError):
        queue.complete_job("parse")
    assert queue.get_completed_jobs() == []


def test_completed_jobs_leave_pending_in_completion_order(queue):
    queue.complete_job("notify")
    queue.complete_job("fetch")
    assert queue.get_completed_jobs() == ["notify", "fetch"]
    assert queue.get_pending_jobs() == ["parse"]


def test_dependencies_and_priority_can_be_read_back(queue):
    assert queue.get_dependencies("parse") == ["fetch"]
    assert queue.get_dependencies("fetch") == []
    assert queue.get_priority("notify") == 3


def test_an_unknown_job_raises_key_error(queue):
    with pytest.raises(KeyError):
        queue.complete_job("ghost")
    with pytest.raises(KeyError):
        queue.get_priority("ghost")
