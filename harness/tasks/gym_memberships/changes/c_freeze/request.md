Let memberships in `gym.py` be frozen, for example while a member is away
or has stopped paying.

- Add `Gym.freeze(member_id)`, `Gym.unfreeze(member_id)` and
  `Gym.is_frozen(member_id) -> bool`. All three raise `KeyError` for a
  member that does not exist. New members are not frozen. Freezing a frozen
  member, or unfreezing one that is not frozen, does nothing.
- Add `class MembershipFrozen(GymError)` to `gym.py`.
- While a member is frozen, `check_in` and `change_plan` for that member
  raise `MembershipFrozen` and change nothing. `MembershipFrozen` is checked
  after every `KeyError` and `ValueError` check and before the `GymError`
  for a repeated day or for the plan the member is already on.
- `get_members` takes a new keyword argument `active_only=False`. With
  `active_only=True` frozen members are left out, with or without a
  `plan_id`. Otherwise frozen members are listed as before.
- Freezing and unfreezing change nothing else: the member's plan and their
  check-ins stay as they are.

All existing behavior must keep working.
