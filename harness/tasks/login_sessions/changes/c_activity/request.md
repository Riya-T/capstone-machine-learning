Keep an activity log for every user in `sessions.py`.

- Record an event for the user each time:
  - `sign_in` succeeds: the event `"sign_in"`;
  - `sign_out` succeeds: the event `"sign_out"`;
  - `sign_in` raises `WrongPassword`: the event `"failed_sign_in"`.
  Nothing else is recorded: registering, `KeyError`s and sign-ins refused
  because the user is already signed in leave no event.
- Add `SessionManager.get_activity(username, kind=None) -> list[str]`: the
  user's events, oldest first. With `kind` given, only the events of that
  kind. It raises `KeyError` for a username that is not registered, then
  `ValueError` if `kind` is neither `None` nor one of the three event names.
- Add `SessionManager.get_users_by_activity() -> list[str]`: every
  registered user, the one with the most events first. Users with the same
  number of events keep their registration order.

All existing behavior must keep working.
