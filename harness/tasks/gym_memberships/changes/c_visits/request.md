Add visit counts to `gym.py`, so the gym can see how much each plan is
actually used.

- Add `Gym.get_visit_count(member_id, plan_id=None) -> int`: the number of
  check-ins the member has recorded. With a `plan_id`, count only the
  check-ins recorded while the member was on that plan: a check-in belongs
  to the plan the member was on at the moment it was recorded, and a later
  `change_plan` does not move it. A plan the member has never been on gives
  0. `KeyError` is raised for a member that does not exist, then `KeyError`
  for a plan that does not exist.
- Add `Gym.get_plan_visits(plan_id) -> int`: the total number of check-ins
  recorded by any member while on that plan, including members who have
  since moved to another plan. `KeyError` for a plan that does not exist.
- Add `Gym.get_leaderboard() -> list[str]`: every member id, the member with
  the most check-ins first. Members with the same number of check-ins are
  listed in the order they joined. Members with no check-ins are included.

All existing behavior must keep working.
