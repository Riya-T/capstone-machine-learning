"""Study groups with finding students.

Correct solution for study_groups after c_find.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from groups import StudyGroups
    groups = StudyGroups()
    groups.add_group("red")
    groups.join("ann", "red")
    groups.find_student("ann")  # ("red", 1)
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
        if self._locate(student) is not None:
            raise GroupError(f"{student!r} is already in a group")
        self._groups[group].append(student)

    def leave(self, student):
        group, _ = self._find(student)
        self._groups[group].remove(student)

    def swap_students(self, a, b):
        (group_a, index_a), (group_b, index_b) = self._find(a), self._find(b)
        if a == b:
            raise ValueError("a student cannot swap with themselves")
        self._groups[group_a][index_a] = b
        self._groups[group_b][index_b] = a

    def dissolve_group(self, name, into):
        self._require(name)
        self._require(into)
        if name == into:
            raise ValueError("cannot dissolve a group into itself")
        members = self._groups.pop(name)
        self._groups[into].extend(members)
        return len(members)

    def find_student(self, student):
        group, index = self._find(student)
        return (group, index + 1)

    def get_students(self):
        return [student for members in self._groups.values() for student in members]

    def get_members(self, group):
        self._require(group)
        return list(self._groups[group])

    def get_groups(self):
        return list(self._groups)

    def _require(self, group):
        if group not in self._groups:
            raise KeyError(group)

    def _locate(self, student):
        # (group, index from 0) of a student, or None when in no group.
        for name, members in self._groups.items():
            if student in members:
                return name, members.index(student)
        return None

    def _find(self, student):
        found = self._locate(student)
        if found is None:
            raise KeyError(student)
        return found
