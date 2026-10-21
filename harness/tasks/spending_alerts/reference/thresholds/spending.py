"""Spending alerts with adjustable alert limits: a default for the tracker
and an optional limit of its own for each category.

Correct solution for spending_alerts after c_thresholds.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from spending import SpendingTracker
    tracker = SpendingTracker(alert_threshold=30000)
    tracker.set_category_threshold("rent", 150000)
    tracker.add_account("alice")
    tracker.record_payment("alice", 1, "food", 1250)
"""

DEFAULT_ALERT_THRESHOLD = 50000


class SpendingError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_month(month):
    if isinstance(month, bool) or not isinstance(month, int) or month < 1:
        raise ValueError(f"month must be an int >= 1, got {month!r}")


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


def check_threshold(threshold):
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 0:
        raise ValueError(f"threshold must be an int >= 0, got {threshold!r}")


class SpendingTracker:
    def __init__(self, alert_threshold=DEFAULT_ALERT_THRESHOLD):
        check_threshold(alert_threshold)
        self._default_threshold = alert_threshold
        self._thresholds = {}  # category -> its own limit
        # account id -> list of (month, category, amount), oldest first
        self._payments = {}
        self._next_id = 1

    def add_account(self, account_id):
        check_name(account_id, "account_id")
        if account_id in self._payments:
            raise SpendingError(f"account {account_id!r} already exists")
        self._payments[account_id] = []

    def get_accounts(self):
        return list(self._payments)

    def record_payment(self, account_id, month, category, amount):
        self._require(account_id)
        check_month(month)
        check_name(category, "category")
        check_amount(amount)
        self._payments[account_id].append((month, category, amount))
        payment_id = self._next_id
        self._next_id += 1
        return payment_id

    def get_total(self, account_id, month):
        self._require(account_id)
        check_month(month)
        return sum(a for m, _, a in self._payments[account_id] if m == month)

    def get_category_total(self, account_id, month, category):
        self._require(account_id)
        check_month(month)
        check_name(category, "category")
        return self._category_total(account_id, month, category)

    def get_alerts(self, account_id, month):
        self._require(account_id)
        check_month(month)
        return [
            category
            for category in self._categories_in(account_id, month)
            if self._is_over(account_id, month, category)
        ]

    def get_alert_months(self, account_id, category):
        self._require(account_id)
        check_name(category, "category")
        months = sorted({m for m, c, _ in self._payments[account_id] if c == category})
        return [m for m in months if self._is_over(account_id, m, category)]

    def set_category_threshold(self, category, threshold):
        check_name(category, "category")
        if threshold is None:
            self._thresholds.pop(category, None)
            return
        check_threshold(threshold)
        self._thresholds[category] = threshold

    def get_threshold(self, category):
        check_name(category, "category")
        return self._thresholds.get(category, self._default_threshold)

    def _require(self, account_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(account_id, str) or account_id not in self._payments:
            raise KeyError(account_id)

    def _category_total(self, account_id, month, category):
        return sum(a for m, c, a in self._payments[account_id] if m == month and c == category)

    def _categories_in(self, account_id, month):
        """Categories paid in the month, in the order of their first payment."""
        seen = []
        for m, category, _ in self._payments[account_id]:
            if m == month and category not in seen:
                seen.append(category)
        return seen

    def _is_over(self, account_id, month, category):
        limit = self.get_threshold(category)
        return self._category_total(account_id, month, category) > limit
