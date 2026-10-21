"""Gym memberships: plans, members, the plan each member is on, and check-ins.

Correct solution for gym_memberships before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from gym import Gym
    gym = Gym()
    gym.add_plan("basic")
    gym.add_member("ann", "basic")
    gym.check_in("ann", 1)
"""


class GymError(Exception):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day <= 0:
        raise ValueError(f"day must be a positive int, got {day!r}")


class Gym:
    def __init__(self):
        self._plans = []  # plan ids in the order added
        self._plan_of = {}  # member id -> current plan id, in joining order
        self._check_ins = {}  # member id -> list of days in the order recorded

    def add_plan(self, plan_id):
        check_id(plan_id, "plan_id")
        if plan_id in self._plans:
            raise GymError(f"plan {plan_id!r} already exists")
        self._plans.append(plan_id)

    def add_member(self, member_id, plan_id):
        check_id(member_id, "member_id")
        self._require_plan(plan_id)
        if member_id in self._plan_of:
            raise GymError(f"member {member_id!r} already exists")
        self._plan_of[member_id] = plan_id
        self._check_ins[member_id] = []

    def change_plan(self, member_id, plan_id):
        self._require_member(member_id)
        self._require_plan(plan_id)
        if self._plan_of[member_id] == plan_id:
            raise GymError(f"member {member_id!r} is already on {plan_id!r}")
        self._plan_of[member_id] = plan_id

    def check_in(self, member_id, day):
        self._require_member(member_id)
        check_day(day)
        if day in self._check_ins[member_id]:
            raise GymError(f"member {member_id!r} already checked in on day {day}")
        self._check_ins[member_id].append(day)

    def get_plan(self, member_id):
        self._require_member(member_id)
        return self._plan_of[member_id]

    def get_check_ins(self, member_id):
        self._require_member(member_id)
        return list(self._check_ins[member_id])

    def get_members(self, plan_id=None):
        if plan_id is None:
            return list(self._plan_of)
        self._require_plan(plan_id)
        return [m for m, p in self._plan_of.items() if p == plan_id]

    def _require_plan(self, plan_id):
        if not isinstance(plan_id, str) or plan_id not in self._plans:
            raise KeyError(plan_id)

    def _require_member(self, member_id):
        # Non-str ids are never stored, so they count as "unknown" too.
        if not isinstance(member_id, str) or member_id not in self._plan_of:
            raise KeyError(member_id)
