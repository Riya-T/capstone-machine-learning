# Feature flags

Write a module `flags.py` that decides which users see which feature flags.
A flag can be rolled out to a share of all users, and switched on for single
users by hand.

## Interface

```python
class FlagError(Exception): ...


class FlagStore:
    def __init__(self): ...
    def add_user(self, user_id: str, bucket: int) -> None: ...
    def create_flag(self, name: str) -> None: ...
    def set_rollout(self, name: str, percent: int) -> None: ...
    def enable_for_user(self, name: str, user_id: str) -> None: ...
    def is_enabled(self, name: str, user_id: str) -> bool: ...
    def get_enabled_users(self, name: str) -> list[str]: ...
    def get_flags(self) -> list[str]: ...
```

All numbers are `int`.

## Users

- `add_user(user_id, bucket)` registers a user. Every user has a bucket, a
  number from 0 to 99, that decides how early a rollout reaches them. An id
  that is empty or not a string raises `ValueError`, and so does a bucket
  that is not an `int` from 0 to 99. Registering an id that is already
  registered raises `FlagError`.
- Every method that takes a `user_id` raises `KeyError` when the user is not
  registered, including values that are not strings at all, such as `None`
  or `1`.

## Flags

- `create_flag(name)` creates a flag. A name that is empty or not a string
  raises `ValueError`; a name that is already a flag raises `FlagError`. A
  new flag has a rollout of 0 and nobody switched on, so it is enabled for
  no one.
- `get_flags()` returns the names of all flags, in the order they were
  created.
- Every method that takes a flag `name` raises `KeyError` when there is no
  such flag, including values that are not strings.
- `set_rollout(name, percent)` replaces the flag's rollout. The percent must
  be an `int` from 0 to 100, or `ValueError` is raised.
- `enable_for_user(name, user_id)` switches the flag on for that one user,
  whatever the rollout is. Switching on a user who is already switched on
  does nothing.

## Deciding

- `is_enabled(name, user_id)` is `True` when the user was switched on with
  `enable_for_user`, or when the user's bucket is less than the flag's
  rollout percent. So a rollout of 0 reaches nobody by bucket, a rollout of
  30 reaches the users with buckets 0 to 29, and a rollout of 100 reaches
  everybody. Users registered after the rollout was set count like any
  other.
- `get_enabled_users(name)` returns the ids of all registered users for whom
  the flag is enabled, in the order the users were registered.

When a call has several problems, the first of these is raised:

1. `KeyError` for a flag that does not exist;
2. `KeyError` for a user that is not registered;
3. `ValueError` for an invalid percent.

A failed call has no effect: if a method raises, no flag, rollout, user or
switch changes.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` buckets or percents, what happens if a returned list is
changed, the text of error messages, saving the store to a file, and use
from several threads.
