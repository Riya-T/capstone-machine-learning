"""IOU tracker with group payments and net views of the debts.

Planted bug (after c_settle and c_net_query): the net views were added
correctly, but get_debts was rewritten on top of them and now lists the
netted debts instead of each direction on its own.
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
        return self.get_net_debts()

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

    def get_net_owed(self, lender, borrower):
        self._require(lender)
        self._require(borrower)
        if lender == borrower:
            raise ValueError("a user has no net debt with themselves")
        return self._owed.get((lender, borrower), 0) - self._owed.get((borrower, lender), 0)

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

    def _require(self, name):
        # Non-str names are never stored, so they count as "not a user" too.
        if not isinstance(name, str) or name not in self._users:
            raise KeyError(name)

    def _net(self, name):
        # What the others still owe name, minus what name still owes them.
        return self.get_total_lent(name) - self.get_total_borrowed(name)

    def _largest_first(self, amounts):
        # Ties keep the order the users were added in.
        return sorted(amounts, key=lambda a: (-a[1], self._users.index(a[0])))
