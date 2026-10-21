"""Public checks for the c_pause change (paused jobs). Shown to the editor,
never to the writer.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pause/public/test_pause_public.py
"""

import pytest
from jobs import JobPaused, JobQueue


@pytest.fixture
def queue():
    q = JobQueue()
    q.add_job("fetch", 5)
    q.add_job("notify", 3)
    return q


def test_a_paused_job_is_pending_but_not_ready(queue):
    queue.pause_job("fetch")
    assert queue.is_paused("fetch")
    assert queue.get_ready_jobs() == ["notify"]
    assert queue.get_pending_jobs() == ["fetch", "notify"]


def test_a_paused_job_cannot_be_completed_until_resumed(queue):
    queue.pause_job("fetch")
    with pytest.raises(JobPaused):
        queue.complete_job("fetch")
    queue.resume_job("fetch")
    assert not queue.is_paused("fetch")
    queue.complete_job("fetch")
    assert queue.get_completed_jobs() == ["fetch"]
