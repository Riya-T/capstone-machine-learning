"""Staff directory with headcount caps and transfers between departments.

Correct solution for staff_directory after c_transfer.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from directory import Directory
    directory = Directory()
    directory.add_department("sales")
    directory.add_department("ops")
    directory.set_cap("ops", 5)
    directory.hire("ana", "sales", 300000)
    directory.transfer(["ana"], "ops")
"""


class DirectoryError(Exception):
    pass


class DepartmentFull(DirectoryError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_salary(salary):
    if isinstance(salary, bool) or not isinstance(salary, int) or salary <= 0:
        raise ValueError(f"salary must be a positive int, got {salary!r}")


def check_cap(cap):
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0:
        raise ValueError(f"cap must be an int >= 0, got {cap!r}")


class Directory:
    def __init__(self):
        self._staff = {}  # department -> employee ids in hire order, in the order added
        self._employees = {}  # employee id -> [department, salary]
        self._caps = {}  # department -> cap; absent means no cap

    def add_department(self, name):
        check_name(name, "department name")
        if name in self._staff:
            raise DirectoryError(f"department {name!r} already exists")
        self._staff[name] = []

    def hire(self, employee_id, department, salary):
        check_name(employee_id, "employee id")
        self._require_department(department)
        check_salary(salary)
        if employee_id in self._employees:
            raise DirectoryError(f"{employee_id!r} is already employed")
        self._require_room(department, 1)
        self._employees[employee_id] = [department, salary]
        self._staff[department].append(employee_id)

    def set_salary(self, employee_id, salary):
        self._require_employee(employee_id)
        check_salary(salary)
        self._employees[employee_id][1] = salary

    def get_salary(self, employee_id):
        self._require_employee(employee_id)
        return self._employees[employee_id][1]

    def get_department(self, employee_id):
        self._require_employee(employee_id)
        return self._employees[employee_id][0]

    def get_staff(self, department):
        self._require_department(department)
        return list(self._staff[department])

    def get_departments(self):
        return list(self._staff)

    def set_cap(self, department, cap):
        self._require_department(department)
        check_cap(cap)
        if len(self._staff[department]) > cap:
            raise DirectoryError(f"department {department!r} already has more than {cap} staff")
        self._caps[department] = cap

    def transfer(self, employee_ids, department):
        self._require_department(department)
        ids = list(employee_ids)
        if not ids or len(set(ids)) != len(ids):
            raise ValueError("employee_ids must be a non-empty list without repeats")
        for employee_id in ids:
            self._require_employee(employee_id)
        for employee_id in ids:
            if self._employees[employee_id][0] == department:
                raise DirectoryError(f"{employee_id!r} is already in {department!r}")
        self._require_room(department, len(ids))
        # Every check passed, so the moves below cannot fail halfway.
        for employee_id in ids:
            old = self._employees[employee_id][0]
            self._staff[old].remove(employee_id)
            self._staff[department].append(employee_id)
            self._employees[employee_id][0] = department

    def _require_department(self, department):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(department, str) or department not in self._staff:
            raise KeyError(department)

    def _require_employee(self, employee_id):
        if not isinstance(employee_id, str) or employee_id not in self._employees:
            raise KeyError(employee_id)

    def _require_room(self, department, newcomers):
        cap = self._caps.get(department)
        if cap is not None and len(self._staff[department]) + newcomers > cap:
            raise DepartmentFull(f"department {department!r} is capped at {cap}")
