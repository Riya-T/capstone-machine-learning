Limit how many users can be signed in at the same time in `sessions.py`.

- `SessionManager` takes a new keyword argument `max_signed_in=None`.
  `None` means no limit. Otherwise it must be an `int` that is 0 or more;
  anything else makes the constructor raise `ValueError`. For example,
  `SessionManager(max_signed_in=-1)` and `SessionManager(max_signed_in="2")`
  raise `ValueError`, and `SessionManager(max_signed_in=0)` creates a
  manager that lets nobody sign in.
- Add `class SessionLimitReached(SessionError)` to `sessions.py`.
- A `sign_in` that would make the number of signed-in users exceed the
  limit raises `SessionLimitReached` and changes nothing at all.
- Add `SessionManager.get_max_signed_in() -> int | None`, which returns the
  current limit.
- Add `SessionManager.set_max_signed_in(limit)`, which replaces the limit.
  `None` removes it. It raises `ValueError` for a limit the constructor
  would reject, and `SessionError` if more users are signed in right now
  than the new limit allows. In each case nothing changes.
- Which error is raised is unspecified when `set_max_signed_in` gets a
  limit that is both invalid and below the number signed in, and when a
  `sign_in` that would exceed the limit also has another problem `sign_in`
  checks for, such as a wrong password or a locked account.

All existing behavior must keep working.
