from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select

from app.core.deps import (
    AdminUser, CurrentUser, DbSession, StaffUser, get_student_profile,
)
from app.models.academic import Course, Enrollment
from app.models.user import Role, Student, User
from app.schemas.academic import StudentCreate, StudentRead, StudentUpdate, Transcript
from app.services.access import can_view_student
from app.services.transcript import build_transcript

router = APIRouter(prefix="/students", tags=["students"])


def _get_student(db, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    return student


@router.post("", response_model=StudentRead, status_code=201)
def create_student(payload: StudentCreate, db: DbSession, _: AdminUser):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.role != Role.STUDENT:
        raise HTTPException(409, "User is not a student account")
    if user.student is not None:
        raise HTTPException(409, "User already has a student profile")
    if db.scalar(select(Student).where(Student.matric_number == payload.matric_number)):
        raise HTTPException(409, "Matric number already exists")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("", response_model=list[StudentRead])
def list_students(
    db: DbSession,
    user: StaffUser,
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    stmt = select(Student)
    if user.role == Role.LECTURER:
        if user.lecturer is None:
            raise HTTPException(403, "No lecturer profile is linked to this account")
        taught = (
            select(Enrollment.student_id)
            .join(Course, Course.id == Enrollment.course_id)
            .where(Course.lecturer_id == user.lecturer.id)
        )
        stmt = stmt.where(Student.id.in_(taught))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Student.first_name.ilike(like),
                Student.last_name.ilike(like),
                Student.matric_number.ilike(like),
            )
        )
    return db.scalars(stmt.order_by(Student.last_name, Student.id).offset(skip).limit(limit)).all()


@router.get("/me", response_model=StudentRead)
def my_profile(student: Annotated[Student, Depends(get_student_profile)]):
    return student


@router.get("/me/transcript", response_model=Transcript)
def my_transcript(db: DbSession, student: Annotated[Student, Depends(get_student_profile)]):
    return build_transcript(db, student)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: DbSession, user: CurrentUser):
    student = _get_student(db, student_id)
    if not can_view_student(db, user, student):
        raise HTTPException(403, "You do not have access to this student")
    return student


@router.get("/{student_id}/transcript", response_model=Transcript)
def get_transcript(student_id: int, db: DbSession, user: CurrentUser):
    student = _get_student(db, student_id)
    is_owner = user.student is not None and user.student.id == student.id
    if user.role != Role.ADMIN and not is_owner:
        raise HTTPException(403, "You do not have access to this transcript")
    return build_transcript(db, student)


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(student_id: int, payload: StudentUpdate, db: DbSession, _: AdminUser):
    student = _get_student(db, student_id)
    data = payload.model_dump(exclude_unset=True)
    new_matric = data.get("matric_number")
    if new_matric and new_matric != student.matric_number:
        if db.scalar(select(Student).where(Student.matric_number == new_matric)):
            raise HTTPException(409, "Matric number already exists")
    for key, value in data.items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: DbSession, _: AdminUser):
    student = _get_student(db, student_id)
    db.delete(student)  # removes the profile and their registrations; the login account stays
    db.commit()