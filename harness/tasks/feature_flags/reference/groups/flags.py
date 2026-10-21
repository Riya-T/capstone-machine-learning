"""Feature flags: rollouts by user bucket, per-user switches and user groups.

Correct solution for feature_flags after c_groups.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from flags import FlagStore
    store = FlagStore()
    store.add_user("ann", 10)
    store.create_flag("dark_mode")
    store.create_group("design")
    store.add_to_group("design", "ann")
    store.enable_for_group("dark_mode", "design")
"""


class FlagError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_range(value, low, high, what):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{what} must be an int from {low} to {high}, got {value!r}")


class FlagStore:
    def __init__(self):
        self._buckets = {}  # user id -> bucket, in registration order
        self._rollouts = {}  # flag name -> rollout percent, in creation order
        self._switched_on = {}  # flag name -> set of user ids switched on by hand
        self._switched_on_groups = {}  # flag name -> set of group names switched on
        self._members = {}  # group name -> list of user ids, in joining order

    def add_user(self, user_id, bucket):
        check_name(user_id, "user_id")
        check_range(bucket, 0, 99, "bucket")
        if user_id in self._buckets:
            raise FlagError(f"user {user_id!r} is already registered")
        self._buckets[user_id] = bucket

    def create_flag(self, name):
        check_name(name, "flag name")
        if name in self._rollouts:
            raise FlagError(f"flag {name!r} already exists")
        self._rollouts[name] = 0
        self._switched_on[name] = set()
        self._switched_on_groups[name] = set()

    def set_rollout(self, name, percent):
        self._require_flag(name)
        check_range(percent, 0, 100, "percent")
        self._rollouts[name] = percent

    def enable_for_user(self, name, user_id):
        self._require_flag(name)
        self._require_user(user_id)
        self._switched_on[name].add(user_id)

    def is_enabled(self, name, user_id):
        self._require_flag(name)
        self._require_user(user_id)
        if user_id in self._switched_on[name]:
            return True
        if any(user_id in self._members[g] for g in self._switched_on_groups[name]):
            return True
        return self._buckets[user_id] < self._rollouts[name]

    def get_enabled_users(self, name):
        self._require_flag(name)
        return [user_id for user_id in self._buckets if self.is_enabled(name, user_id)]

    def get_flags(self):
        return list(self._rollouts)

    # --- groups ---

    def create_group(self, group_name):
        check_name(group_name, "group name")
        if group_name in self._members:
            raise FlagError(f"group {group_name!r} already exists")
        self._members[group_name] = []

    def add_to_group(self, group_name, user_id):
        self._require_group(group_name)
        self._require_user(user_id)
        if user_id not in self._members[group_name]:
            self._members[group_name].append(user_id)

    def get_group_members(self, group_name):
        self._require_group(group_name)
        return list(self._members[group_name])

    def enable_for_group(self, name, group_name):
        self._require_flag(name)
        self._require_group(group_name)
        self._switched_on_groups[name].add(group_name)

    def _require_flag(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._rollouts:
            raise KeyError(name)

    def _require_user(self, user_id):
        if not isinstance(user_id, str) or user_id not in self._buckets:
            raise KeyError(user_id)

    def _require_group(self, group_name):
        if not isinstance(group_name, str) or group_name not in self._members:
            raise KeyError(group_name)
