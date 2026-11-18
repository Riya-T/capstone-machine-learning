Let a skipper ask which locks a boat can reach from a lock in `canals.py`.

- Add `CanalNetwork.get_reachable(name) -> list[str]`. It raises
  `KeyError` for a lock that is not in use.
- It returns every lock that can be reached from `name` by following one
  or more channels, not including `name` itself, each listed once, in
  breadth-first order:
  - first the locks joined to `name`, in the order `get_channels(name)`
    lists them;
  - then the locks joined to those that are not listed yet: those of the
    first one in its `get_channels` order, then those of the second one,
    and so on;
  - then the locks one channel further out, found the same way, until no
    new lock is found.
- A lock with no channels reaches nothing: `get_reachable` returns `[]`.
- `get_reachable` only reads: it changes nothing.

All existing behavior must keep working.
