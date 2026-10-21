"""Staff directory where employees can be on leave.

Correct solution for staff_directory after c_leave.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from directory import Directory
    directory = Directory()
    directory.add_department("sales")
    directory.hire("ana", "sales", 300000)
    directory.start_leave("ana")
"""


class DirectoryError(Exception):
    pass


class OnLeave(DirectoryError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_salary(salary):
    if isinstance(salary, bool) or not isinstance(salary, int) or salary <= 0:
        raise ValueError(f"salary must be a positive int, got {salary!r}")


class Directory:
    def __init__(self):
        self._staff = {}  # department -> employee ids in hire order, in the order added
        self._employees = {}  # employee id -> [department, salary]
        self._on_leave = set()

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
        self._employees[employee_id] = [department, salary]
        self._staff[department].append(employee_id)

    def set_salary(self, employee_id, salary):
        self._require_employee(employee_id)
        check_salary(salary)
        self._require_present(employee_id)
        self._employees[employee_id][1] = salary

    def get_salary(self, employee_id):
        self._require_employee(employee_id)
        return self._employees[employee_id][1]

    def get_department(self, employee_id):
        self._require_employee(employee_id)
        return self._employees[employee_id][0]

    def get_staff(self, department, include_on_leave=True):
        self._require_department(department)
        if not isinstance(include_on_leave, bool):
            raise ValueError("include_on_leave must be a bool")
        staff = self._staff[department]
        if include_on_leave:
            return list(staff)
        return [emp for emp in staff if emp not in self._on_leave]

    def get_departments(self):
        return list(self._staff)

    def start_leave(self, employee_id):
        self._require_employee(employee_id)
        self._on_leave.add(employee_id)

    def end_leave(self, employee_id):
        self._require_employee(employee_id)
        self._on_leave.discard(employee_id)

    def is_on_leave(self, employee_id):
        self._require_employee(employee_id)
        return employee_id in self._on_leave

    def _require_department(self, department):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(department, str) or department not in self._staff:
            raise KeyError(department)

    def _require_employee(self, employee_id):
        if not isinstance(employee_id, str) or employee_id not in self._employees:
            raise KeyError(employee_id)

    def _require_present(self, employee_id):
        if employee_id in self._on_leave:
            raise OnLeave(f"{employee_id!r} is on leave")
