Lock a user's account in `sessions.py` after too many wrong passwords.

- Add `class AccountLocked(SessionError)` to `sessions.py`.
- Every `sign_in` that raises `WrongPassword` counts as one failed attempt
  for that user. A user who has 3 failed attempts in a row is locked: the
  third wrong attempt itself still raises `WrongPassword`, and from then on
  `sign_in` for that user raises `AccountLocked`, even with the right
  password. A successful sign-in sets the user's failed attempts back to 0.
- Add `SessionManager.unlock(username)`: it unlocks the account and sets
  the failed attempts back to 0. On an account that is not locked it only
  resets the attempts.
- Add `SessionManager.is_locked(username) -> bool` and
  `SessionManager.get_failed_attempts(username) -> int`, the number of
  failed attempts in a row so far (3 while locked, 0 after a success or an
  unlock). New users have 0 failed attempts and are not locked.
- `unlock`, `is_locked` and `get_failed_attempts` raise `KeyError` for a
  username that is not registered.
- In `sign_in`, `AccountLocked` is checked after `KeyError` and after the
  check for a user who is already signed in, and before the password is
  compared. A sign-in refused because the account is locked is not a failed
  attempt and is not recorded anywhere.
- Locking and unlocking never change who is signed in.

All existing behavior must keep working.
