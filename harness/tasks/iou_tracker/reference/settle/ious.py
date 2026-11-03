"""IOU tracker where a borrower can pay back several lenders at once.

Correct solution for iou_tracker after c_settle.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ious import IouTracker
    tracker = IouTracker()
    tracker.add_user("alice")
    tracker.add_user("bob")
    tracker.record_iou("alice", "bob", 500)
    tracker.settle("bob", [("alice", 200)])
    tracker.get_owed("alice", "bob")  # 300
    tracker.get_total_lent("alice")  # 300: the totals follow get_owed
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

    def settle(self, borrower, payments):
        self._require(borrower)
        for lender, amount in payments:
            self._require(lender)
            check_amount(amount)
            if lender == borrower:
                raise ValueError("a user cannot pay themselves")
        lenders = [lender for lender, _ in payments]
        if len(set(lenders)) != len(lenders):
            raise ValueError("a lender may appear only once")
        for lender, amount in payments:
            if amount > self._owed.get((lender, borrower), 0):
                raise IouError(f"{borrower!r} does not owe {lender!r} {amount}")
        # Every payment has been checked, so none can fail from here on.
        for lender, amount in payments:
            self._owed[(lender, borrower)] -= amount

    def get_owed(self, lender, borrower):
        self._require(lender)
        self._require(borrower)
        return self._owed.get((lender, borrower), 0)

    def get_debts(self):
        debts = [(l, b, amt) for (l, b), amt in self._owed.items() if amt > 0]
        return sorted(debts, key=lambda d: -d[2])

    def get_total_lent(self, name):
        self._require(name)
        return sum(amt for (lender, _), amt in self._owed.items() if lender == name)

    def get_total_borrowed(self, name):
        self._require(name)
        return sum(amt for (_, borrower), amt in self._owed.items() if borrower == name)

    def get_history(self, name):
        self._require(name)
        return [iou for iou in self._history if name in iou[:2]]

    def get_users(self):
        return list(self._users)

    def _require(self, name):
        # Non-str names are never stored, so they count as "not a user" too.
        if not isinstance(name, str) or name not in self._users:
            raise KeyError(name)
