"""Job queue where jobs nobody waits for can be cancelled.

Correct solution for job_queue after c_cancel.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from jobs import JobQueue
    queue = JobQueue()
    queue.add_job("fetch", 5)
    queue.add_job("notify", 3)
    queue.cancel_job("notify")
"""


class QueueError(Exception):
    pass


def check_job_id(job_id):
    if not isinstance(job_id, str) or not job_id:
        raise ValueError(f"job_id must be a non-empty str, got {job_id!r}")


def check_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValueError(f"priority must be an int, got {priority!r}")


class JobQueue:
    def __init__(self):
        self._priorities = {}  # job id -> priority, in add order
        self._dependencies = {}  # job id -> ids it waits for, in the given order
        self._completed = []  # job ids in completion order
        self._cancelled = []  # job ids in cancellation order

    def add_job(self, job_id, priority, depends_on=None):
        check_job_id(job_id)
        check_priority(priority)
        if job_id in self._priorities:
            raise QueueError(f"job {job_id!r} is already in the queue")
        dependencies = list(depends_on or [])
        for dep in dependencies:
            self._require(dep)
        self._priorities[job_id] = priority
        self._dependencies[job_id] = dependencies

    def complete_job(self, job_id):
        self._require(job_id)
        if job_id in self._completed:
            raise QueueError(f"job {job_id!r} is already completed")
        if not self._is_unblocked(job_id):
            raise QueueError(f"job {job_id!r} still waits for a dependency")
        self._completed.append(job_id)

    def cancel_job(self, job_id):
        self._require(job_id)
        if job_id in self._completed:
            raise QueueError(f"job {job_id!r} is already completed")
        for other in self.get_pending_jobs():
            if job_id in self._dependencies[other]:
                raise QueueError(f"job {other!r} still waits for {job_id!r}")
        del self._priorities[job_id]
        del self._dependencies[job_id]
        self._cancelled.append(job_id)

    def get_ready_jobs(self):
        ready = [j for j in self.get_pending_jobs() if self._is_unblocked(j)]
        # sorted is stable, so equal priorities keep add order.
        return sorted(ready, key=lambda j: -self._priorities[j])

    def get_pending_jobs(self):
        return [j for j in self._priorities if j not in self._completed]

    def get_completed_jobs(self):
        return list(self._completed)

    def get_cancelled_jobs(self):
        return list(self._cancelled)

    def get_dependencies(self, job_id):
        self._require(job_id)
        return list(self._dependencies[job_id])

    def get_priority(self, job_id):
        self._require(job_id)
        return self._priorities[job_id]

    def _require(self, job_id):
        # Non-str ids are never stored, so they count as "not in the queue" too.
        if not isinstance(job_id, str) or job_id not in self._priorities:
            raise KeyError(job_id)

    def _is_unblocked(self, job_id):
        return all(dep in self._completed for dep in self._dependencies[job_id])
