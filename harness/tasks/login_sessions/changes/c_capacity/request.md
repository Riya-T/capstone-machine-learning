Limit how many users can be signed in at the same time in `sessions.py`.

- `SessionManager` takes a new keyword argument `max_signed_in=None`.
  `None` means no limit. Otherwise it must be an `int` that is 0 or more
  (not a `bool`); anything else raises `ValueError`.
- Add `class SessionLimitReached(SessionError)` to `sessions.py`.
- A `sign_in` that would make the number of signed-in users exceed the
  limit raises `SessionLimitReached` and changes nothing at all. This check
  comes last, after every other check `sign_in` makes, so a wrong password
  is still reported as such when the limit is reached.
- Add `SessionManager.get_max_signed_in() -> int | None`, which returns the
  current limit.
- Add `SessionManager.set_max_signed_in(limit)`, which replaces the limit.
  `None` removes it. It raises `ValueError` for an invalid limit, then
  `SessionError` if more users are signed in right now than the new limit
  allows. In each case nothing changes.

All existing behavior must keep working.
