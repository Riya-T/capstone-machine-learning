"""Study groups with undo and locked groups.

Planted bug (after c_undo and c_lock): locks were added correctly, but
swap_students, rewritten to check both groups' locks first, no longer
records itself, so undo skips it and reverses the call before it instead.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from groups import StudyGroups
    groups = StudyGroups()
    groups.add_group("red")
    groups.join("ann", "red")
    groups.lock_group("red")  # nobody joins or leaves red now
    groups.undo()  # red is unlocked again
"""


class GroupError(Exception):
    pass


class GroupLocked(GroupError):
    pass


class StudyGroups:
    def __init__(self):
        # group name -> its members in order, in the order the groups were added.
        self._groups = {}
        self._locked = set()  # names of the locked groups
        self._undo_stack = []  # (groups, locked) as they were before each call

    def add_group(self, name):
        if name in self._groups:
            raise GroupError(f"group name {name!r} is already used")
        self._save()
        self._groups[name] = []

    def join(self, student, group):
        self._require(group)
        if self._group_of(student) is not None:
            raise GroupError(f"{student!r} is already in a group")
        self._require_unlocked(group)
        self._save()
        self._groups[group].append(student)

    def leave(self, student):
        group = self._find(student)
        self._require_unlocked(group)
        self._save()
        self._groups[group].remove(student)

    def swap_students(self, a, b):
        group_a, group_b = self._find(a), self._find(b)
        if a == b:
            raise ValueError("a student cannot swap with themselves")
        self._require_unlocked(group_a)
        self._require_unlocked(group_b)
        members_a, members_b = self._groups[group_a], self._groups[group_b]
        index_a, index_b = members_a.index(a), members_b.index(b)
        members_a[index_a] = b
        members_b[index_b] = a

    def dissolve_group(self, name, into):
        self._require(name)
        self._require(into)
        if name == into:
            raise ValueError("cannot dissolve a group into itself")
        self._require_unlocked(name)
        self._require_unlocked(into)
        self._save()
        members = self._groups.pop(name)
        self._groups[into].extend(members)
        return len(members)

    def lock_group(self, name):
        self._require(name)
        self._save()
        self._locked.add(name)

    def unlock_group(self, name):
        self._require(name)
        self._save()
        self._locked.discard(name)

    def undo(self):
        if not self._undo_stack:
            raise GroupError("nothing to undo")
        self._groups, self._locked = self._undo_stack.pop()

    def get_locked(self):
        return [name for name in self._groups if name in self._locked]

    def get_members(self, group):
        self._require(group)
        return list(self._groups[group])

    def get_groups(self):
        return list(self._groups)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        groups = {name: list(members) for name, members in self._groups.items()}
        self._undo_stack.append((groups, set(self._locked)))

    def _require(self, group):
        if group not in self._groups:
            raise KeyError(group)

    def _require_unlocked(self, group):
        if group in self._locked:
            raise GroupLocked(f"group {group!r} is locked")

    def _group_of(self, student):
        for name, members in self._groups.items():
            if student in members:
                return name
        return None

    def _find(self, student):
        group = self._group_of(student)
        if group is None:
            raise KeyError(student)
        return group
