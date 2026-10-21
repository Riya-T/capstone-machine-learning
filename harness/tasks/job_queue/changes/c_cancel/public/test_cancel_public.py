"""Public checks for the c_cancel change (cancelling jobs). Shown to the
editor, never to the writer.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
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


def test_a_cancelled_job_disappears(queue):
    queue.cancel_job("notify")
    assert queue.get_pending_jobs() == ["fetch", "parse"]
    assert queue.get_ready_jobs() == ["fetch"]
    assert queue.get_cancelled_jobs() == ["notify"]
    with pytest.raises(KeyError):
        queue.get_priority("notify")


def test_a_job_others_wait_for_cannot_be_cancelled(queue):
    with pytest.raises(QueueError):
        queue.cancel_job("fetch")
    assert queue.get_pending_jobs() == ["fetch", "parse", "notify"]


def test_a_cancelled_id_can_be_reused(queue):
    queue.cancel_job("notify")
    queue.add_job("notify", 9)
    assert queue.get_ready_jobs() == ["notify", "fetch"]
