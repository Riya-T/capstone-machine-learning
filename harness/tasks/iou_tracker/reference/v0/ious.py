"""IOU tracker: who owes money to whom in a group of users, with a history
of every IOU.

Correct solution for iou_tracker before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ious import IouTracker
    tracker = IouTracker()
    tracker.add_user("alice")
    tracker.add_user("bob")
    tracker.record_iou("alice", "bob", 500)
"""


class IouError(Exception):
    pass


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


class IouTracker:
    def __init__(self):
        self._users = []  # names in the order they were added
        self._owed = {}  # (lender, borrower) -> amount the borrower owes the lender
        self._history = []  # (lender, borrower, amount), oldest first

    def add_user(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._users:
            raise IouError(f"{name!r} is already a user")
        self._users.append(name)

    def record_iou(self, lender, borrower, amount):
        self._require(lender)
        self._require(borrower)
        check_amount(amount)
        if lender == borrower:
            raise ValueError("a user cannot owe themselves")
        pair = (lender, borrower)
        self._owed[pair] = self._owed.get(pair, 0) + amount
        self._history.append((lender, borrower, amount))

    def get_owed_to(self, name):
        self._require(name)
        debts = [(b, amt) for (l, b), amt in self._owed.items() if l == name and amt > 0]
        return self._largest_first(debts)

    def get_owed_by(self, name):
        self._require(name)
        debts = [(l, amt) for (l, b), amt in self._owed.items() if b == name and amt > 0]
        return self._largest_first(debts)

    def get_balance(self, name):
        self._require(name)
        owed_to = sum(amt for _, amt in self.get_owed_to(name))
        owed_by = sum(amt for _, amt in self.get_owed_by(name))
        return owed_to - owed_by

    def get_history(self, name):
        self._require(name)
        return [iou for iou in self._history if name in iou[:2]]

    def get_users(self):
        return list(self._users)

    def _require(self, name):
        # Non-str names are never stored, so they count as "not a user" too.
        if not isinstance(name, str) or name not in self._users:
            raise KeyError(name)

    def _largest_first(self, debts):
        return sorted(debts, key=lambda d: (-d[1], self._users.index(d[0])))
