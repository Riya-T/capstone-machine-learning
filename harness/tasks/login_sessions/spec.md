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

- `register(username, password)` adds a user who is not signed in. An
  empty string or `None` as the username or the password raises
  `ValueError`. Registering a username that is already registered raises
  `SessionError`. When several of these apply, the username is checked
  first, then the password, then whether the name is taken.
- `get_users()` returns every registered username, in the order they were
  registered.
- Every other method raises `KeyError` when given a username that is not
  registered, including values that are not strings at all, such as `None`
  or `1`. A registered user is known to every method from the moment they
  are registered, whether or not they have ever signed in: right after
  `register("bob", "secret")`, `is_signed_in("bob")` returns `False` and
  `sign_out("bob")` raises `SessionError`, not `KeyError`.

## Signing in and out

- `sign_in(username, password)` signs the user in. If the user is already
  signed in, `SessionError` is raised. If the password is not the one given
  at registration, `WrongPassword` is raised. When several problems apply,
  the first of these is raised: `KeyError` for an unknown user, then
  `SessionError` for a user who is already signed in, then `WrongPassword`.
- `sign_out(username)` signs the user out. If the user is not signed in,
  `SessionError` is raised. A user who signed out is like one who never
  signed in: `is_signed_in` returns `False`, `sign_out` raises
  `SessionError`, and `sign_in` with their password signs them in again.
- `is_signed_in(username)` tells whether the user is signed in right now.
- `get_signed_in()` returns the usernames of the registered users who are
  signed in right now, each once, in any order. For example, after
  registering `"ann"`, `"ben"` and `"cy"` and then signing in `"cy"` and
  then `"ann"`, `get_signed_in()` returns `"ann"` and `"cy"` in either
  order; after `sign_out("cy")` it returns `["ann"]`.

A failed call has no effect: if a method raises, who is signed in is
unchanged, and so is the list of users.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes other values that are not strings, such as `7`, passed to
`register` as a username or a password, passwords that are not strings
passed to `sign_in`, the order of the names `get_signed_in` returns, what
happens if a returned list is changed, the text of error messages, saving
the users to a file, and use from several threads.
