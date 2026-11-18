"""Study groups.

Planted bug (initial version): swap_students takes both students out and
then puts each in at the other's old index; the indexes shift as students
are taken out, so swapping a student with the one just before them goes
wrong. The public checks only swap the first and last of three students,
which this happens to get right, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from groups import StudyGroups
    groups = StudyGroups()
    groups.add_group("red")
    groups.join("ann", "red")
"""


class GroupError(Exception):
    pass


class StudyGroups:
    def __init__(self):
        # group name -> its members in order, in the order the groups were added.
        self._groups = {}

    def add_group(self, name):
        if name in self._groups:
            raise GroupError(f"group name {name!r} is already used")
        self._groups[name] = []

    def join(self, student, group):
        self._require(group)
        if self._group_of(student) is not None:
            raise GroupError(f"{student!r} is already in a group")
        self._groups[group].append(student)

    def leave(self, student):
        group = self._find(student)
        self._groups[group].remove(student)

    def swap_students(self, a, b):
        group_a, group_b = self._find(a), self._find(b)
        if a == b:
            raise ValueError("a student cannot swap with themselves")
        members_a, members_b = self._groups[group_a], self._groups[group_b]
        index_a, index_b = members_a.index(a), members_b.index(b)
        members_a.remove(a)
        members_b.remove(b)
        members_a.insert(index_a, b)
        members_b.insert(index_b, a)

    def dissolve_group(self, name, into):
        self._require(name)
        self._require(into)
        if name == into:
            raise ValueError("cannot dissolve a group into itself")
        members = self._groups.pop(name)
        self._groups[into].extend(members)
        return len(members)

    def get_members(self, group):
        self._require(group)
        return list(self._groups[group])

    def get_groups(self):
        return list(self._groups)

    def _require(self, group):
        if group not in self._groups:
            raise KeyError(group)

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
