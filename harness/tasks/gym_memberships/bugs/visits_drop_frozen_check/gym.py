"""Gym memberships with frozen memberships and visit counts per plan.

Planted bug (after c_freeze and c_visits): visit counts were added
correctly, but check_in no longer refuses a frozen member, so frozen members
keep recording visits. Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from gym import Gym
    gym = Gym()
    gym.add_plan("basic")
    gym.add_member("ann", "basic")
    gym.check_in("ann", 1)
    gym.freeze("ann")
    gym.get_visit_count("ann", "basic")
"""


class GymError(Exception):
    pass


class MembershipFrozen(GymError):
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
        self._visits = {}  # member id -> list of (day, plan the member was on)
        self._frozen = set()  # member ids that are frozen

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
        self._visits[member_id] = []

    def change_plan(self, member_id, plan_id):
        self._require_member(member_id)
        self._require_plan(plan_id)
        self._require_active(member_id)
        if self._plan_of[member_id] == plan_id:
            raise GymError(f"member {member_id!r} is already on {plan_id!r}")
        self._plan_of[member_id] = plan_id

    def check_in(self, member_id, day):
        self._require_member(member_id)
        check_day(day)
        if day in self.get_check_ins(member_id):
            raise GymError(f"member {member_id!r} already checked in on day {day}")
        self._visits[member_id].append((day, self._plan_of[member_id]))

    def freeze(self, member_id):
        self._require_member(member_id)
        self._frozen.add(member_id)

    def unfreeze(self, member_id):
        self._require_member(member_id)
        self._frozen.discard(member_id)

    def is_frozen(self, member_id):
        self._require_member(member_id)
        return member_id in self._frozen

    def get_plan(self, member_id):
        self._require_member(member_id)
        return self._plan_of[member_id]

    def get_check_ins(self, member_id):
        self._require_member(member_id)
        return [day for day, _ in self._visits[member_id]]

    def get_members(self, plan_id=None, active_only=False):
        if plan_id is not None:
            self._require_plan(plan_id)
        return [
            m
            for m, p in self._plan_of.items()
            if (plan_id is None or p == plan_id) and not (active_only and m in self._frozen)
        ]

    def get_visit_count(self, member_id, plan_id=None):
        self._require_member(member_id)
        if plan_id is None:
            return len(self._visits[member_id])
        self._require_plan(plan_id)
        return sum(1 for _, p in self._visits[member_id] if p == plan_id)

    def get_plan_visits(self, plan_id):
        self._require_plan(plan_id)
        return sum(self.get_visit_count(m, plan_id) for m in self._plan_of)

    def get_leaderboard(self):
        # sorted is stable, so equal counts keep joining order.
        return sorted(self._plan_of, key=lambda m: -len(self._visits[m]))

    def _require_plan(self, plan_id):
        if not isinstance(plan_id, str) or plan_id not in self._plans:
            raise KeyError(plan_id)

    def _require_member(self, member_id):
        # Non-str ids are never stored, so they count as "unknown" too.
        if not isinstance(member_id, str) or member_id not in self._plan_of:
            raise KeyError(member_id)

    def _require_active(self, member_id):
        if member_id in self._frozen:
            raise MembershipFrozen(f"member {member_id!r} is frozen")
