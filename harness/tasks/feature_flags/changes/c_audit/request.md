Record how each flag in `flags.py` was changed, so a rollout that went
wrong can be traced back.

- Add `FlagStore.get_audit(name, action=None) -> list[tuple]`: the flag's
  recorded changes, oldest first. Every successful `set_rollout` adds
  `("rollout", percent)`, even when the percent is the same as before.
  An `enable_for_user` that switches on a user who was not switched on yet
  adds `("enable_user", user_id)`; switching on a user who already was adds
  nothing. Creating a flag adds nothing, and a call that raises adds
  nothing. A flag that has never been changed has an empty audit.
- With `action` given, `get_audit` returns only the entries whose first
  element equals `action`, in the same order; an action with no entries
  gives `[]`. `get_audit` raises `KeyError` for a flag that does not exist,
  whether or not `action` is given.
- Add `FlagStore.get_flags_for_user(user_id) -> list[str]`: the names of
  the flags currently enabled for that user, in the order the flags were
  created. `KeyError` for a user that is not registered.
- Add `FlagStore.get_changed_flags() -> list[str]`: the names of the flags
  with at least one audit entry, in the order the flags were created.

All existing behavior must keep working.
