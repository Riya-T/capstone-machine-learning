# Login sessions

Write a module `sessions.py` that keeps the registered users of a service
and knows which of them are signed in right now.

## Interface

```python
class SessionError(Exception): ...


class WrongPassword(SessionError): ...


class SessionManager:
    def __init__(self): ...
    def register(self, username: str, password: str) -> None: ...
    def sign_in(self, username: str, password: str) -> None: ...
    def sign_out(self, username: str) -> None: ...
    def is_signed_in(self, username: str) -> bool: ...
    def get_users(self) -> list[str]: ...
    def get_signed_in(self) -> list[str]: ...
```

## Users

- `register(username, password)` adds a user who is not signed in. The
  username must be a non-empty `str`, or `ValueError` is raised; so must the
  password. Registering a username that is already registered raises
  `SessionError`. When several of these apply, the username is checked
  first, then the password, then whether the name is taken.
- `get_users()` returns every registered username, in the order they were
  registered.
- Every other method raises `KeyError` when given a username that is not
  registered, including values that are not strings at all, such as `None`
  or `1`.

## Signing in and out

- `sign_in(username, password)` signs the user in. If the user is already
  signed in, `SessionError` is raised. If the password is not the one given
  at registration, `WrongPassword` is raised. When several problems apply,
  the first of these is raised: `KeyError` for an unknown user, then
  `SessionError` for a user who is already signed in, then `WrongPassword`.
- `sign_out(username)` signs the user out. If the user is not signed in,
  `SessionError` is raised.
- `is_signed_in(username)` tells whether the user is signed in right now.
- `get_signed_in()` returns the usernames of everyone signed in right now,
  in the order they were registered.

A failed call has no effect: if a method raises, who is signed in is
unchanged, and so is the list of users.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes passwords that are not strings passed to `sign_in`, what happens
if a returned list is changed, the text of error messages, saving the users
to a file, and use from several threads.
