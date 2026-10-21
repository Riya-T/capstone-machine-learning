# Gym memberships

Write a module `gym.py` that keeps track of a gym's membership plans, its
members, the plan each member is on, and the days each member checked in.

## Interface

```python
class GymError(Exception): ...


class Gym:
    def __init__(self): ...
    def add_plan(self, plan_id: str) -> None: ...
    def add_member(self, member_id: str, plan_id: str) -> None: ...
    def change_plan(self, member_id: str, plan_id: str) -> None: ...
    def check_in(self, member_id: str, day: int) -> None: ...
    def get_plan(self, member_id: str) -> str: ...
    def get_check_ins(self, member_id: str) -> list[int]: ...
    def get_members(self, plan_id: str | None = None) -> list[str]: ...
```

Days are whole numbers counted from the day the gym opened, as `int`: day 1,
day 2, and so on.

## Plans

- `add_plan(plan_id)` adds a membership plan. An empty id raises
  `ValueError`, and adding an id that already exists raises `GymError`.
- Every other method that takes a `plan_id` raises `KeyError` when the plan
  does not exist.

## Members

- `add_member(member_id, plan_id)` adds a member on the given plan. An empty
  member id raises `ValueError`; a member id that is already in use raises
  `GymError`. When a call has several problems, the first of these is
  raised: `ValueError` for the member id, `KeyError` for the plan,
  `GymError` for the duplicate member.
- `change_plan(member_id, plan_id)` moves the member to another plan.
  Moving a member to the plan they are already on raises `GymError`. The
  member is checked before the plan.
- `get_plan(member_id)` returns the id of the plan the member is on now.
- `get_members()` returns the ids of all members in the order they joined.
  `get_members(plan_id)` returns only the members currently on that plan,
  in the same order.
- Every method that takes a `member_id` other than `add_member` raises
  `KeyError` when the member does not exist, including values that are not
  strings at all, such as `None` or `1`.

## Check-ins

- `check_in(member_id, day)` records that the member visited on that day.
  The day must be an `int` greater than 0, or `ValueError` is raised. A
  member can check in at most once per day: a second check-in on the same
  day raises `GymError`. Days may be recorded in any order.
- `get_check_ins(member_id)` returns the member's days in the order they
  were recorded. A member's check-ins are kept when they change plan.

When a `check_in` call has several problems, the first of these is raised:
`KeyError` for the member, `ValueError` for the day, `GymError` for the
repeated day.

A failed call has no effect: if a method raises, every plan, every member and
every check-in is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_plan` or as the new id in
`add_member`, `bool` days, what happens if a returned list is changed, the
text of error messages, saving the gym to a file, and use from several
threads.
