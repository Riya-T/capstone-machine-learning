Add user groups to `flags.py`, so a flag can be switched on for a whole
team at once instead of one user at a time.

- Add `FlagStore.create_group(group_name)`. A name that is empty or not a
  string raises `ValueError`; a name that is already a group raises
  `FlagError`. Group names are separate from flag names and user ids: a
  group may share its name with either.
- Add `FlagStore.add_to_group(group_name, user_id)`. It raises `KeyError`
  for a group that does not exist, then `KeyError` for a user that is not
  registered. Adding a member who is already in the group does nothing. A
  user may be in any number of groups.
- Add `FlagStore.get_group_members(group_name) -> list[str]`: the members
  in the order they were added. `KeyError` for a group that does not exist.
- Add `FlagStore.enable_for_group(name, group_name)`, which switches the
  flag on for every member of the group. It raises `KeyError` for a flag
  that does not exist, then `KeyError` for a group that does not exist.
  Switching on a group twice does nothing.
- `is_enabled(name, user_id)` is now also `True` when the user is a member
  of any group switched on for the flag. Members added to the group after
  the group was switched on count too, as soon as they are added.
- `get_enabled_users(name)` includes those members, still in the order the
  users were registered, each user once even if several rules apply.

A failed call changes nothing. All existing behavior must keep working.
