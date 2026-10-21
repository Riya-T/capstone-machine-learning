Group the plans in `gym.py` into tiers, such as "standard" and "premium",
so the gym can report on whole tiers at once.

- `add_plan` takes a new keyword argument `tier="standard"`: the tier the
  plan belongs to. A tier must be a non-empty `str`; anything else raises
  `ValueError` and no plan is added. If both the plan id and the tier are
  invalid, either `ValueError` may come first. The `GymError` for a plan
  that already exists is checked after both.
- Add `Gym.get_tier(plan_id) -> str`, which returns the plan's tier, and
  `Gym.set_tier(plan_id, tier)`, which moves the plan to another tier. Both
  raise `KeyError` for a plan that does not exist; `set_tier` then raises
  `ValueError` for an invalid tier. Setting the tier a plan already has is
  allowed and changes nothing.
- Add `Gym.get_plans(tier=None) -> list[str]`: the ids of all plans in the
  order they were added. With a `tier`, only the plans in that tier, in the
  same order; a tier that no plan belongs to gives an empty list. An invalid
  tier raises `ValueError`.
- Add `Gym.get_members_in_tier(tier) -> list[str]`: the ids of the members
  whose current plan belongs to that tier, in the order they joined. An
  invalid tier raises `ValueError`; a tier that no plan belongs to gives an
  empty list.

All existing behavior must keep working.
