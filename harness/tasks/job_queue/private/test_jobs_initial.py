"""Hidden tests for the initial job_queue spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with jobs.py importable, e.g. in the sandbox):
    python -m pytest private/test_jobs_initial.py
"""

import pytest
from jobs import JobQueue, QueueError

BAD_IDS = ["", None, 7]
BAD_PRIORITIES = [1.5, "3", None, True]


@pytest.fixture
def queue():
    q = JobQueue()
    q.add_job("fetch", 5)
    q.add_job("parse", 1, depends_on=["fetch"])
    q.add_job("notify", 3)
    return q


def state(q):
    """Every job's priority and dependencies plus the three lists, to check
    that a failed call changed nothing."""
    jobs = {j: (q.get_priority(j), q.get_dependencies(j)) for j in q.get_pending_jobs()}
    return jobs, q.get_ready_jobs(), q.get_pending_jobs(), q.get_completed_jobs()


# --- adding jobs ------------------------------------------------------------


def test_a_new_queue_is_empty():
    q = JobQueue()
    assert q.get_ready_jobs() == []
    assert q.get_pending_jobs() == []
    assert q.get_completed_jobs() == []


def test_jobs_without_dependencies_are_ready_at_once():
    q = JobQueue()
    q.add_job("a", 1)
    assert q.get_ready_jobs() == ["a"]
    assert q.get_dependencies("a") == []


def test_pending_jobs_keep_add_order(queue):
    queue.add_job("archive", 9)
    assert queue.get_pending_jobs() == ["fetch", "parse", "notify", "archive"]


def test_ready_jobs_are_sorted_highest_priority_first(queue):
    queue.add_job("archive", 9)
    queue.add_job("report", -2)
    assert queue.get_ready_jobs() == ["archive", "fetch", "notify", "report"]


def test_equal_priorities_keep_add_order():
    q = JobQueue()
    for name in ["zeta", "alpha", "mid"]:
        q.add_job(name, 2)
    q.add_job("top", 3)
    assert q.get_ready_jobs() == ["top", "zeta", "alpha", "mid"]


def test_zero_and_negative_priorities_are_allowed():
    q = JobQueue()
    q.add_job("low", -5)
    q.add_job("zero", 0)
    assert q.get_priority("low") == -5
    assert q.get_ready_jobs() == ["zero", "low"]


@pytest.mark.parametrize("bad", BAD_IDS)
def test_invalid_job_ids_are_rejected(queue, bad):
    before = state(queue)
    with pytest.raises(ValueError):
        queue.add_job(bad, 1)
    assert state(queue) == before


@pytest.mark.parametrize("bad", BAD_PRIORITIES)
def test_invalid_priorities_are_rejected(queue, bad):
    before = state(queue)
    with pytest.raises(ValueError):
        queue.add_job("archive", bad)
    assert state(queue) == before


def test_adding_an_existing_id_is_rejected(queue):
    before = state(queue)
    with pytest.raises(QueueError):
        queue.add_job("fetch", 99, depends_on=["notify"])
    assert state(queue) == before
    assert queue.get_priority("fetch") == 5
    assert queue.get_dependencies("fetch") == []


def test_a_dependency_that_is_not_in_the_queue_is_rejected(queue):
    before = state(queue)
    with pytest.raises(KeyError):
        queue.add_job("archive", 1, depends_on=["fetch", "ghost"])
    assert state(queue) == before
    assert "archive" not in queue.get_pending_jobs()


def test_dependencies_keep_the_given_order(queue):
    queue.add_job("archive", 1, depends_on=["notify", "fetch", "parse"])
    assert queue.get_dependencies("archive") == ["notify", "fetch", "parse"]


