Add a kill switch to `flags.py`, so a flag can be shut off for everybody
at once when a feature misbehaves, without losing its settings.

- Add `FlagStore.kill(name)`, `FlagStore.revive(name)` and
  `FlagStore.is_killed(name) -> bool`. All three raise `KeyError` for a
  flag that does not exist. New flags are not killed. Killing a killed
  flag, or reviving one that is not killed, does nothing.
- While a flag is killed, `is_enabled` returns `False` for every user and
  `get_enabled_users` returns `[]`, whatever the rollout and the switches
  say. The `KeyError` checks for the flag and the user still come first and
  still apply.
- The rollout and the switches of a killed flag can still be changed, and
  the flag can still be switched on for users; all of it takes effect as
  before once the flag is revived.
- A killed flag is still listed by `get_flags`. Killing and reviving one
  flag has no effect on any other flag.

All existing behavior must keep working.
