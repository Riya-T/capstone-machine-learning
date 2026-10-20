"""Bank ledger with overdraft limits.

Correct solution for bank_ledger after c_overdraft.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ledger import Ledger
    ledger = Ledger()
    ledger.open_account("alice", overdraft_limit=500)
    ledger.withdraw("alice", 200)
"""


class LedgerError(Exception):
    pass


class InsufficientFunds(LedgerError):
    pass


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


def check_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError(f"overdraft limit must be an int >= 0, got {limit!r}")


class Ledger:
    def __init__(self):
        self._balances = {}  # account id -> balance in cents, in opening order
        self._history = {}  # account id -> list of (kind, amount)
        self._limits = {}  # account id -> overdraft limit in cents

    def open_account(self, account_id, overdraft_limit=0):
        if not isinstance(account_id, str) or not account_id:
            raise ValueError("account_id must be a non-empty str")
        check_limit(overdraft_limit)
        if account_id in self._balances:
            raise LedgerError(f"account {account_id!r} is already open")
        self._balances[account_id] = 0
        self._history[account_id] = []
        self._limits[account_id] = overdraft_limit

    def deposit(self, account_id, amount):
        self._require(account_id)
        check_amount(amount)
        self._balances[account_id] += amount
        self._history[account_id].append(("deposit", amount))

    def withdraw(self, account_id, amount):
        self._require(account_id)
        check_amount(amount)
        self._require_funds(account_id, amount)
        self._balances[account_id] -= amount
        self._history[account_id].append(("withdrawal", amount))

    def transfer(self, from_id, to_id, amount):
        self._require(from_id)
        self._require(to_id)
        check_amount(amount)
        if from_id == to_id:
            raise ValueError("cannot transfer to the same account")
        self._require_funds(from_id, amount)
        self._balances[from_id] -= amount
        self._balances[to_id] += amount
        self._history[from_id].append(("transfer_out", amount))
        self._history[to_id].append(("transfer_in", amount))

    def get_balance(self, account_id):
        self._require(account_id)
        return self._balances[account_id]

    def get_history(self, account_id):
        self._require(account_id)
        return list(self._history[account_id])

    def get_accounts(self):
        return list(self._balances)

    def get_overdraft_limit(self, account_id):
        self._require(account_id)
        return self._limits[account_id]

    def set_overdraft_limit(self, account_id, limit):
        self._require(account_id)
        check_limit(limit)
        if self._balances[account_id] < -limit:
            raise LedgerError(f"account {account_id!r} already owes more than {limit}")
        self._limits[account_id] = limit

    def _require(self, account_id):
        # Non-str ids are never stored, so they count as "not open" too.
        if not isinstance(account_id, str) or account_id not in self._balances:
            raise KeyError(account_id)

    def _require_funds(self, account_id, amount):
        if self._balances[account_id] - amount < -self._limits[account_id]:
            raise InsufficientFunds(f"account {account_id!r} cannot cover {amount}")
