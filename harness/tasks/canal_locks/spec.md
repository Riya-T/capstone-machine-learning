# Canal locks

Write a module `canals.py` that keeps track of a network of canal locks
joined by channels, as locks are added, joined, closed and merged.

## Interface

```python
class CanalError(Exception): ...


class CanalNetwork:
    def __init__(self): ...
    def add_lock(self, name: str) -> None: ...
    def connect(self, first: str, second: str) -> None: ...
    def disconnect(self, first: str, second: str) -> None: ...
    def close_lock(self, name: str) -> int: ...
    def merge_locks(self, source: str, into: str) -> int: ...
    def get_locks(self) -> list[str]: ...
    def get_channels(self, name: str) -> list[str]: ...
```

Lock names are non-empty strings.

## Locks

- `add_lock(name)` adds a lock with no channels. A name that is already in
  use raises `CanalError`.
- `get_locks()` returns the names of the locks in use, in the order they
  were added.
- Every other method raises `KeyError` when given a lock name that is not
  in use: one that was never added, or one that was closed or merged away.

## Channels

- A channel joins two different locks and goes both ways: a channel
  between `a` and `b` is a channel of `a` and a channel of `b`. Two locks
  are joined by at most one channel.
- `get_channels(name)` returns the names of the locks joined to `name`, in
  the order those channels were added, oldest first. A new lock has none.
- `connect(first, second)` adds a channel between the two locks, which are
  not joined yet. It is listed last among the channels of `first`, and
  last among the channels of `second`.
- `disconnect(first, second)` removes the channel between two locks that
  are joined (they may be given in either order). The other channels keep
  their order, and the two locks are not joined any more.
- `connect` and `disconnect` raise `ValueError` when both names are the
  same.
- Calls that join two locks that are already joined, or that disconnect
  two locks that are not joined, are unspecified.

## Closing and merging

- `close_lock(name)` removes every channel of the lock and then the lock
  itself: it is removed from `get_locks()`, and every method treats it as
  not in use. It returns how many channels it removed (0 if it had none).
  The other locks keep their remaining channels in the same order. The
  name is then free: `add_lock` may add it again later, as a new lock with
  no channels.
- `merge_locks(source, into)` moves the channels of `source` to `into`,
  one at a time, in the order `get_channels(source)` lists them. For each
  lock `x` joined to `source`:
  - the channel between `source` and `x` is removed, as by `disconnect`;
  - then, unless `x` is `into` or `x` is already joined to `into`, a
    channel between `into` and `x` is added, as by `connect` (so it is
    listed last among the channels of `into` and last among those of `x`).

  Then `source` is removed, as by `close_lock`. It returns how many
  channels it added to `into`.
- `merge_locks` raises `ValueError` when `source` and `into` are the same.

## Errors

A failed call has no effect: if a method raises, the locks and every
lock's channels, in their order, are unchanged.

## Python notes

- One simple way to keep the channels is a list of names per lock (for
  example a dict from lock name to list). Two locks are joined when one
  name is in the other's list: test `second in channels[first]`, not
  `(first, second) in channels`. A channel is in both lists, so adding or
  removing one changes both.
- Do not change a list while looping over it: the loop skips entries. In
  `close_lock` and `merge_locks` loop over a copy, such as
  `for x in list(channels[name])`.
- `close_lock` and `merge_locks` find the other locks through the lock's
  own channels, so fix the other locks' lists first and delete the lock
  itself last.
- Create the dict and lists in `__init__`, so that no two networks share
  them (no class attributes, no default argument values).

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has more than one problem (for
example a lock that is not in use and the same name twice), names that are
not non-empty strings (such as `""`, `None` or `1`), what happens if a
returned list is changed, the text of error messages, saving the network to
a file, and use from several threads.
