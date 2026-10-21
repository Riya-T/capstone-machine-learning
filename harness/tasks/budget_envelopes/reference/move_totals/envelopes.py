"""Budget envelopes with moves, all-or-nothing allocation and spending totals.

Correct solution for budget_envelopes after c_move and c_totals.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from envelopes import Budget
    budget = Budget()
    budget.add_envelope("food")
    budget.add_income(50000)
    budget.allocate("food", 20000)
    budget.spend("food", 1250)
    budget.get_total_spent()
"""


class BudgetError(Exception):
    pass


class NotEnoughMoney(BudgetError):
    pass


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


class Budget:
    def __init__(self):
        self._unassigned = 0  # income not yet put into an envelope, in cents
        self._income = 0  # everything ever added with add_income
        self._balances = {}  # envelope name -> cents held, in creation order
        self._spent = {}  # envelope name -> cents spent so far

    def add_envelope(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._balances:
            raise BudgetError(f"envelope {name!r} already exists")
        self._balances[name] = 0
        self._spent[name] = 0

    def add_income(self, amount):
        check_amount(amount)
        self._unassigned += amount
        self._income += amount

    def allocate(self, name, amount):
        self._require(name)
        check_amount(amount)
        self._require_unassigned(amount)
        self._unassigned -= amount
        self._balances[name] += amount

    def allocate_many(self, amounts):
        # Check everything first so a failure half-way cannot happen.
        for name in amounts:
            self._require(name)
        for amount in amounts.values():
            check_amount(amount)
        self._require_unassigned(sum(amounts.values()))
        for name, amount in amounts.items():
            self._unassigned -= amount
            self._balances[name] += amount

    def spend(self, name, amount):
        self._require(name)
        check_amount(amount)
        self._require_funds(name, amount)
        self._balances[name] -= amount
        self._spent[name] += amount

    def move(self, from_name, to_name, amount):
        self._require(from_name)
        self._require(to_name)
        check_amount(amount)
        if from_name == to_name:
            raise ValueError("cannot move money into the same envelope")
        self._require_funds(from_name, amount)
        self._balances[from_name] -= amount
        self._balances[to_name] += amount

    def get_balance(self, name):
        self._require(name)
        return self._balances[name]

    def get_unassigned(self):
        return self._unassigned

    def get_envelopes(self):
        return list(self._balances)

    def get_spent(self, name):
        self._require(name)
        return self._spent[name]

    def get_total_spent(self):
        return sum(self._spent.values())

    def get_total_income(self):
        return self._income

    def get_top_spenders(self):
        # sorted is stable, so equal totals keep the creation order.
        return sorted(self._balances, key=lambda name: -self._spent[name])

    def _require(self, name):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(name, str) or name not in self._balances:
            raise KeyError(name)

    def _require_unassigned(self, amount):
        if amount > self._unassigned:
            raise NotEnoughMoney(f"only {self._unassigned} unassigned, cannot allocate {amount}")

    def _require_funds(self, name, amount):
        if amount > self._balances[name]:
            raise NotEnoughMoney(f"envelope {name!r} cannot cover {amount}")