@pytest.mark.parametrize(
    "call",
    [
        lambda q: q.complete_job("ghost"),
        lambda q: q.get_dependencies("ghost"),
        lambda q: q.get_priority("ghost"),
        lambda q: q.complete_job(None),
        lambda q: q.get_priority(1),
        lambda q: q.add_job("archive", 1, depends_on=[None]),
    ],
)
def test_jobs_that_are_not_in_the_queue_raise_key_error(queue, call):
    before = state(queue)
    with pytest.raises(KeyError):
        call(queue)
    assert state(queue) == before


# --- completing jobs --------------------------------------------------------


def test_a_blocked_job_is_pending_but_not_ready(queue):
    assert "parse" in queue.get_pending_jobs()
    assert "parse" not in queue.get_ready_jobs()


def test_completing_a_blocked_job_raises_and_changes_nothing(queue):
    before = state(queue)
    with pytest.raises(QueueError):
        queue.complete_job("parse")
    assert state(queue) == before


def test_completing_twice_raises_and_changes_nothing(queue):
    queue.complete_job("fetch")
    before = state(queue)
    with pytest.raises(QueueError):
        queue.complete_job("fetch")
    assert state(queue) == before
    assert queue.get_completed_jobs() == ["fetch"]


def test_completed_jobs_leave_ready_and_pending(queue):
    queue.complete_job("notify")
    assert queue.get_ready_jobs() == ["fetch"]
    assert queue.get_pending_jobs() == ["fetch", "parse"]
    assert queue.get_completed_jobs() == ["notify"]


def test_completion_order_is_recorded_not_add_order(queue):
    queue.complete_job("notify")
    queue.complete_job("fetch")
    queue.complete_job("parse")
    assert queue.get_completed_jobs() == ["notify", "fetch", "parse"]
    assert queue.get_pending_jobs() == []


def test_a_job_waits_for_all_of_its_dependencies(queue):
    queue.add_job("archive", 8, depends_on=["fetch", "notify"])
    queue.complete_job("fetch")
    assert "archive" not in queue.get_ready_jobs()
    queue.complete_job("notify")
    assert queue.get_ready_jobs() == ["archive", "parse"]


def test_a_dependency_on_a_completed_job_is_satisfied_at_once(queue):
    queue.complete_job("fetch")
    queue.add_job("archive", 2, depends_on=["fetch"])
    assert queue.get_ready_jobs() == ["notify", "archive", "parse"]


def test_a_chain_unlocks_one_job_at_a_time():
    q = JobQueue()
    q.add_job("a", 1)
    q.add_job("b", 1, depends_on=["a"])
    q.add_job("c", 1, depends_on=["b"])
    assert q.get_ready_jobs() == ["a"]
    q.complete_job("a")
    assert q.get_ready_jobs() == ["b"]
    with pytest.raises(QueueError):
        q.complete_job("c")
    q.complete_job("b")
    assert q.get_ready_jobs() == ["c"]


def test_completed_jobs_still_report_dependencies_and_priority(queue):
    queue.complete_job("fetch")
    queue.complete_job("parse")
    assert queue.get_dependencies("parse") == ["fetch"]
    assert queue.get_priority("parse") == 1


# --- error precedence -------------------------------------------------------


def test_a_bad_id_is_reported_before_a_bad_priority(queue):
    with pytest.raises(ValueError):
        queue.add_job("", "high")


def test_a_bad_priority_is_reported_before_a_duplicate_id(queue):
    with pytest.raises(ValueError):
        queue.add_job("fetch", None)


def test_a_duplicate_id_is_reported_before_an_unknown_dependency(queue):
    with pytest.raises(QueueError):
        queue.add_job("fetch", 1, depends_on=["ghost"])
    assert "ghost" not in queue.get_pending_jobs()


def test_queues_do_not_share_jobs():
    first, second = JobQueue(), JobQueue()
    first.add_job("a", 1)
    first.complete_job("a")
    assert second.get_pending_jobs() == []
    assert second.get_completed_jobs() == []
    second.add_job("a", 2)
    assert second.get_ready_jobs() == ["a"]
