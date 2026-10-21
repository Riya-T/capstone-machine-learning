"""Public checks for the c_deprules change (adding dependencies with rules).
Shown to the editor, never to the writer.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest changes/c_deprules/public/test_deprules_public.py
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


def test_an_added_dependency_blocks_the_job(queue):
    queue.add_dependency("notify", "fetch")
    assert queue.get_dependencies("notify") == ["fetch"]
    assert queue.get_ready_jobs() == ["fetch"]
    queue.complete_job("fetch")
    assert queue.get_ready_jobs() == ["notify", "parse"]


def test_a_cycle_is_refused(queue):
    with pytest.raises(QueueError):
        queue.add_dependency("fetch", "parse")
    assert queue.get_dependencies("fetch") == []


def test_a_job_cannot_depend_on_itself(queue):
    with pytest.raises(ValueError):
        queue.add_dependency("fetch", "fetch")
