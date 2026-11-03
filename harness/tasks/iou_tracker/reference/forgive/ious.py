"""IOU tracker where a lender can cancel the most recent IOU to a borrower.

Correct solution for iou_tracker after c_forgive.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ious import IouTracker
    tracker = IouTracker()
    tracker.add_user("alice")
    tracker.add_user("bob")
    tracker.record_iou("alice", "bob", 500)
    tracker.record_iou("alice", "bob", 200)
    tracker.forgive_last("alice", "bob")  # 200
    tracker.get_ious()  # [("alice", "bob", 500)]
"""


class IouError(Exception):
    pass


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


class IouTracker:
    def __init__(self):
        self._users = []  # names in the order they were added
        self._ious = []  # (lender, borrower, amount), oldest first

    def add_user(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._users:
            raise IouError(f"{name!r} is already a user")
        self._users.append(name)

    def get_users(self):
        return list(self._users)

    def record_iou(self, lender, borrower, amount):
        self._require(lender)
        self._require(borrower)
        check_amount(amount)
        if lender == borrower:
            raise ValueError("a user cannot lend to themselves")
        self._ious.append((lender, borrower, amount))

    def get_ious(self):
        return list(self._ious)

    def get_owed(self, lender, borrower):
        self._require(lender)
        self._require(borrower)
        return sum(amt for l, b, amt in self._ious if (l, b) == (lender, borrower))

    def forgive_last(self, lender, borrower):
        self._require(lender)
        self._require(borrower)
        index = self._last_iou_index(lender, borrower)
        if index is None:
            raise IouError(f"no IOU from {lender!r} to {borrower!r} remains")
        _, _, amount = self._ious.pop(index)
        return amount

    def _last_iou_index(self, lender, borrower):
        for index in range(len(self._ious) - 1, -1, -1):
            if self._ious[index][:2] == (lender, borrower):
                return index
        return None

    def _require(self, name):
        # Non-str names are never stored, so they count as "not a user" too.
        if not isinstance(name, str) or name not in self._users:
            raise KeyError(name)
