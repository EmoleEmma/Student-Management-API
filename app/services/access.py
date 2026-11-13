from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import Course, Enrollment
from app.models.user import Role, Student, User


def can_view_student(db: Session, user: User, student: Student) -> bool:
    if user.role == Role.ADMIN:
        return True
    if user.role == Role.STUDENT:
        return user.student is not None and user.student.id == student.id
    if user.role == Role.LECTURER and user.lecturer is not None:
        shared = db.scalar(
            select(Enrollment.id)
            .join(Course, Course.id == Enrollment.course_id)
            .where(Enrollment.student_id == student.id, Course.lecturer_id == user.lecturer.id)
            .limit(1)
        )
        return shared is not None
    return False