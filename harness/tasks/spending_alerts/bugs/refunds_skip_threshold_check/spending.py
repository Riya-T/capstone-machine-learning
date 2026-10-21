"""Spending alerts with adjustable alert limits and refunds of payments.

Planted bug (after c_thresholds and c_refunds): refunds work, but
set_category_threshold no longer checks the threshold it is given.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from spending import SpendingTracker
    tracker = SpendingTracker(alert_threshold=30000)
    tracker.add_account("alice")
    payment_id = tracker.record_payment("alice", 1, "food", 1250)
    tracker.refund(payment_id, 250)
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


class Payment:
    def __init__(self, account_id, month, category, amount):
        self.account_id = account_id
        self.month = month
        self.category = category
        self.amount = amount
        self.refunded = 0

    def remaining(self):
        return self.amount - self.refunded


class SpendingTracker:
    def __init__(self, alert_threshold=DEFAULT_ALERT_THRESHOLD):
        check_threshold(alert_threshold)
        self._default_threshold = alert_threshold
        self._thresholds = {}  # category -> its own limit
        self._accounts = {}  # account id -> list of payment ids, oldest first
        self._payments = {}  # payment id -> Payment

    def add_account(self, account_id):
        check_name(account_id, "account_id")
        if account_id in self._accounts:
            raise SpendingError(f"account {account_id!r} already exists")
        self._accounts[account_id] = []

    def get_accounts(self):
        return list(self._accounts)

    def record_payment(self, account_id, month, category, amount):
        self._require(account_id)
        check_month(month)
        check_name(category, "category")
        check_amount(amount)
        payment_id = len(self._payments) + 1
        self._payments[payment_id] = Payment(account_id, month, category, amount)
        self._accounts[account_id].append(payment_id)
        return payment_id

    def get_total(self, account_id, month):
        self._require(account_id)
        check_month(month)
        return sum(p.remaining() for p in self._payments_of(account_id) if p.month == month)

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
        months = sorted({p.month for p in self._payments_of(account_id) if p.category == category})
        return [m for m in months if self._is_over(account_id, m, category)]

    def set_category_threshold(self, category, threshold):
        check_name(category, "category")
        if threshold is None:
            self._thresholds.pop(category, None)
            return
        self._thresholds[category] = threshold

    def get_threshold(self, category):
        check_name(category, "category")
        return self._thresholds.get(category, self._default_threshold)

    def refund(self, payment_id, amount=None):
        payment = self._payment(payment_id)
        if amount is not None:
            check_amount(amount)
        left = payment.remaining()
        if left == 0:
            raise SpendingError(f"payment {payment_id} is already fully refunded")
        if amount is None:
            amount = left
        elif amount > left:
            raise SpendingError(f"payment {payment_id} has only {left} left to refund")
        payment.refunded += amount

    def get_refunded(self, payment_id):
        return self._payment(payment_id).refunded

    def _require(self, account_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(account_id, str) or account_id not in self._accounts:
            raise KeyError(account_id)

    def _payment(self, payment_id):
        if isinstance(payment_id, bool) or not isinstance(payment_id, int):
            raise KeyError(payment_id)
        if payment_id not in self._payments:
            raise KeyError(payment_id)
        return self._payments[payment_id]

    def _payments_of(self, account_id):
        return [self._payments[i] for i in self._accounts[account_id]]

    def _category_total(self, account_id, month, category):
        return sum(
            p.remaining()
            for p in self._payments_of(account_id)
            if p.month == month and p.category == category
        )

    def _categories_in(self, account_id, month):
        """Categories paid in the month, in the order of their first payment."""
        seen = []
        for p in self._payments_of(account_id):
            if p.month == month and p.category not in seen:
                seen.append(p.category)
        return seen

    def _is_over(self, account_id, month, category):
        limit = self.get_threshold(category)
        return self._category_total(account_id, month, category) > limit
