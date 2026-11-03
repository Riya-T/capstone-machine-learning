"""IOU tracker with group payments and net views of the debts.

Correct solution for iou_tracker after c_settle and c_net_query.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ious import IouTracker
    tracker = IouTracker()
    tracker.add_user("alice")
    tracker.add_user("bob")
    tracker.record_iou("alice", "bob", 500)
    tracker.record_iou("bob", "alice", 200)
    tracker.get_net_owed("alice", "bob")  # 300
    tracker.get_net_debts()  # [("alice", "bob", 300)]
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
        self._paid = {}  # (lender, borrower) -> everything borrower has paid lender

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
        return self._owed(lender, borrower)

    def settle(self, borrower, payments):
        self._require(borrower)
        for lender, amount in payments:
            self._require(lender)
            check_amount(amount)
        lenders = [lender for lender, _ in payments]
        if len(set(lenders)) != len(lenders):
            raise ValueError("a lender may appear only once")
        for lender, amount in payments:
            if amount > self._owed(lender, borrower):
                raise IouError(f"{borrower!r} does not owe {lender!r} {amount}")
        # Every payment has been checked, so none can fail from here on.
        for lender, amount in payments:
            pair = (lender, borrower)
            self._paid[pair] = self._paid.get(pair, 0) + amount

    def get_net_owed(self, lender, borrower):
        self._require(lender)
        self._require(borrower)
        if lender == borrower:
            raise ValueError("a user has no net debt with themselves")
        return self._owed(lender, borrower) - self._owed(borrower, lender)

    def get_net_debts(self):
        nets = []
        for i, a in enumerate(self._users):
            for b in self._users[i + 1 :]:
                net = self.get_net_owed(a, b)
                if net > 0:
                    nets.append((a, b, net))
                elif net < 0:
                    nets.append((b, a, -net))
        return sorted(nets, key=lambda d: -d[2])

    def get_debtors(self):
        debtors = [(u, -self._net(u)) for u in self._users if self._net(u) < 0]
        return [u for u, _ in self._largest_first(debtors)]

    def get_creditors(self):
        creditors = [(u, self._net(u)) for u in self._users if self._net(u) > 0]
        return [u for u, _ in self._largest_first(creditors)]

    def _owed(self, lender, borrower):
        lent = sum(amt for l, b, amt in self._ious if (l, b) == (lender, borrower))
        return lent - self._paid.get((lender, borrower), 0)

    def _net(self, name):
        # What the others still owe name, minus what name still owes them.
        return sum(self.get_net_owed(name, other) for other in self._users if other != name)

    def _largest_first(self, amounts):
        # Ties keep the order the users were added in.
        return sorted(amounts, key=lambda a: (-a[1], self._users.index(a[0])))

    def _require(self, name):
        # Non-str names are never stored, so they count as "not a user" too.
        if not isinstance(name, str) or name not in self._users:
            raise KeyError(name)
