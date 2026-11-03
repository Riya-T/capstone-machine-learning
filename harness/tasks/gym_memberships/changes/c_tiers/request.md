Group the plans in `gym.py` into tiers, such as "standard" and "premium",
so the gym can report on whole tiers at once.

- `add_plan` takes a new keyword argument `tier="standard"`: the tier the
  plan belongs to. A tier is a non-empty string: an empty string or `None`
  raises `ValueError` and no plan is added.
- Add `Gym.get_tier(plan_id) -> str`, which returns the plan's tier, and
  `Gym.set_tier(plan_id, tier)`, which moves the plan to another tier. Both
  raise `KeyError` for a plan that does not exist, and `set_tier` raises
  `ValueError` for an empty string or `None` as the tier. Setting the tier
  a plan already has is allowed and changes nothing.
- Add `Gym.get_plans(tier=None) -> list[str]`: the ids of all plans in the
  order they were added. With a `tier`, only the plans in that tier, in the
  same order; a tier that no plan belongs to gives an empty list. An empty
  string as the tier raises `ValueError`.
- Add `Gym.get_members_in_tier(tier) -> list[str]`: the ids of the members
  whose current plan belongs to that tier, in the order they joined. An
  empty string or `None` as the tier raises `ValueError`; a tier that no
  plan belongs to gives an empty list.
- When a call has several problems (for example an `add_plan` with an id
  that already exists and an empty tier), which error is raised is
  unspecified.

All existing behavior must keep working.
