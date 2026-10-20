class Course:
    def __init__(self, course_code: str, title: str, capacity: int):
        self.course_code = course_code
        self.title = title
        self.capacity = capacity
        self.enrolled_students = set()

class EnrollmentSystem:
    def __init__(self):
        self.courses = {}
        self.students = set()

    def add_course(self, course_code: str, title: str, capacity: int):
        self.courses[course_code] = Course(course_code, title, capacity)

    def register_student(self, student_id: str):
        self.students.add(student_id)

    def enroll(self, student_id: str, course_code: str) -> bool:
        if student_id not in self.students or course_code not in self.courses:
            return False
        # BUG: Ignores course capacity check entirely!
        self.courses[course_code].enrolled_students.add(student_id)
        return True