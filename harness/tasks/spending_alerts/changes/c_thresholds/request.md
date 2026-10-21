Make the alert limit in `spending.py` adjustable, for the whole tracker and
for single categories. Rent, for example, is often over 500.00 without
anything being wrong.

- `SpendingTracker` takes a new keyword argument `alert_threshold=50000`:
  the default limit in cents. It must be an `int` that is 0 or more (not a
  `bool`); anything else raises `ValueError`.
- Add `SpendingTracker.set_category_threshold(category, threshold)`, which
  gives one category its own limit, replacing the default for that
  category on every account. The threshold follows the same rules as
  `alert_threshold`. Passing `threshold=None` removes the category's own
  limit, so the default applies again. Setting a limit for a category that
  has no payments yet is allowed.
- Add `SpendingTracker.get_threshold(category) -> int`, which returns the
  limit that currently applies to that category.
- Both new methods raise `ValueError` for a category that is not a
  non-empty string, and then `ValueError` for an invalid threshold. A
  failed call changes nothing.
- A category is over the limit in a month when its total is more than the
  limit that applies to it; a total equal to the limit is not over it.
  `get_alerts` and `get_alert_months` always use the limits in force when
  they are called, for every month, including months recorded before the
  limit was changed.

All existing behavior must keep working.
