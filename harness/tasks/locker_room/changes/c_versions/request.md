Several desks now work on the same locker room in `lockers.py`. Let staff
move items between lockers, and stop a desk from acting on a locker that
someone else changed since the desk last looked at it.

Versions:

- Add `class VersionConflict(LockerError)` to `lockers.py`.
- Every locker has a version number. It is 1 right after `add_locker` and
  goes up by 1 every time the locker changes: an item is put into it
  (`store`, `move`) or taken out of it (`retrieve`, `move`), and any other
  change made to that locker. Calls that raise, and calls that only read,
  change no version. Lockers that a call does not touch keep their version.
- Add `LockerRoom.get_version(locker_id) -> int`. It raises `KeyError` for a
  locker id that was not added, including values that are not strings.
- `retrieve` takes a new keyword argument `expected_version=None`. When it
  is not `None` and is not equal to the current version of the locker the
  item is in, `retrieve` raises `VersionConflict` and changes nothing. The
  `KeyError` for an item that is not in a locker comes first.
- `store` picks its locker itself and takes no `expected_version`.

Moving:

- Add `LockerRoom.move(item_id, locker_id, expected_version=None)`, which
  takes a stored item out of its locker and puts it into the locker
  `locker_id`. It charges no fee, and `get_locker` returns the new locker
  afterwards. Both lockers' versions go up by 1.
- `expected_version` is compared with the version of the locker the item
  is moved **into**.
- `move` raises, in this order, and changes nothing:
  1. `KeyError` for an item that is not in a locker;
  2. `KeyError` for a locker id that was not added;
  3. `VersionConflict` when `expected_version` is given and does not match;
  4. `LockerError` when the target locker is not empty (this includes the
     locker the item is already in);
  5. `LockerError` when the target locker is too small for the item, going
     by the size the item was stored with.

All existing behavior must keep working.
