"""Staff directory: departments, employees and their salaries.

Planted bug (initial version): hiring an id that is already employed is
not refused; the old record is overwritten and the id is listed in the new
department as well. The public checks never hire the same id twice, so only
the hidden initial tests catch it. Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from directory import Directory
    directory = Directory()
    directory.add_department("sales")
    directory.hire("ana", "sales", 300000)
"""


class DirectoryError(Exception):
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

    def add_department(self, name):
        check_name(name, "department name")
        if name in self._staff:
            raise DirectoryError(f"department {name!r} already exists")
        self._staff[name] = []

    def hire(self, employee_id, department, salary):
        check_name(employee_id, "employee id")
        self._require_department(department)
        check_salary(salary)
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

    def _require_department(self, department):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(department, str) or department not in self._staff:
            raise KeyError(department)

    def _require_employee(self, employee_id):
        if not isinstance(employee_id, str) or employee_id not in self._employees:
            raise KeyError(employee_id)
