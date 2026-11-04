"""IOU tracker: money lent within a group of users, as a list of every IOU
and how much each borrower owes each lender.

Planted bug (initial version): add_user never checks for an existing user,
so adding a name twice raises nothing and lists it twice. The public checks
never add a user twice, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from ious import IouTracker
    tracker = IouTracker()
    tracker.add_user("alice")
    tracker.add_user("bob")
    tracker.record_iou("alice", "bob", 500)
    tracker.get_ious()  # [("alice", "bob", 500)]
    tracker.get_owed("alice", "bob")  # 500
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

    def _require(self, name):
        # Non-str names are never stored, so they count as "not a user" too.
        if not isinstance(name, str) or name not in self._users:
            raise KeyError(name)
