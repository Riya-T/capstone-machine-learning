"""IOU tracker with group payments and net views of the debts.

Planted bug (after c_settle and c_net_query): the net views were added
correctly, but get_owed_to and get_owed_by were rewritten on top of them and
now return netted amounts instead of the debts in one direction.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from ious import IouTracker
    tracker = IouTracker()
    tracker.add_user("alice")
    tracker.add_user("bob")
    tracker.record_iou("alice", "bob", 500)
    tracker.record_iou("bob", "alice", 200)
    tracker.get_net_owed("alice", "bob")  # 300
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

    def get_owed_to(self, name):
        return self.get_net_owed_to(name)

    def get_owed_by(self, name):
        self._require(name)
        nets = [(u, -self.get_net_owed(name, u)) for u in self._users if u != name]
        return self._largest_first([(u, net) for u, net in nets if net > 0])

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

    def get_net_owed(self, a, b):
        self._require(a)
        self._require(b)
        if a == b:
            raise ValueError("a user has no net debt with themselves")
        return self._owed.get((a, b), 0) - self._owed.get((b, a), 0)

    def get_net_owed_to(self, name):
        self._require(name)
        nets = [(u, self.get_net_owed(name, u)) for u in self._users if u != name]
        return self._largest_first([(u, net) for u, net in nets if net > 0])

    def get_debtors(self):
        debtors = [(u, -self.get_balance(u)) for u in self._users if self.get_balance(u) < 0]
        return [u for u, _ in self._largest_first(debtors)]

    def get_creditors(self):
        creditors = [(u, self.get_balance(u)) for u in self._users if self.get_balance(u) > 0]
        return [u for u, _ in self._largest_first(creditors)]

    def _require(self, name):
        # Non-str names are never stored, so they count as "not a user" too.
        if not isinstance(name, str) or name not in self._users:
            raise KeyError(name)

    def _largest_first(self, debts):
        return sorted(debts, key=lambda d: (-d[1], self._users.index(d[0])))
