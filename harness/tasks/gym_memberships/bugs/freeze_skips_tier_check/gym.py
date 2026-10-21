"""Gym memberships with plan tiers and frozen memberships.

Planted bug (after c_tiers and c_freeze): freezing was added correctly, but
set_tier no longer rejects an invalid tier such as "" or None, so a plan can
end up in a tier that is not a non-empty string. Never shown to the writer
or the editor; validate-tasks checks that the tests catch it.

Usage:
    from gym import Gym
    gym = Gym()
    gym.add_plan("gold", tier="premium")
    gym.add_member("ann", "gold")
    gym.freeze("ann")
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
        self._tier_of = {}  # plan id -> tier, in the order plans were added
        self._plan_of = {}  # member id -> current plan id, in joining order
        self._check_ins = {}  # member id -> list of days in the order recorded
        self._frozen = set()  # member ids that are frozen

    def add_plan(self, plan_id, tier="standard"):
        check_id(plan_id, "plan_id")
        check_id(tier, "tier")
        if plan_id in self._tier_of:
            raise GymError(f"plan {plan_id!r} already exists")
        self._tier_of[plan_id] = tier

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
        self._require_active(member_id)
        if self._plan_of[member_id] == plan_id:
            raise GymError(f"member {member_id!r} is already on {plan_id!r}")
        self._plan_of[member_id] = plan_id

    def check_in(self, member_id, day):
        self._require_member(member_id)
        check_day(day)
        self._require_active(member_id)
        if day in self._check_ins[member_id]:
            raise GymError(f"member {member_id!r} already checked in on day {day}")
        self._check_ins[member_id].append(day)

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
        return list(self._check_ins[member_id])

    def get_members(self, plan_id=None, active_only=False):
        if plan_id is not None:
            self._require_plan(plan_id)
        return [
            m
            for m, p in self._plan_of.items()
            if (plan_id is None or p == plan_id) and not (active_only and m in self._frozen)
        ]

    def get_tier(self, plan_id):
        self._require_plan(plan_id)
        return self._tier_of[plan_id]

    def set_tier(self, plan_id, tier):
        self._require_plan(plan_id)
        self._tier_of[plan_id] = tier

    def get_plans(self, tier=None):
        if tier is None:
            return list(self._tier_of)
        check_id(tier, "tier")
        return [p for p, t in self._tier_of.items() if t == tier]

    def get_members_in_tier(self, tier):
        check_id(tier, "tier")
        return [m for m, p in self._plan_of.items() if self._tier_of[p] == tier]

    def _require_plan(self, plan_id):
        if not isinstance(plan_id, str) or plan_id not in self._tier_of:
            raise KeyError(plan_id)

    def _require_member(self, member_id):
        # Non-str ids are never stored, so they count as "unknown" too.
        if not isinstance(member_id, str) or member_id not in self._plan_of:
            raise KeyError(member_id)

    def _require_active(self, member_id):
        if member_id in self._frozen:
            raise MembershipFrozen(f"member {member_id!r} is frozen")
