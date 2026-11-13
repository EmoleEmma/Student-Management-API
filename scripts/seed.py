"""Seed development data. Safe to run repeatedly. Never run against production."""
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.academic import Course, Enrollment, Grade
from app.models.user import Lecturer, Role, Student, User

if settings.environment == "production":
    sys.exit("Refusing to seed a production database.")

DEMO_PASSWORD = "Password123"  # development only

LECTURERS = [
    ("lecturer1@school.test", "STF001", "Folake", "Adebayo"),
    ("lecturer2@school.test", "STF002", "Ibrahim", "Musa"),
]
COURSES = [  # code, title, credit units, lecturer staff id
    ("CSC101", "Introduction to Computer Science", 3, "STF001"),
    ("CSC102", "Programming Fundamentals", 3, "STF001"),
    ("MTH101", "General Mathematics I", 2, "STF002"),
    ("GST101", "Use of English", 2, "STF002"),
]
STUDENTS = [
    ("student1@school.test", "MAT001", "Chinedu", "Okafor"),
    ("student2@school.test", "MAT002", "Aisha", "Bello"),
    ("student3@school.test", "MAT003", "Tunde", "Adeyemi"),
    ("student4@school.test", "MAT004", "Ngozi", "Eze"),
    ("student5@school.test", "MAT005", "Emeka", "Nwosu"),
]
# matric number -> {course code: score, or None if registered but not yet graded}
RESULTS = {
    "MAT001": {"CSC101": 78, "CSC102": 64, "MTH101": 55, "GST101": 71},
    "MAT002": {"CSC101": 48, "CSC102": 52, "MTH101": 41, "GST101": None},
    "MAT003": {"CSC101": 91, "CSC102": 85, "MTH101": 70, "GST101": 66},
    "MAT004": {"CSC101": 35, "CSC102": None},
    "MAT005": {"CSC101": None, "MTH101": None},
}


def get_or_create_user(db, email: str, role: Role) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, hashed_password=hash_password(DEMO_PASSWORD), role=role)
        db.add(user)
        db.flush()
    return user


def main() -> None:
    with SessionLocal() as db:
        get_or_create_user(db, "admin@school.test", Role.ADMIN)

        lecturers = {}
        for email, staff_id, first, last in LECTURERS:
            user = get_or_create_user(db, email, Role.LECTURER)
            lecturer = db.scalar(select(Lecturer).where(Lecturer.staff_id == staff_id))
            if lecturer is None:
                lecturer = Lecturer(user_id=user.id, staff_id=staff_id, first_name=first, last_name=last)
                db.add(lecturer)
                db.flush()
            lecturers[staff_id] = lecturer

        courses = {}
        for code, title, units, staff_id in COURSES:
            course = db.scalar(select(Course).where(Course.code == code))
            if course is None:
                course = Course(code=code, title=title, credit_units=units, lecturer_id=lecturers[staff_id].id)
                db.add(course)
                db.flush()
            courses[code] = course

        students = {}
        for email, matric, first, last in STUDENTS:
            user = get_or_create_user(db, email, Role.STUDENT)
            student = db.scalar(select(Student).where(Student.matric_number == matric))
            if student is None:
                student = Student(
                    user_id=user.id, matric_number=matric, first_name=first,
                    last_name=last, department="Computer Science",
                )
                db.add(student)
                db.flush()
            students[matric] = student

        for matric, results in RESULTS.items():
            for code, score in results.items():
                student, course = students[matric], courses[code]
                enrollment = db.scalar(
                    select(Enrollment).where(
                        Enrollment.student_id == student.id, Enrollment.course_id == course.id
                    )
                )
                if enrollment is None:
                    enrollment = Enrollment(student_id=student.id, course_id=course.id)
                    db.add(enrollment)
                    db.flush()
                if score is not None and enrollment.grade is None:
                    enrollment.grade = Grade(score=Decimal(str(score)))

        db.commit()
    print("Seed complete. All demo accounts use the password:", DEMO_PASSWORD)


if __name__ == "__main__":
    main()