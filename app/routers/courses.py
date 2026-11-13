from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select

from app.core.deps import (
    AdminUser, CurrentUser, DbSession, StaffUser, get_lecturer_profile, get_student_profile,
)
from app.models.academic import Course, Enrollment, Grade
from app.models.user import Lecturer, Role, Student, User
from app.schemas.academic import (
    CourseCreate, CourseRead, CourseUpdate, EnrollmentRead, GradeIn, GradeRead, StudentRead,
)
from app.services.grading import score_to_grade

router = APIRouter(prefix="/courses", tags=["courses"])


def _get_course(db, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "Course not found")
    return course


def _ensure_course_staff(user: User, course: Course) -> None:
    if user.role == Role.ADMIN:
        return
    if user.lecturer is None or course.lecturer_id != user.lecturer.id:
        raise HTTPException(403, "You are not assigned to this course")


def _ensure_lecturer_exists(db, lecturer_id: int | None) -> None:
    if lecturer_id is not None and db.get(Lecturer, lecturer_id) is None:
        raise HTTPException(404, "Lecturer not found")


# ---------- course management (admin) ----------
@router.post("", response_model=CourseRead, status_code=201)
def create_course(payload: CourseCreate, db: DbSession, _: AdminUser):
    if db.scalar(select(Course).where(Course.code == payload.code)):
        raise HTTPException(409, "Course code already exists")
    _ensure_lecturer_exists(db, payload.lecturer_id)
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("", response_model=list[CourseRead])
def list_courses(
    db: DbSession,
    _: CurrentUser,
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    stmt = select(Course)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Course.code.ilike(like), Course.title.ilike(like)))
    return db.scalars(stmt.order_by(Course.code).offset(skip).limit(limit)).all()


@router.get("/mine", response_model=list[CourseRead])
def my_courses(db: DbSession, lecturer: Annotated[Lecturer, Depends(get_lecturer_profile)]):
    stmt = select(Course).where(Course.lecturer_id == lecturer.id).order_by(Course.code)
    return db.scalars(stmt).all()


@router.get("/{course_id}", response_model=CourseRead)
def get_course(course_id: int, db: DbSession, _: CurrentUser):
    return _get_course(db, course_id)


@router.patch("/{course_id}", response_model=CourseRead)
def update_course(course_id: int, payload: CourseUpdate, db: DbSession, _: AdminUser):
    course = _get_course(db, course_id)
    data = payload.model_dump(exclude_unset=True)
    if "lecturer_id" in data:
        _ensure_lecturer_exists(db, data["lecturer_id"])
    for key, value in data.items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int, db: DbSession, _: AdminUser):
    course = _get_course(db, course_id)
    if db.scalar(select(Enrollment.id).where(Enrollment.course_id == course_id).limit(1)):
        raise HTTPException(409, "Cannot delete a course that has registered students")
    db.delete(course)
    db.commit()


# ---------- roster (assigned lecturer or admin) ----------
@router.get("/{course_id}/students", response_model=list[StudentRead])
def course_students(course_id: int, db: DbSession, user: StaffUser):
    course = _get_course(db, course_id)
    _ensure_course_staff(user, course)
    stmt = (
        select(Student)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(Enrollment.course_id == course_id)
        .order_by(Student.last_name, Student.id)
    )
    return db.scalars(stmt).all()


# ---------- registration (student, self-service) ----------
def _find_enrollment(db, student_id: int, course_id: int) -> Enrollment | None:
    return db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id, Enrollment.course_id == course_id
        )
    )


@router.post("/{course_id}/register", response_model=EnrollmentRead, status_code=201)
def register_course(
    course_id: int,
    db: DbSession,
    student: Annotated[Student, Depends(get_student_profile)],
):
    _get_course(db, course_id)
    if _find_enrollment(db, student.id, course_id):
        raise HTTPException(409, "Already registered for this course")
    enrollment = Enrollment(student_id=student.id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.delete("/{course_id}/register", status_code=204)
def drop_course(
    course_id: int,
    db: DbSession,
    student: Annotated[Student, Depends(get_student_profile)],
):
    enrollment = _find_enrollment(db, student.id, course_id)
    if enrollment is None:
        raise HTTPException(404, "You are not registered for this course")
    if enrollment.grade is not None:
        raise HTTPException(409, "Cannot drop a course that has already been graded")
    db.delete(enrollment)
    db.commit()


# ---------- grades (assigned lecturer or admin) ----------
@router.put("/{course_id}/students/{student_id}/grade", response_model=GradeRead)
def set_grade(course_id: int, student_id: int, payload: GradeIn, db: DbSession, user: StaffUser):
    course = _get_course(db, course_id)
    _ensure_course_staff(user, course)
    enrollment = _find_enrollment(db, student_id, course_id)
    if enrollment is None:
        raise HTTPException(404, "Student is not registered for this course")
    if enrollment.grade is None:
        enrollment.grade = Grade(score=payload.score)
    else:
        enrollment.grade.score = payload.score
    db.commit()
    db.refresh(enrollment.grade)
    letter, points = score_to_grade(enrollment.grade.score)
    return GradeRead(
        student_id=student_id,
        course_id=course_id,
        score=enrollment.grade.score,
        grade=letter,
        points=points,
    )