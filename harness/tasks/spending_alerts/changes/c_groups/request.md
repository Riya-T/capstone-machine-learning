Let categories in `spending.py` be gathered into groups, such as "food" and
"drinks" into "eating out", so totals can be seen per group.

- Add `SpendingTracker.set_group(category, group)`, which puts the category
  into the group. A category is in at most one group: setting a new group
  moves it. `group=None` takes the category out of its group (doing
  nothing if it is in none). Groups are shared by all accounts.
- Add `SpendingTracker.get_group(category) -> str | None`: the category's
  group, or `None` if it has none.
- Add `SpendingTracker.get_group_total(account_id, month, group) -> int`:
  the account's total that month over the categories currently in that
  group. A group that no category is in has a total of 0.
- Add `SpendingTracker.get_group_totals(account_id, month)
  -> list[tuple[str, int]]`: a `(group, total)` pair for every group whose
  total that month is more than 0, in the order the groups were first
  named in `set_group`. Categories in no group are left out.
- Group membership is looked up when a total is asked for, so moving a
  category changes the group totals of every month, earlier months too.
  Category totals and alerts do not depend on groups.
- Category and group names must be non-empty strings (other than `None`
  where allowed above), or `ValueError` is raised and nothing changes.
- When a call has several problems, `KeyError` for an unknown account
  comes first, then `ValueError`.

All existing behavior must keep working.
