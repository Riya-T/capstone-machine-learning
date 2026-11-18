Let groups in `groups.py` be locked, for example once a group has handed in
its project plan: nobody may join, leave or be moved into or out of a
locked group.

- Add `StudyGroups.lock_group(name)` and `StudyGroups.unlock_group(name)`.
  Both raise `KeyError` for a group that is not in use. New groups are
  unlocked. Locking a locked group, or unlocking one that is not locked,
  does nothing.
- Add `StudyGroups.get_locked() -> list[str]`, which returns the names of
  the locked groups, in the order of `get_groups()`.
- Add `class GroupLocked(GroupError)` to `groups.py`.
- Every call that would change the members of a locked group raises
  `GroupLocked` and changes nothing:
  - `join` into a locked group;
  - `leave` by a student in a locked group;
  - `swap_students` of two students in a locked group;
  - `dissolve_group` when either group, `name` or `into`, is locked, even
    when the group to dissolve is empty.
- Groups that are not locked work as before. `lock_group` and
  `unlock_group` change no members, and `add_group`, `get_members` and
  `get_groups` work as before on locked groups.
- When a call has another problem as well (a group not in use, a student
  not in any group, the same student or group twice), which
  error it raises is unspecified.
- `undo` still restores the exact earlier state. `lock_group` and
  `unlock_group` change the state too, so `undo` reverses them like any
  other call.

All existing behavior must keep working.
