"""Job queue where dependencies can be added later, without cycles.

Correct solution for job_queue after c_deprules.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from jobs import JobQueue
    queue = JobQueue()
    queue.add_job("fetch", 5)
    queue.add_job("notify", 3)
    queue.add_dependency("notify", "fetch")
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

    def add_dependency(self, job_id, dep_id):
        self._require(job_id)
        self._require(dep_id)
        if job_id == dep_id:
            raise ValueError(f"job {job_id!r} cannot depend on itself")
        if job_id in self._completed:
            raise QueueError(f"job {job_id!r} is already completed")
        if dep_id in self._dependencies[job_id]:
            raise QueueError(f"job {job_id!r} already depends on {dep_id!r}")
        if self._depends_on(dep_id, job_id):
            raise QueueError(f"{job_id!r} -> {dep_id!r} would form a cycle")
        self._dependencies[job_id].append(dep_id)

    def complete_job(self, job_id):
        self._require(job_id)
        if job_id in self._completed:
            raise QueueError(f"job {job_id!r} is already completed")
        if not self._is_unblocked(job_id):
            raise QueueError(f"job {job_id!r} still waits for a dependency")
        self._completed.append(job_id)

    def get_ready_jobs(self):
        ready = [j for j in self.get_pending_jobs() if self._is_unblocked(j)]
        # sorted is stable, so equal priorities keep add order.
        return sorted(ready, key=lambda j: -self._priorities[j])

    def get_pending_jobs(self):
        return [j for j in self._priorities if j not in self._completed]

    def get_completed_jobs(self):
        return list(self._completed)

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

    def _depends_on(self, start, target):
        """Whether `start` waits for `target`, directly or through other jobs."""
        stack, seen = [start], set()
        while stack:
            job = stack.pop()
            if job == target:
                return True
            if job not in seen:
                seen.add(job)
                stack.extend(self._dependencies[job])
        return False
